from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(ActiveSession)


class ActiveSessionAdmin(admin.ModelAdmin):
     list_display=('user','session_key')

class SchedulingAdmin(admin.ModelAdmin):
     list_display=('sftp_host','sftp_port','sftp_username','sftp_password','sftp_remote_path','rss_url','limit','schedule_time','recurrence_type', 'voice','intros', 'outros', 'is_pending','created_at','news_caster')
     list_filter = ('news_caster',) 
admin.site.register(SchedulingTasks,SchedulingAdmin)   
    

class IntrosAdmin(admin.ModelAdmin):
    list_display = ('intros','created_at','news_caster')
    list_filter = ('news_caster',) 
class OutrosAdmin(admin.ModelAdmin):
    list_display = ('outros','created_at','news_caster')
    list_filter = ('news_caster',) 

admin.site.register(Intros,IntrosAdmin)  
admin.site.register(Outros,OutrosAdmin)  

class SchedulingWeatherAdmin(admin.ModelAdmin):
    list_display = ('sftp_host', 'sftp_port', 'sftp_username', 'sftp_password', 'sftp_remote_path',
                    'city_name', 'schedule_time', 'created_at', 'recurrence_type', 'intros', 'outros', 'is_pending',)
    

admin.site.register(SchedulingTasksWeather,SchedulingWeatherAdmin)  


class SchedulingWeatherByZipcode(admin.ModelAdmin):
    list_display = ('sftp_host', 'sftp_port', 'sftp_username', 'sftp_password', 'sftp_remote_path',
                    'city_zipcode', 'schedule_time', 'created_at', 'recurrence_type','voice', 'intros', 'outros', 'is_pending')
    

admin.site.register(SchedulingTasksWeatherByZipcode,SchedulingWeatherByZipcode)    



class Newscasteradmin(admin.ModelAdmin):
     list_display = ('name', 'language', 'voice')

admin.site.register(Newscaster,Newscasteradmin)