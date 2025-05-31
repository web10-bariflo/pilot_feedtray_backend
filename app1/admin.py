from django.contrib import admin
from.models import *


@admin.register(MQTTMessage)
class MQTTMessageAdmin(admin.ModelAdmin):
    list_display=["device_id","topic","weight_intial","weight_final","timestamp","cycle_number"]



@admin.register(Cycle)
class Cycle(admin.ModelAdmin):
    list_display=["device_id","cyclecount","remaining","timestamp"]
   