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
from django.urls import path,include
from . import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from .views import CustomLogoutView,mixing_sources
app_name = 'rss_to_audio_app'
urlpatterns = [
    
    path('news/',login_required(views.convert_to_audio),name='convert',),
    path('contactus/',login_required(views.contactus),name='contactus',),
    path('intro-text/',login_required(views.enter_intro),name='enter_intro',),
    path('outro-text/',login_required(views.enter_outro),name='enter_outro',),
    path('intro-text-weather/',login_required(views.enter_intro_weather),name='enter_intro',),
    path('outro-text-weather/',login_required(views.enter_outro_weather),name='enter_outro',),
    path('weather-zipcode/', views.zipcode_weather, name='weather_zipcode'),
    path('mixing-sources/', views.mixing_sources, name='mixing_sources'),
    path('chatbot', login_required(views.chatgpt), name='chatgpt'),
    path('thankyou/', login_required(views.thank_you), name='thankyou'),
    path('aboutus/', login_required(views.aboutus), name='aboutus'),  
    # path('weather/',login_required(views.home), name='home'),
    path('generate/', login_required(views.generate_speech), name='generate_speech'),
     path('logout/', CustomLogoutView.as_view(), name='logout'),
     
    path('', views.login_view,name='login')
]
