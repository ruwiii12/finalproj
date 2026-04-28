from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Employee, Payslip

# Create your views here.


# EMPLOYEE VIEWS
def EmployeesPage(request):
    employees = Employee.objects.all()
    return render(request, 'payroll_app/employees.html', {
        'employees': employees
    })


def CreateEmployee(request):
    if request.method == "POST":
        name = request.POST.get('name')
        id_number = request.POST.get('id_number')
        rate = float(request.POST.get('rate'))
        allowance = request.POST.get('allowance')

        if allowance == "":
            allowance = None
        else:
            allowance = float(allowance)

        Employee.objects.create(
            name=name,
            id_number=id_number,
            rate=rate,
            allowance=allowance
        )
        return redirect('employees')

    return render(request, 'payroll_app/create_employee.html')


def UpdateEmployee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        employee.name = request.POST.get('name')
        employee.id_number = request.POST.get('id_number')
        employee.rate = float(request.POST.get('rate'))

        allowance = request.POST.get('allowance')
        if allowance == "":
            employee.allowance = None
        else:
            employee.allowance = float(allowance)

        employee.save()
        return redirect('employees')

    return render(request, 'payroll_app/update_employee.html', {
        'employee': employee
    })


def DeleteEmployee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.delete()
    return redirect('employees')


# OVERTIME FUNCTION
def AddOvertime(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        hours = float(request.POST.get('hours'))

        # Overtime = (Rate/160) x 1.5 x Hours
        overtime = (employee.rate / 160) * 1.5 * hours

        if employee.overtime_pay is None:
            employee.overtime_pay = 0

        employee.overtime_pay += overtime
        employee.save()

    return redirect('employees')


# PAYSLIP VIEWS
def PayslipPage(request):
    employees = Employee.objects.all()
    payslips = Payslip.objects.all()

    if request.method == "POST":
        selected = request.POST.get('employee')  # "all" or specific id
        month = request.POST.get('month')
        year = request.POST.get('year')
        cycle = int(request.POST.get('cycle'))

        # choose employees
        if selected == "all":
            selected_employees = employees
        else:
            selected_employees = Employee.objects.filter(id_number=selected)

        for emp in selected_employees:
            #prevents duplicate payslip
            if Payslip.objects.filter(
                id_number=emp,
                month=month,
                year=year,
                pay_cycle=cycle
            ).exists():
                messages.error(request, 'Payslip already exists for {0} for {1} {2}, Cycle {3}.'.format(emp.name, month, year, cycle))
                continue

            rate = emp.rate
            cycle_rate = rate / 2
            allowance = emp.allowance if emp.allowance else 0
            overtime = emp.overtime_pay if emp.overtime_pay else 0

            # deductions
            if cycle == 1:
                pag_ibig = 100
                health = 0
                sss = 0
                taxable_income = (cycle_rate + allowance + overtime) - pag_ibig
            else:
                pag_ibig = 0
                health = rate * 0.04
                sss = rate * 0.045
                taxable_income = (cycle_rate + allowance + overtime) - health - sss

            tax = taxable_income * 0.20
            total = taxable_income - tax

            Payslip.objects.create(
                id_number=emp,
                month=month,
                date_range="1-15" if cycle == 1 else "16-30",
                year=year,
                pay_cycle=cycle,
                rate=rate,
                earnings_allowance=allowance,
                deductions_tax=tax,
                deductions_health=health,
                pag_ibig=pag_ibig,
                sss=sss,
                overtime=overtime,
                total_pay=total
            )

            emp.resetOvertime()

        return redirect('payslips')

    return render(request, 'payroll_app/payslips.html', {
        'employees': employees,
        'payslips': payslips,
        'months': ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    })


# VIEW SINGLE PAYSLIP
def ViewPayslip(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)

    return render(request, 'payroll_app/view_payslip.html', {
        'payslip': payslip
    })