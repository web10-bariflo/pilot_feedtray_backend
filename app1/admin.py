from django.contrib import admin
from.models import *

@admin.register(Cycle)
class Cycle(admin.ModelAdmin):
    list_display=["id","cyclecount","start_time","end_time"]
