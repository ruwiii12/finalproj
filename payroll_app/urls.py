"""
URL configuration for Shemu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.EmployeesPage, name="employees_page"),

    # Employee Management
    path("employees/", views.EmployeesPage, name="employees_page"),
    path("employees/create/", views.CreateEmployee, name="create_employee"),
    path("employees/update/<int:pk>/", views.UpdateEmployee, name="update_employee"),
    path("employees/delete/<int:pk>/", views.DeleteEmployee, name="delete_employee"),
    path("employees/overtime/<int:pk>/", views.AddOvertime, name="add_overtime"),

    # Payslips Management
    path("payslips/", views.PayslipsPage, name="payslips_page"),
    path("payslip/<int:pk>/", views.ViewPayslip, name="view_payslip"),
    path("payslip/update/<int:pk>/", views.EditSlip, name="update_payslip"),
    
    # Authentication
    path("login/", views.LoginView, name="login"),
    path("logout/", views.LogoutView, name="logout"),
]