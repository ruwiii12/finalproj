from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import Account, Employee, Payslip


# ─────────────── ACCESS CONTROL ───────────────

def AdminOnly(request):
    if not request.user.is_authenticated and not request.session.get("user_id"):
        return redirect("login")
    if not request.session.get("is_admin") and not request.user.is_authenticated:
        return redirect("payslips_page")
    return None


def LoginOnly(request):
    if not request.user.is_authenticated and not request.session.get("user_id"):
        return redirect("login")
    return None


def CurrentAccount(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return Account.objects.filter(pk=user_id).first()


def DisplayName(request):
    if request.user.is_authenticated:
        return "Admin"
    user_id = request.session.get("user_id")
    if user_id:
        account = Account.objects.filter(pk=user_id).first()
        if account:
            if account.is_admin:
                return "Admin"
            employee = Employee.objects.filter(account_id=account).first()
            return employee.getName() if employee else account.username
    return ""


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


# ─────────────── VALIDATION AND FORMATTING ───────────────

def RoundAmount(value):
    return round(float(value), 2)


def CheckNonNegative(value, label):
    try:
        number = float(value)
    except (ValueError, TypeError):
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
    if value == "" or value is None:
        return None
    return CheckNonNegative(value, label)


# ─────────────── EMPLOYEE FORM VALUES ───────────────

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
    last_day = DAYS_IN_MONTH.get(month, 30)
    if month == "February":
        try:
            year_int = int(year)
            leap = (year_int % 4 == 0 and year_int % 100 != 0) or (year_int % 400 == 0)
            if leap:
                last_day = 29
        except ValueError:
            pass
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


# ─────────────── LOGIN / LOGOUT ───────────────

def LoginView(request):
    # Already logged in → redirect appropriately
    if request.user.is_authenticated:
        return redirect("employees_page")
    if request.session.get("user_id"):
        if request.session.get("is_admin"):
            return redirect("employees_page")
        return redirect("payslips_page")

    success, error = GetFlash(request)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        # Try Django superuser first
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session["is_admin"] = True
            return redirect("employees_page")

        # Try custom Account table (plain-text password)
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
    request.session.pop("user_id", None)
    request.session.pop("is_admin", None)
    FlashSuccess(request, "You have been logged out.")
    return redirect("login")


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
            except ValueError as e:
                error = str(e)
                cleaned = None

            if cleaned is not None:
                if Employee.objects.filter(id_number=id_number).exists():
                    error = "An employee with that ID number already exists."
                elif Account.objects.filter(username=username).exists():
                    error = "That username is already taken."
                else:
                    account = Account.objects.create(
                        username=username,
                        password=password,
                        is_admin=False
                    )
                    Employee.objects.create(
                        account_id=account,
                        name=cleaned["name"],
                        id_number=cleaned["id_number"],
                        rate=cleaned["rate"],
                        overtime_pay=0,
                        allowance=cleaned["allowance"]
                    )
                    FlashSuccess(request, "Employee created successfully.")
                    return redirect("employees_page")

    return render(request, "payroll_app/create_employee.html", {
        "form_values": values,
        "error": error,
        "is_admin": True,
        "display_name": DisplayName(request)
    })


def UpdateEmployee(request, pk):
    guard = AdminOnly(request)
    if guard:
        return guard

    employee = get_object_or_404(Employee, pk=pk)
    error = ""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        rate = request.POST.get("rate", "").strip()
        allowance = request.POST.get("allowance", "").strip()

        if not (name and rate):
            error = "Name and rate are required."
        else:
            try:
                cleaned_rate = CheckPositive(rate, "Rate")
                cleaned_allowance = CheckOptional(allowance, "Allowance")
            except ValueError as e:
                error = str(e)
                cleaned_rate = None

            if not error:
                employee.name = name
                employee.rate = cleaned_rate
                employee.allowance = cleaned_allowance
                employee.save()
                FlashSuccess(request, "Employee updated successfully.")
                return redirect("employees_page")

    return render(request, "payroll_app/update_employee.html", {
        "employee": employee,
        "error": error,
        "is_admin": True,
        "display_name": DisplayName(request)
    })


def DeleteEmployee(request, pk):
    guard = AdminOnly(request)
    if guard:
        return guard

    if request.method == "POST":
        employee = get_object_or_404(Employee, pk=pk)
        name = employee.getName()
        # Also delete linked account
        if employee.account_id:
            employee.account_id.delete()
        else:
            employee.delete()
        FlashSuccess(request, f"Employee {name} deleted.")
    return redirect("employees_page")


# ─────────────── OVERTIME ───────────────

def AddOvertime(request, pk):
    guard = AdminOnly(request)
    if guard:
        return guard

    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        hours = request.POST.get("hours", "0")
        try:
            h = float(hours)
            if 0 < h <= 744:
                overtime_amount = (employee.getRate() / 160) * 1.5 * h
                employee.overtime_pay = (employee.overtime_pay or 0) + overtime_amount
                employee.save()
                FlashSuccess(request, f"Overtime added for {employee.getName()}.")
            else:
                FlashError(request, "Please enter a valid number of hours (greater than 0).")
        except (ValueError, TypeError):
            FlashError(request, "Please enter a valid number.")
    return redirect("employees_page")


# ─────────────── PAYSLIP VIEWS ───────────────

def PayslipsPage(request):
    guard = LoginOnly(request)
    if guard:
        return guard

    is_admin = request.user.is_authenticated or bool(request.session.get("is_admin"))
    success, error = GetFlash(request)
    employees = Employee.objects.all().order_by("name")

    # Non-admin employees only see their own payslips
    if is_admin:
        payslips = Payslip.objects.all().order_by("-pk")
    else:
        account = CurrentAccount(request)
        emp = Employee.objects.filter(account_id=account).first() if account else None
        payslips = Payslip.objects.filter(id_number=emp).order_by("-pk") if emp else Payslip.objects.none()

    if request.method == "POST" and is_admin:
        payroll_for = request.POST.get("payroll_for", "")
        month = request.POST.get("month", "")
        year = request.POST.get("year", "").strip()
        cycle_raw = request.POST.get("cycle", "")

        if not (payroll_for and month and year and cycle_raw):
            error = "All fields are required to generate payroll."
        else:
            try:
                cycle = int(cycle_raw)
                if cycle not in (1, 2):
                    raise ValueError
            except ValueError:
                error = "Invalid cycle selected."
                cycle = None

            if cycle and not year.isdigit():
                error = "Year must be a valid number."
                cycle = None

            if cycle:
                if payroll_for == "ALL":
                    target_employees = list(employees)
                else:
                    target_employees = list(Employee.objects.filter(id_number=payroll_for))

                if not target_employees:
                    error = "No matching employee found."
                else:
                    created = 0
                    skipped = []
                    for emp in target_employees:
                        if Payslip.objects.filter(id_number=emp, month=month, year=year, pay_cycle=cycle).exists():
                            skipped.append(emp.getID())
                            continue

                        calc = CalculateForEmployee(emp, month, year, cycle)
                        Payslip.objects.create(
                            id_number=emp,
                            month=month,
                            year=year,
                            pay_cycle=cycle,
                            **calc
                        )
                        emp.resetOvertime()
                        created += 1

                    if skipped and created == 0:
                        error = f"Payslip(s) already exist for: {', '.join(skipped)}."
                    elif skipped:
                        error = f"Skipped existing payslip(s) for: {', '.join(skipped)}."
                        FlashSuccess(request, f"{created} payslip(s) generated.")
                        return redirect("payslips_page")
                    else:
                        FlashSuccess(request, f"{created} payslip(s) generated successfully.")
                        return redirect("payslips_page")

        # Re-fetch after possible partial creation
        payslips = Payslip.objects.all().order_by("-pk")

    return render(request, "payroll_app/payslips.html", {
        "employees": employees,
        "payslips": payslips,
        "months": MONTHS,
        "is_admin": is_admin,
        "display_name": DisplayName(request),
        "ok": success,
        "error": error
    })


def ViewPayslip(request, pk):
    guard = LoginOnly(request)
    if guard:
        return guard

    payslip = get_object_or_404(Payslip, pk=pk)
    is_admin = request.user.is_authenticated or bool(request.session.get("is_admin"))
    return render(request, "payroll_app/view_payslip.html", {
        "payslip": payslip,
        "is_admin": is_admin,
        "display_name": DisplayName(request)
    })


def EditSlip(request, pk):
    guard = AdminOnly(request)
    if guard:
        return guard

    payslip = get_object_or_404(Payslip, pk=pk)
    success, error = GetFlash(request)

    form_values = {
        "payroll_for": payslip.getIDNumber(),
        "month": payslip.getMonth(),
        "year": payslip.getYear(),
        "cycle": str(payslip.getPay_cycle()),
        "rate": payslip.getRate(),
        "earnings_allowance": payslip.getEarnings_allowance(),
        "overtime": payslip.getOvertime(),
        "date_range": payslip.getDate_range(),
        "deductions_tax": payslip.getDeductions_tax(),
        "deductions_health": payslip.getDeductions_health(),
        "pag_ibig": payslip.getPag_ibig(),
        "sss": payslip.getSSS(),
        "total_pay": payslip.getTotal_pay(),
    }

    if request.method == "POST":
        month = request.POST.get("month", "")
        year = request.POST.get("year", "").strip()
        cycle_raw = request.POST.get("cycle", "")
        rate_raw = request.POST.get("rate", "")
        allowance_raw = request.POST.get("earnings_allowance", "")
        overtime_raw = request.POST.get("overtime", "")

        try:
            cycle = int(cycle_raw)
            rate = float(rate_raw)
            allowance = float(allowance_raw)
            overtime = float(overtime_raw)

            calc = CalculatePayslip(rate, allowance, overtime, month, year, cycle)
            payslip.month = month
            payslip.year = year
            payslip.pay_cycle = cycle
            payslip.rate = calc["rate"]
            payslip.date_range = calc["date_range"]
            payslip.earnings_allowance = calc["earnings_allowance"]
            payslip.deductions_tax = calc["deductions_tax"]
            payslip.deductions_health = calc["deductions_health"]
            payslip.pag_ibig = calc["pag_ibig"]
            payslip.sss = calc["sss"]
            payslip.overtime = calc["overtime"]
            payslip.total_pay = calc["total_pay"]
            payslip.save()
            FlashSuccess(request, "Payslip updated successfully.")
            return redirect("view_payslip", pk=payslip.pk)
        except (ValueError, KeyError) as e:
            error = "Invalid values: " + str(e)
            form_values.update({
                "month": month, "year": year, "cycle": cycle_raw,
                "rate": rate_raw, "earnings_allowance": allowance_raw, "overtime": overtime_raw
            })

    return render(request, "payroll_app/update_payslip.html", {
        "payslip": payslip,
        "form_values": form_values,
        "months": MONTHS,
        "is_admin": True,
        "display_name": DisplayName(request),
        "ok": success,
        "error": error
    })
