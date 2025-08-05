from django.contrib import admin
from.models import *


@admin.register(MyUser)
class MyUser(admin.ModelAdmin):
    list_display = ('Device_id','User_name','Mob','Email','password')
    

@admin.register(Cycle)
class Cycle(admin.ModelAdmin):
    list_display=["id","cyclecount","start_time","end_time"]


@admin.register(Scheduling)
class Scheduling(admin.ModelAdmin):
    list_display=["id","schedule_id","start_time","cyclecount","recurring_hours","status","timestamp"]
