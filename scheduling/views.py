from django.shortcuts import render,HttpResponse
import time
from .task import *
from datetime import datetime, time
# Create your views here.

def homepage(request):
    return render(request,"scheduling.html")

def check(request):
    
    handle_sleep.delay()
  
    # time.sleep(10)
    return HttpResponse("Hello ")



