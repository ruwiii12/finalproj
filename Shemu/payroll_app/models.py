from django.db import models

# Create your models here.

class Employee(models.Model):
    name = models.CharField(max_length=300)
<<<<<<< HEAD
    id_number = models.CharField(max_length=100)
=======
    id_number = models.CharField(max_length=100, unique=True)
>>>>>>> be96a3a8574ff5b6aa19ec0d87743d524c7c0c59
    rate = models.FloatField()
    overtime_pay = models.FloatField(null=True, blank=True)
    allowance = models.FloatField(null=True, blank=True)
    objects = models.Manager()

    def getName(self):
        return self.name
    
    def getID(self):
        return self.id_number
    
    def getRate(self):
        return self.rate
    
    def getOvertime(self):
        return self.overtime_pay
    
    def resetOvertime(self):
        self.overtime_pay = 0
<<<<<<< HEAD
        #idk if need to return smth here or do the "self.save()"" so the change will reflect also in the database
    
=======
        self.save()

>>>>>>> be96a3a8574ff5b6aa19ec0d87743d524c7c0c59
    def getAllowance(self):
        return self.allowance
    
    def __str__(self):
<<<<<<< HEAD
        return '{0}: {1}, rate: {2}'.format(self.pk, self.id_number, self.rate)
=======
        return 'pk: {0}, rate: {1}'.format(self.id_number, self.rate)

class Payslip (models.Model):
    id_number = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    date_range = models.CharField(max_length=20)
    year = models.CharField(max_length = 20)
    pay_cycle = models.IntegerField()
    rate = models.FloatField()
    earnings_allowance = models.FloatField()
    deductions_tax = models.FloatField()
    deductions_health = models.FloatField()
    pag_ibig = models.FloatField()
    sss = models.FloatField()
    overtime = models.FloatField(default = 0)
    total_pay = models.FloatField()

    def getIDNumber(self):
        return self.id_number.id_number
    
    def getMonth(self):
        return self.month
    
    def getDate_range(self):
        return self.date_range
    
    def getYear(self):
        return self.year
    
    def getPay_cycle(self):
        return self.pay_cycle
    
    def getCycleRate(self):
        return self.rate / 2
    
    def getRate(self):
        return self.rate
    
    def getEarnings_allowance(self):
        return self.earnings_allowance  
    
    def getDeductions_tax(self):
        return self.deductions_tax
    
    def getDeductions_health(self):
        return self.deductions_health
    
    def getPag_ibig(self):
        return self.pag_ibig
    
    def getSSS(self):
        return self.sss
    
    def getOvertime(self):
        return self.overtime
    
    def getTotal_pay(self):
        return self.total_pay
    
    def __str__(self):
        return 'pk: {0}, Employee: {1}, Period: {2} {3}, {4}, Cycle: {5}, Total Pay: {6}'.format(
            self.pk,
            self.id_number.id_number,
            self.month,
            self.date_range,
            self.year, 
            self.pay_cycle,
            self.total_pay
        )    
>>>>>>> be96a3a8574ff5b6aa19ec0d87743d524c7c0c59
