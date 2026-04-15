from django.db import models

# Create your models here.

class Employee(models.Model):
    name = models.CharField(max_length=300)
    id_number = models.CharField(max_length=100)
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
        #idk if need to return smth here or do the "self.save()"" so the change will reflect also in the database
    
    def getAllowance(self):
        return self.allowance
    
    def __str__(self):
        return '{0}: {1}, rate: {2}'.format(self.pk, self.id_number, self.rate)