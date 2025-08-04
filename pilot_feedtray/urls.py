from django.contrib import admin
from django.urls import path
from app1.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create_user_feedtray/', create_user),
    path('login/', login_user),
    path('forgot_password/', forgot_password),
    path('reset_password/', reset_password),
    path('reset-password/', reset_password_page),  
    #############################################################
    path('post_cyclecount/', handle_cycle),
    path('getall_cycle/', get_all_cycles),
    path('latest_cycles/', get_latest_cycles),
    path('download_csv/', download_cycles_csv),

    ####################################################
    path('create_schedule/', create_schedule),
    path('get_all_schedules/', get_all_schedules),
    path('get_all_schedule_ids/', get_all_schedule_ids),
    path('delete_schedule_id/', delete_schedule_by_id),

    #######################################
    path('upload_project_data/', upload_project_data, name='upload_project_data'),
    path('download_all_thermal_images/', download_all_images_combined),

]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
