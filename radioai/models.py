from django.db import models
from django.contrib.auth.models import User

class ActiveSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40,null=True, blank=True)

class SchedulingTasks(models.Model):
    RECURRENCE_CHOICES = [
        ('weekly', 'Weekly'),
        ('everyhour', 'Every Hour'),
        ('monthly', 'Monthly'),
        ('onetime', 'Onetime'),
    ]
    VOICE_CHOICES = [
        # ('Neutral', 'Neutral'),
        # ('Female', 'Female'),
        # ('Male', 'Male'),
        ('Joanna', 'Joanna'),
        ('Matthew', 'Matthew'),
        ('Ivy', 'Ivy'),
        ('Justin', 'Justin'),
        ('Kendra', 'Kendra'),
        ('Kimberly', 'Kimberly'),
        ('Salli', 'Salli'),
        ('Joey', 'Joey'),
        ('Nicole', 'Nicole'),
        ('Russell','Russell'),
        ('Amy', 'Amy'),
        ('Brian', 'Brian'),
        ('Emma','Emma'),
        ('Daniella','Daniella'),
        ('Ruth','Ruth'),
        ('Gregory','Gregory'),
        ('Kevin','Kevin'),
        ('Joey','Joey'),
        ('Stephan','Stephan'),

    ]
    sftp_host = models.CharField(max_length=255)
    sftp_port = models.IntegerField()
    sftp_username = models.CharField(max_length=255)
    sftp_password = models.CharField(max_length=255)
    sftp_remote_path = models.CharField(max_length=255)
    rss_url = models.URLField()
    limit = models.IntegerField(default=2)
    schedule_time = models.CharField(max_length=200)
    recurrence_type = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default='onetime'
    )
    voice=models.CharField(
        max_length=2000, choices=VOICE_CHOICES, default='Neutral'
    )
    intros = models.CharField(max_length=200, default='')
    outros = models.CharField(max_length=200, default='')
    is_pending = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sftp_username    

    
class Intros(models.Model):
    intros=models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class Outros(models.Model):
    outros=models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)    
        


  

class SchedulingTasksWeather(models.Model):
    RECURRENCE_CHOICES = [
        ('weekly', 'Weekly'),
        ('everyhour', 'Every Hour'),
        ('monthly', 'Monthly'),
        ('onetime', 'Onetime'),
    ]
    
    sftp_host = models.CharField(max_length=255)
    sftp_port = models.IntegerField()
    sftp_username = models.CharField(max_length=255)
    sftp_password = models.CharField(max_length=255)
    sftp_remote_path = models.CharField(max_length=255)
    schedule_time = models.CharField(max_length=200)
    recurrence_type = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default='onetime'
    )
    intros = models.CharField(max_length=200, default='')
    outros = models.CharField(max_length=200, default='')
    is_pending = models.BooleanField(default=True)
    city_name = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SchedulingTasksWeatherByZipcode(models.Model):
    RECURRENCE_CHOICES = [
        ('weekly', 'Weekly'),
        ('everyhour', 'Every Hour'),
        ('monthly', 'Monthly'),
        ('onetime', 'Onetime'),
    ]
    VOICE_CHOICES = [
        # ('Neutral', 'Neutral'),
        # ('Female', 'Female'),
        # ('Male', 'Male'),
        ('Joanna', 'Joanna'),
        ('Matthew', 'Matthew'),
        ('Ivy', 'Ivy'),
        ('Justin', 'Justin'),
        ('Kendra', 'Kendra'),
        ('Kimberly', 'Kimberly'),
        ('Salli', 'Salli'),
        ('Joey', 'Joey'),
        ('Nicole', 'Nicole'),
        ('Russell','Russell'),
        ('Amy', 'Amy'),
        ('Brian', 'Brian'),
        ('Emma','Emma'),
        ('Daniella','Daniella'),
        ('Ruth','Ruth'),
        ('Gregory','Gregory'),
        ('Kevin','Kevin'),
        ('Joey','Joey'),
        ('Stephan','Stephan'),

    ]
    sftp_host = models.CharField(max_length=255)
    sftp_port = models.IntegerField()
    sftp_username = models.CharField(max_length=255)
    sftp_password = models.CharField(max_length=255)
    sftp_remote_path = models.CharField(max_length=255)
    schedule_time = models.CharField(max_length=200)
    recurrence_type = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default='onetime'
    )
    voice=models.CharField(
        max_length=2000, choices=VOICE_CHOICES, default='Neutral'
    )
    intros = models.CharField(max_length=200, default='')
    outros = models.CharField(max_length=200, default='')
    city_zipcode=models.CharField(max_length=200)
    is_pending = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)    