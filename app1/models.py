# app1/models.py
from django.db import models
from django.utils import timezone


class MQTTMessage(models.Model):
    device_id = models.CharField(max_length=100, db_index=True)
    topic = models.CharField(max_length=200,null=True,blank=True)
    weight_intial= models.CharField(max_length=200,null=True,blank=True)
    # cyclecount = models.CharField(primary_key, null=True, blank=True)
    weight_final = models.CharField(max_length=200,null=True,blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    cycle_number = models.PositiveIntegerField(default=1)


class Cycle(models.Model):
    device_id = models.CharField(max_length=100)  
    cyclecount = models.CharField(max_length=255)
    remaining = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
