from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Account, Employee, Payslip


# ─────────────── ACCESS CONTROL ───────────────

def AdminOnly(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.session.get("is_admin"):
        return redirect("payslips_page")
    return None


def LoginOnly(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return None


def CurrentAccount(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return Account.objects.filter(pk=user_id).first()


def EmployeeOf(account):
    if account is None:
        return None
    return Employee.objects.filter(account_id=account).first()


def DisplayName(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return "Admin"
    account = CurrentAccount(request)
    if not account:
        return ""
    if account.is_admin:
        return "Admin"
    employee = Employee.objects.filter(account_id=account).first()
    if employee:
        return employee.getName()
    return account.username


# ─────────────── FLASH MESSAGES ───────────────

def FlashSuccess(request, message):
    request.session["flash_ok"] = message


def FlashError(request, message):
    request.session["flash_error"] = message


def GetFlash(request):
    success = request.session.pop("flash_ok", "")
    error = request.session.pop("flash_error", "")
    return success, error


# ─────────────── CONSTANTS ───────────────

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

DAYS_IN_MONTH = {
    "January": 31, "February": 28, "March": 31, "April": 30,
    "May": 31, "June": 30, "July": 31, "August": 31,
    "September": 30, "October": 31, "November": 30, "December": 31
}


# ─────────────── VALIDATION AND FORMAT ───────────────

def RoundAmount(value):
    return round(float(value), 2)


def CheckNonNegative(value, label):
    try:
        number = float(value)
    except ValueError:
        raise ValueError(label + " must be a valid number.")
    if number < 0:
        raise ValueError(label + " cannot be negative.")
    return RoundAmount(number)


def CheckPositive(value, label):
    number = CheckNonNegative(value, label)
    if number <= 0:
        raise ValueError(label + " must be greater than 0.")
    return number


def CheckOptional(value, label):
    if value == "":
        return None
    return CheckNonNegative(value, label)


# ─────────────── EMPLOYEE FORM VALIDATION ───────────────

def EmployeeFormValues(name="", id_number="", rate="", allowance="", username="", password=""):
    return {
        "name": name,
        "id_number": id_number,
        "rate": rate,
        "allowance": allowance,
        "username": username,
        "password": password
    }


def CleanEmployee(name, id_number, rate, allowance):
    if not name or not id_number or not rate:
        raise ValueError("Name, ID number, and rate are required.")
    cleaned_rate = CheckPositive(rate, "Rate")
    cleaned_allowance = CheckOptional(allowance, "Allowance")
    return {
        "name": name,
        "id_number": id_number,
        "rate": cleaned_rate,
        "allowance": cleaned_allowance
    }


# ─────────────── DATE RANGE ───────────────

def GetDateRange(month, year, cycle):
    if cycle == 1:
        return "1-15"
    last_day = DAYS_IN_MONTH[month]
    if month == "February":
        year_int = int(year)
        leap = (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0)
        if leap:
            last_day = 29
    return "16-" + str(last_day)


# ─────────────── PAYROLL FORMULAS ───────────────

def CalculatePayslip(rate, allowance, overtime, month, year, cycle):
    rate = RoundAmount(rate)
    allowance = RoundAmount(allowance or 0)
    overtime = RoundAmount(overtime or 0)
    half_rate = RoundAmount(rate / 2)

    if cycle == 1:
        pagibig = 100.0
        philhealth = 0.0
        sss = 0.0
        taxable = half_rate + allowance + overtime - pagibig
    else:
        pagibig = 0.0
        philhealth = RoundAmount(rate * 0.04)
        sss = RoundAmount(rate * 0.045)
        taxable = half_rate + allowance + overtime - philhealth - sss

    tax = RoundAmount(taxable * 0.20)
    total = RoundAmount(taxable - tax)
    if total < 0:
        total = 0.0

    return {
        "date_range": GetDateRange(month, year, cycle),
        "rate": rate,
        "earnings_allowance": allowance,
        "deductions_tax": tax,
        "deductions_health": philhealth,
        "pag_ibig": pagibig,
        "sss": sss,
        "overtime": overtime,
        "total_pay": total
    }


def CalculateForEmployee(employee, month, year, cycle):
    return CalculatePayslip(
        employee.getRate(),
        employee.getAllowance() or 0,
        employee.getOvertime() or 0,
        month,
        year,
        cycle
    )


# ─────────────── EMPLOYEE VIEWS ───────────────

def EmployeesPage(request):
    guard = AdminOnly(request)
    if guard:
        return guard

    success, error = GetFlash(request)
    employee_list = Employee.objects.all().order_by("name", "id_number")
    return render(request, "payroll_app/employees.html", {
        "employees": employee_list,
        "is_admin": True,
        "display_name": DisplayName(request),
        "ok": success,
        "error": error
    })


def CreateEmployee(request):
    guard = AdminOnly(request)
    if guard:
        return guard

    values = EmployeeFormValues()
    error = ""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        id_number = request.POST.get("id_number", "").strip()
        rate = request.POST.get("rate", "").strip()
        allowance = request.POST.get("allowance", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        values = EmployeeFormValues(name, id_number, rate, allowance, username, password)

        if not (name and id_number and rate):
            error = "Name, ID number, and rate are required."
        elif not (username and password):
            error = "Username and password are required."
        else:
            try:
                cleaned = CleanEmployee(name, id_number, rate, allowance)
            except ValueError as exception:
                error = str(exception)
                cleaned = None

            if cleaned is not None:
                if Employee.objects.filter(id_number=id_number).exists():
                    error = "That employee ID already exists."
                elif Account.objects.filter(username=username).exists():
                    error = "That username already exists."
                else:
                    account = Account.objects.create(username=username, password=password, is_admin=False)
                    Employee.objects.create(
                        account_id=account,
                        name=cleaned["name"],
                        id_number=cleaned["id_number"],
                        rate=cleaned["rate"],
                        overtime_pay=0,
                        allowance=cleaned["allowance"]
                    )
                    FlashSuccess(request, "Employee and login account created successfully.")
                    return redirect("employees_page")

    return render(request, "payroll_app/create_employee.html", {
        "form_values": values,
        "error": error,
        "is_admin": True,
        "display_name": DisplayName(request)
    })


def DeleteEmployee(request, primary_key):
    guard = AdminOnly(request)
    if guard:
        return guard
    if request.method != "POST":
        FlashError(request, "Employees can only be deleted using the delete button.")
        return redirect("employees_page")

    employee = get_object_or_404(Employee, pk=primary_key)
    name = employee.getName()
    employee.delete()
    FlashSuccess(request, "Employee " + name + " was deleted.")
    return redirect("employees_page")


# ─────────────── OVERTIME ───────────────

def AddOvertime(request, primary_key):
    guard = AdminOnly(request)
    if guard:
        return guard

    employee = get_object_or_404(Employee, pk=primary_key)
    if request.method != "POST":
        return redirect("employees_page")

    hours_value = request.POST.get("hours", "").strip()
    if not hours_value:
        FlashError(request, "Enter overtime hours first.")
        return redirect("employees_page")

    try:
        hours = float(hours_value)
    except ValueError:
        FlashError(request, "Overtime hours must be a valid number.")
        return redirect("employees_page")

    if hours <= 0:
        FlashError(request, "Overtime hours must be more than 0.")
        return redirect("employees_page")
    if hours > 744:
        FlashError(request, "Overtime hours cannot exceed 744.")
        return redirect("employees_page")

    current_overtime = employee.getOvertime() or 0
    overtime_amount = RoundAmount((employee.getRate() / 160) * 1.5 * hours)
    employee.overtime_pay = RoundAmount(current_overtime + overtime_amount)
    employee.save()

    message = "Added PHP " + str(overtime_amount) + " overtime pay for " + employee.getName() + "."
    FlashSuccess(request, message)
    return redirect("employees_page")


# ─────────────── LOGIN AND LOGOUT (Superuser Compatible) ───────────────

def LoginView(request):
    # Redirect logged-in users
    if request.user.is_authenticated:
        if request.user.is_superuser or request.session.get("is_admin"):
            return redirect("employees_page")
        else:
            return redirect("payslips_page")

    success, error = GetFlash(request)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            error = "Username and password are required."
        else:
            # Django superuser authentication
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session["is_admin"] = user.is_superuser
                return redirect("employees_page")

            # Fallback: check internal Account table
            account = Account.objects.filter(username=username, password=password).first()
            if account:
                request.session["user_id"] = account.pk
                request.session["is_admin"] = account.is_admin
                if account.is_admin:
                    return redirect("employees_page")
                return redirect("payslips_page")

            error = "Invalid username or password."

    return render(request, "payroll_app/login.html", {"ok": success, "error": error})


def LogoutView(request):
    if request.user.is_authenticated:
        logout(request)
    if "user_id" in request.session:
        del request.session["user_id"]
    if "is_admin" in request.session:
        del request.session["is_admin"]
    FlashSuccess(request, "You have been logged out.")
    return redirect("login")
