"""
URL configuration for pilot_feedtray project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from app1.views import*

from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('get_mqttdata/', get_mqttdata),
    path('cyclecount_api/',cyclecount_api),
    # path('device_cycle_details/<str:device_id>/cycles/', device_cycle_details),
    path('get_deviceid_data/<str:device_id>/', get_deviceid_data),
]
