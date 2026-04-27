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
<<<<<<< HEAD
    path('admin/', admin.site.urls),
    #insert here the needed urls for the app
=======
    #Employees
    path('', views.EmployeesPage, name='employees'),
    path('create/', views.CreateEmployee, name='create_employee'),
    path('update/<int:pk>/', views.UpdateEmployee, name='update_employee'),
    path('delete/<int:pk>/', views.DeleteEmployee, name='delete_employee'),
    path('overtime/<int:pk>/', views.AddOvertime, name='add_overtime'),

    #Payslips
    path('payslips/', views.PayslipPage, name='payslips'),
    path('payslip/<int:pk>/', views.ViewPayslip, name='view_payslip'),
>>>>>>> be96a3a8574ff5b6aa19ec0d87743d524c7c0c59
]