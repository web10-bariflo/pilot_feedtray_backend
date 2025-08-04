# app1/models.py
# from django.db import models
# from django.utils import timezone


# class MQTTMessage(models.Model):
#     device_id = models.CharField(max_length=100, db_index=True)
#     topic = models.CharField(max_length=200,null=True,blank=True)
#     weight_initial= models.CharField(max_length=200,null=True,blank=True)
#     cyclecount = models.CharField(max_length=100,null=True, blank=True)
#     weight_final = models.CharField(max_length=200,null=True,blank=True)
#     timestamp = models.DateTimeField(default=timezone.now)
#     cycle_number = models.PositiveIntegerField(null=True, blank=True)
#     cycle_status = models.CharField(max_length=200,null=True,blank=True)


# class Cycle(models.Model):
#     device_id = models.CharField(max_length=100)  
#     cyclecount = models.CharField(max_length=200,null=True,blank=True)
#     remaining = models.CharField(max_length=255)
#     timestamp = models.DateTimeField(default=timezone.now)


# models.py
from django.db import models
from django.utils import timezone



class MyUser(models.Model):   
    Device_id=models.CharField(primary_key=True)                                    
    User_name=models.CharField(max_length=30)
    password = models.CharField(max_length=50, blank=True, null=True)
    Mob=models.BigIntegerField(unique=True)
    Email =models.EmailField()
 

    
    def __str__(self):
        return str(self.Device_id)

class Cycle(models.Model):
    cyclecount = models.IntegerField()
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    thermal_image = models.BinaryField(null=True, blank=True)
    color_image = models.BinaryField( null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)  
    def __str__(self):
        return f"Cycle {self.id} - Count: {self.cyclecount}"


class Scheduling(models.Model):
    schedule_id= models.CharField(max_length=155) 
    start_time = models.DateTimeField(default=timezone.now)
    cyclecount = models.IntegerField()
    recurring_hours = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)


