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
        ('21m00Tcm4TlvDq8ikWAM', 'Rachel'),
        ('29vD33N1CtxCmqQRPOHJ', 'Drew'),
        ('2EiwWnXFnvU5JabPnv8n', 'Clyde'),
        ('AZnzlk1XvdvUeBnXmlld', 'Domi'),
        ('CYw3kZ02Hs0563khs1Fj', 'Dave'),
        ('D38z5RcWu1voky8WS1ja', 'Fin'),
        ('EXAVITQu4vr4xnSDxMaL', 'Sarah'),
        ('ErXwobaYiN019PkySvjV', 'Antoni'),
        ('GBv7mTt0atIp3Br8iCZE', 'Thomas'),
        ('IKne3meq5aSn9XLyUdCD','Charlie'),
        ('JBFqnCBsd6RMkjVDRZzb', 'George'),
        ('LcfcDJNUP1GQjkzn1xUU', 'Emily'),
        ('MF3mGyEYCl7XYWbV9V6O','Elli'),
        ('N2lVS1w4EtoT3dr4eOWO','Callum'),
        ('ODq5zmih8GrVes37Dizd','Patrick'),
        ('SOYHLrjzK2X1ezoPC6cr','Harry'),
        ('TX3LPaxmHKxFdv7VOQHJ','Liam'),
        ('ThT5KcBeYPX3keUQqHPh','Dorothy'),
        ('TxGEqnHWrfWFTfGW9XjX','Josh'),

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
    news_caster=models.CharField(max_length=200,default="")
    language=models.CharField(max_length=200,default="") 
    # type = "halgffhf"
    def __str__(self):
        return self.sftp_username    

    
class Intros(models.Model):
    intros=models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    news_caster=models.CharField(max_length=200,default="")

class Outros(models.Model):
    outros=models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)    
    news_caster=models.CharField(max_length=200,default="")
        


  

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
        ('21m00Tcm4TlvDq8ikWAM', 'Rachel'),
        ('29vD33N1CtxCmqQRPOHJ', 'Drew'),
        ('2EiwWnXFnvU5JabPnv8n', 'Clyde'),
        ('AZnzlk1XvdvUeBnXmlld', 'Domi'),
        ('CYw3kZ02Hs0563khs1Fj', 'Dave'),
        ('D38z5RcWu1voky8WS1ja', 'Fin'),
        ('EXAVITQu4vr4xnSDxMaL', 'Sarah'),
        ('ErXwobaYiN019PkySvjV', 'Antoni'),
        ('GBv7mTt0atIp3Br8iCZE', 'Thomas'),
        ('IKne3meq5aSn9XLyUdCD','Charlie'),
        ('JBFqnCBsd6RMkjVDRZzb', 'George'),
        ('LcfcDJNUP1GQjkzn1xUU', 'Emily'),
        ('MF3mGyEYCl7XYWbV9V6O','Elli'),
        ('N2lVS1w4EtoT3dr4eOWO','Callum'),
        ('ODq5zmih8GrVes37Dizd','Patrick'),
        ('SOYHLrjzK2X1ezoPC6cr','Harry'),
        ('TX3LPaxmHKxFdv7VOQHJ','Liam'),
        ('ThT5KcBeYPX3keUQqHPh','Dorothy'),
        ('TxGEqnHWrfWFTfGW9XjX','Josh'),


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
    news_caster=models.CharField(max_length=200,default="") 
    language=models.CharField(max_length=200,default="") 


#Newscaster    
    
from django.db import models

class Newscaster(models.Model):
    # Choices for the language field
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('spanish', 'Spanish'),
    ]

    name = models.CharField(max_length=100)
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES)
    voice = models.CharField(max_length=100)
    sftp_host = models.CharField(max_length=255,default="")
    sftp_port = models.IntegerField(default="1")
    sftp_username = models.CharField(max_length=255,default="")
    sftp_password = models.CharField(max_length=255,default="")
    sftp_remote_path = models.CharField(max_length=255,default="")
    # ... add other fields as necessary

    def __str__(self):
        return self.name
#Meta Song
    
class SchedulingSongsMetaData(models.Model):
    
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
    sftp_playlist_folder_name = models.CharField(max_length=255)
    sftp_output_folder_name = models.CharField(max_length=255)
    station_name = models.CharField(max_length=255,default='')
    # extra_edge = models.CharField(max_length=255,default='')

    is_pending = models.BooleanField(default=True)
    schedule_time = models.CharField(max_length=200)
    recurrence_type = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default='onetime'
    )
   