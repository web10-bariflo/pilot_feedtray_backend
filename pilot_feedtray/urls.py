from django.contrib import admin
from django.urls import path
from app1.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    #############################################################
    path('post_cyclecount/', handle_cycle),
    path('getall_cycle/', get_all_cycles),
    path('latest_cycles/', get_latest_cycles),
    path('download_csv/', download_cycles_csv),


    
    #######################################
    path('upload_project_data/', upload_project_data, name='upload_project_data'),
    path('download_all_thermal_images/', download_all_images_combined),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
