from django.contrib import admin
from .models import *
from django import forms

# Register your models here.
admin.site.register(ActiveSession)


class ActiveSessionAdmin(admin.ModelAdmin):
     list_display=('user','session_key')

class SchedulingAdminForm(forms.ModelForm):
    class Meta:
        model = SchedulingTasks
        fields = '__all__'
        widgets = {
            'sftp_password': forms.PasswordInput(render_value=True),
        }

class SchedulingAdmin(admin.ModelAdmin):
    form = SchedulingAdminForm
    list_display = (
        'sftp_host', 'sftp_port', 'sftp_username', 'display_sftp_password', 'sftp_remote_path',
        'rss_url', 'limit', 'schedule_time', 'recurrence_type', 'voice', 'intros', 'outros', 'is_pending',
        'created_at', 'news_caster','language'
    )
    list_filter = ('news_caster',)

    def display_sftp_password(self, obj):
        # Function to display asterisks instead of the actual password
        return '*' * len(obj.sftp_password)

    display_sftp_password.short_description = 'SFTP Password'
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


class SchedulingWeatherByZipcodeAdminForm(forms.ModelForm):
    class Meta:
        model = SchedulingTasksWeatherByZipcode
        fields = '__all__'
        widgets = {
            'sftp_password': forms.PasswordInput(render_value=True),
        }

class SchedulingWeatherByZipcodeAdmin(admin.ModelAdmin):
    form = SchedulingWeatherByZipcodeAdminForm
    list_display = (
        'sftp_host', 'sftp_port', 'sftp_username', 'display_sftp_password', 'sftp_remote_path',
        'city_zipcode', 'schedule_time', 'created_at', 'recurrence_type', 'voice', 'intros', 'outros', 'is_pending', 'news_caster','language',
    )
    list_filter = ('news_caster',)

    def display_sftp_password(self, obj):
        # Function to display asterisks instead of the actual password
        return '*' * len(obj.sftp_password)

    display_sftp_password.short_description = 'SFTP Password'

admin.site.register(SchedulingTasksWeatherByZipcode, SchedulingWeatherByZipcodeAdmin)


class Newscasteradmin(admin.ModelAdmin):
     list_display = ('name', 'language', 'voice','sftp_host','sftp_port','sftp_username','sftp_password','sftp_remote_path',)

admin.site.register(Newscaster,Newscasteradmin)



#Meta Song
class MetaSongadmin(admin.ModelAdmin):
     list_display = ('sftp_host','sftp_port','sftp_username','sftp_password','sftp_playlist_folder_name','sftp_output_folder_name','schedule_time','recurrence_type','is_pending')


admin.site.register(SchedulingSongsMetaData,MetaSongadmin)