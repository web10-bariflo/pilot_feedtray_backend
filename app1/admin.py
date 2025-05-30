from django.contrib import admin
from.models import MQTTMessage


@admin.register(MQTTMessage)
class MQTTMessageAdmin(admin.ModelAdmin):
    list_display=["device_id","topic","weight_intial","weight_final","timestamp","cycle_number"]
   