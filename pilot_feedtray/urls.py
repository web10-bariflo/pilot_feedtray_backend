from django.contrib import admin
from django.urls import path
from app1.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('get_mqttdata/', get_mqttdata),
    # path('cyclecount_api/', cyclecount_api),
    # path('device_cycle_details/<str:device_id>/cycles/', device_cycle_details),
    # path('get_deviceid_data/<str:device_id>/', get_deviceid_data),
    path('SaveMQTTMessageView/', SaveMQTTMessageView.as_view()),
    path('CycleCountpost/', SaveCycleCountView.as_view()),
    path('get_data/', get_data),
    # path('getmqttdata/', combined_mqtt_cycle_api),  # removed extra quote here
]
