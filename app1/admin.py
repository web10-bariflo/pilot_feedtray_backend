from django.contrib import admin
from.models import *


@admin.register(MQTTMessage)
class MQTTMessageAdmin(admin.ModelAdmin):
    list_display=["device_id","topic","weight_initial","cyclecount","weight_final","timestamp","cycle_number","cycle_status"]



@admin.register(Cycle)
class Cycle(admin.ModelAdmin):
    list_display=["device_id","cyclecount","remaining","timestamp"]
   