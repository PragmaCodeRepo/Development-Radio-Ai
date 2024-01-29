"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from .views import CustomLogoutView, mixing_sources
app_name = 'rss_to_audio_app'
urlpatterns = [

    path('news/', login_required(views.convert_to_audio), name='convert',),
    path('contactus/', login_required(views.contactus), name='contactus',),
    path('intro-text/', login_required(views.enter_intro), name='enter_intro',),
    path('outro-text/', login_required(views.enter_outro), name='enter_outro',),
    path('intro-text-weather/',
         login_required(views.enter_intro_weather), name='enter_intro',),
    path('outro-text-weather/',
         login_required(views.enter_outro_weather), name='enter_outro',),
    path('weather-zipcode/', views.zipcode_weather, name='weather_zipcode'),
    path('mixing-sources/', views.mixing_sources, name='mixing_sources'),
    path('chatbot', login_required(views.chatgpt), name='chatgpt'),
    path('thankyou/', login_required(views.thank_you), name='thankyou'),
    path('aboutus/', login_required(views.aboutus), name='aboutus'),
    path('Newscasters/', login_required(views.newscaster_list), name='Newscasters'),
    path('add_newscaster/', login_required(views.add_newscaster),
         name='add_newscaster'),
    # path('weather/',login_required(views.home), name='home'),
    path('generate/', login_required(views.generate_speech), name='generate_speech'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('delete_newscaster/', login_required(views.delete_newscaster),
         name='delete_newscaster'),
    path('edit_newscaster/<int:newscaster_id>/',
         login_required(views.edit_newscaster), name='edit_newscaster'),
    path('scheduling_news_task/',
         login_required(views.scheduling_news_task), name='Newscasters'),
    path('add_scheduling_news_task/', login_required(views.add_scheduling_news_task),
         name='add_scheduling_news_task'),
    path('edit_scheduling_news_task/<int:scheduling_news_task_id>/',
         login_required(views.edit_scheduling_news_task), name='edit_scheduling_news_task'),
    path('delete_scheduling_tasks_id/', login_required(views.delete_scheduling_news_task),
         name='delete_scheduling_news_task'),
    path('scheduling_weather_task/', login_required(views.scheduling_weather_task),
         name='scheduling_weather_task'),
    path('delete_scheduling_tasks_weather_id/', login_required(
        views.delete_scheduling_weather_task), name='delete_scheduling_weather_task'),
    path('edit_scheduling_weather_task/<int:scheduling_weather_task_id>/',
         login_required(views.edit_scheduling_weather_task), name='edit_scheduling_weather_task'),
    path('add_scheduling_weather_task/', login_required(views.add_scheduling_weather_task),
         name='add_scheduling_weather_task'),
    path('delete_all_scheduling_weather_tasks/', login_required(
        views.delete_all_scheduling_weather_tasks), name='delete_all_scheduling_weather_tasks'),
    path('delete_all_scheduling_news_tasks/', login_required(
        views.delete_all_scheduling_news_tasks), name='delete_all_scheduling_news_tasks'),
    path('delete_all_newscaster/', login_required(views.delete_all_newscaster),
         name='delete_all_newscaster'),
    path('', views.login_view, name='login')
]
