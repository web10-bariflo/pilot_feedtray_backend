# app1/models.py
from django.db import models
from django.utils import timezone


class MQTTMessage(models.Model):
    device_id = models.CharField(max_length=100, db_index=True)
    topic = models.CharField(max_length=200,null=True,blank=True)
    weight_intial= models.CharField(max_length=200,null=True,blank=True)
    weight_final = models.CharField(max_length=200,null=True,blank=True)
    # payload = models.CharField(max_length=200,null=True,blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    cyclecount = models.CharField(max_length=20, null=True, blank=True)
    cycle_number = models.PositiveIntegerField(default=1)
