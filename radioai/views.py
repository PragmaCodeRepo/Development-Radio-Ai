from itertools import zip_longest
from .models import SchedulingTasks
from django.core.mail import send_mail, BadHeaderError
import datetime
import requests
from xml.etree import ElementTree as ET
from app.settings import BASE_DIR
import openai
from moviepy.editor import *
from io import BytesIO
from django.shortcuts import render, redirect
from django.http import HttpResponse
import tempfile
import os
from django.http import FileResponse
import paramiko
from django.contrib.auth import authenticate, login
from .models import *
from django.contrib.auth.views import LogoutView
from django.contrib.auth import authenticate, login, logout
from moviepy.editor import AudioFileClip, vfx, CompositeAudioClip
import random
from google.cloud import texttospeech
import os
import logging
from datetime import datetime
from .tasks import schedule_convert_to_audio
from .serializers import AudioConversionRequestSerializer
from decouple import config
import boto3
from django.http import JsonResponse
from requests.exceptions import RequestException
from django.shortcuts import render, redirect, get_object_or_404
from translate import Translator




# logging
logger = logging.getLogger("django")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "groundrush-labs-voices-5f4df2f4a0fc.json"
# SFTP_HOST = "75.43.156.99"
# SFTP_PORT = 2022
# SFTP_USERNAME = "haljordan"
# SFTP_PASSWORD = "RawNotesandBeats$!"
# SFTP_REMOTE_PATH = "/ANNOUNCEMENTS_FOLDER"


# Constants

# for intros and outros
INTROS_LIST = [
    intro.intros for intro in Intros.objects.all()
]
# Barry Allen

OUTROS_LIST = [
    outro.outros for outro in Outros.objects.all()

]


# OPENAI_API_KEY = "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"

ELEVEN_API_KEY = "f94fb64d2d4db67ec4f7dcee39d05e17"
CHUNK_SIZE = 1024
MUSIC_PATH = "music.mp3"  # Replace with the path to your music file on the server


def fetch_xml_content(url):
    response = requests.get(url)
    return ET.fromstring(response.content)


def extract_news_items(root, limit):
    print(f"the limit in extract_news function is {limit}")
    news_items = []
    for item in root.findall(".//item")[:limit]:
        description = item.find('description').text
        content_element = item.find(
            ".//content:encoded", namespaces={'content': 'http://purl.org/rss/1.0/modules/content/'})

        if content_element is not None:
            content = content_element.text
        else:
            content = None

        news_items.append((description, content))

    return news_items


def rewrite_with_chatgpt(text):
    # truncated_text = text[:4096]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant. Rewrite the following text in a small concise and clear manner and not more than 30 seconds in length."
        },
            {
            "role": "user",
            "content": str(text)
        }]
    )

    return response.choices[0].message['content'].strip()


# GOOGLE TEXT TO SPPECH FUNCTION
# def convert_text_to_audio(text, voice_gender="NEUTRAL"):

#     # Initialize a Text-to-Speech client.
#     client = texttospeech.TextToSpeechClient()

#     # Determine voice name based on gender preference
#     # Wavenet-D is male, Wavenet-F is female
#     voice_name = "en-US-Wavenet-F" if voice_gender == "FEMALE" else "en-US-Wavenet-D"

#     # Customize the voice parameters.
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="en-US",
#         ssml_gender=texttospeech.SsmlVoiceGender[voice_gender],
#         name=voice_name
#     )

#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3
#     )

#     # Construct the SSML with pitch, speed, and other attributes.
#     ssml = f'<speak><prosody rate="medium" pitch="-1st">{text}</prosody></speak>'

#     # Request the synthesis with SSML.
#     input_text = texttospeech.SynthesisInput(ssml=ssml)
#     response = client.synthesize_speech(
#         input=input_text, voice=voice, audio_config=audio_config
#     )

#     # Return the audio content
#     return response.audio_content


def convert_text_to_audio(text,voice):
    voice_id=voice
    ELEVEN_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"    
    try:
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_API_KEY
        }
        response = requests.post(ELEVEN_API_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to convert text to audio. Status code: {response.status_code}")
            return None
    except RequestException as e:
        print(f"An error occurred: {str(e)}")
        return None


def overlay_background_music(news_content, music_file_path, output_file):
    # Save news content to a temporary file
    temp_news_file = "temp_news_audio.mp3"
    with open(temp_news_file, "wb") as temp_file:
        temp_file.write(news_content)

    # Load the two audio files
    news_audio = AudioFileClip(temp_news_file)
    background_music = AudioFileClip(music_file_path)

    # Ensure background music is long enough for the news segment, if not loop it
    background_music = background_music.fx(
        vfx.loop, duration=news_audio.duration)

    background_music = background_music.volumex(0.5)
    news_audio = news_audio.volumex(2.5)


    # Combine the two audio files
    combined_audio = CompositeAudioClip(
        [background_music.volumex(0.2), news_audio])

    # Export the result to output file
    combined_audio.write_audiofile(output_file, fps=44100)

    # Remove the temporary file
    os.remove(temp_news_file)

    # Return the path to the combined audio file
    return output_file


def upload_to_sftp(local_path, remote_path, sftp_host, sftp_port, sftp_username, sftp_password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(
        f"the value of {sftp_host},{sftp_port},{sftp_username},{sftp_password},{remote_path}")
    try:
        ssh_client.connect(
            hostname=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password

        )

        with ssh_client.open_sftp() as sftp:
            sftp.put(local_path, remote_path)

    except Exception as e:
        print(f"Error uploading file via SFTP: {e}")
    finally:
        ssh_client.close()


def insert_pause(seconds):
    return f"<break time='{seconds}s'/>"


def convert_to_audio(request):
    INTROS_LIST = [intro.intros for intro in Intros.objects.all()]
    OUTROS_LIST = [outro.outros for outro in Outros.objects.all()]
    flag = False
    time_to_show=None
    recurr_type=None
    start_time = datetime.now()

    if request.method == 'POST':
        sftp_host = request.POST.get('sftp_host')
        sftp_port = int(request.POST.get('sftp_port'))
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_remote_path = request.POST.get('sftp_remote_path')
        rss_url = request.POST.get('rss_url')
        limit = int(request.POST.get('limit', 2))
        schedule_time = request.POST.get('schedule_time')
        recurrence_type = request.POST.get('recurrence_type', 'onetime')
        voice = request.POST.get('voice')
        intro_user = request.POST.get('intros_user','')
        outro_user = request.POST.get('outro_user',"hola")
        news_caster = request.POST.get('news_caster')
        language = request.POST.get('language')
        print(f"outros:{outro_user}")
        print("request.POST = ",request.POST)
        obj = SchedulingTasks.objects.create(
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_password=sftp_password,
            sftp_username=sftp_username,
            sftp_remote_path=sftp_remote_path,
            rss_url=rss_url,
            limit=limit,
            schedule_time=schedule_time,
            recurrence_type=recurrence_type,
            voice=voice,
            intros=intro_user,
            outros=outro_user,
            is_pending=True if schedule_time else False,
            news_caster = request.POST.get('news_caster'),
            language = request.POST.get('language'),

        )
        obj.save()
        if limit == 0:
            limit = 2
        print(f"the limit is {limit}")

        # Check if a custom music file was uploaded
        if 'music_file' in request.FILES:
            # Save the uploaded music file to a temporary location
            music_file = request.FILES['music_file']
            with open('uploaded/music.mp3', 'wb') as destination:
                for chunk in music_file.chunks():
                    destination.write(chunk)

            # Set the path to the uploaded music file
            music_file_path = 'uploaded/music.mp3'
        else:
            # Use the default music path
            music_file_path = 'music.mp3'

        # Extract voice gender from the request
        # voice_gender = request.POST.get('voice_gender', 'NEUTRAL')
            
        if schedule_time:

            # return HttpResponse("Task scheduled successfully")
            flag = True
            schedule_time_datetime = datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")
            time_to_show = schedule_time_datetime.strftime("%A, %B %d, %Y %I:%M %p")
            recurr_type=recurrence_type
            all_intros = Intros.objects.all()
            all_outros=Outros.objects.all()
        
            if news_caster:
             # Filter intros based on the selected newscaster name
             intros = [intro for intro in all_intros if intro.news_caster == news_caster]
             outros=[outro for outro in all_outros if outro.news_caster==news_caster]
            else:
                intros = all_intros
                outros=all_outros


            return render(request, 'index.html', context={'intros': intros, 'all_intros': all_intros,'outros':outros,'all_outros':all_outros,  "flag": flag,"time_to_show":time_to_show,"recurr_type":recurr_type,"news_caster": news_caster,})


# main.delay(time)

        # Fetch RSS feed content
        root = fetch_xml_content(rss_url)
        news_items = extract_news_items(root, limit)

        all_news_text = f'{intro_user} <break time="1s"/>'
        

        for (description, content) in news_items:
            # Rewrite using GPT-3
            print(f"before content={content}")
            print(f"before description={description}")

            if content:
                rewritten_content = rewrite_with_chatgpt(content)
                print(f"after content={rewritten_content}")
                # Concatenate rewritten content
                all_news_text += f"{rewritten_content}\n"

            else:
                rewritten_description = rewrite_with_chatgpt(description)
                print(f"after description={rewritten_description}")

                # Concatenate rewritten content
                all_news_text += f"{rewritten_description}\n"

        all_news_text += f'<break time="1s"/>{outro_user}'
        
        

        # Convert text to audio using the selected voice gender
        audio_content = convert_text_to_audio(all_news_text,voice)

        if audio_content:
            # Overlay background music
            BACKGROUND_MUSIC_PATH = music_file_path  # Use the uploaded music file path
            combined_audio_path = "combined_news_audio.mp3"
            overlay_background_music(
                audio_content, BACKGROUND_MUSIC_PATH, combined_audio_path)

            # Upload to SFTP server
            # Change to your desired remote path
            remote_sftp_path = f'{sftp_remote_path}/news_with_music.mp3'
            upload_to_sftp(combined_audio_path, remote_sftp_path,
                           sftp_host, sftp_port, sftp_username, sftp_password)

            # Serve the combined audio file as HttpResponse
            with open(combined_audio_path, 'rb') as f:
                response_content = f.read()

            response = HttpResponse(content_type="audio/mpeg")
            response['Content-Disposition'] = 'attachment; filename="news_with_music.mp3"'
            response.write(response_content)

            # Optionally, remove the combined audio file if you don't want to keep it
            os.remove(combined_audio_path)
            print("Time = ", datetime.now() - start_time)
            return response
    language = request.GET.get('language', '')    
    news_caster = request.GET.get('newscaster', '')
    sftp_host = request.GET.get('sftp_host', '')
    sftp_port = request.GET.get('sftp_port', '')
    sftp_username = request.GET.get('sftp_username', '')
    sftp_password = request.GET.get('sftp_password', '')
    sftp_remote_path = request.GET.get('sftp_remote_path', '')
    all_intros = Intros.objects.all()
    all_outros=Outros.objects.all()
    print(language)
    

        
    if news_caster:
        # Filter intros based on the selected newscaster name
            intros = [intro for intro in all_intros if intro.news_caster == news_caster]
            outros=[outro for outro in all_outros if outro.news_caster==news_caster]
    else:
            intros = all_intros
            outros=all_outros

    return render(request, 'index.html', context={'intros': intros, 'all_intros': all_intros,'outros':outros,'all_outros':all_outros,'news_caster':news_caster,'language':language,'sftp_host':sftp_host,'sftp_port':sftp_port,'sftp_username':sftp_username,'sftp_password':sftp_password,'sftp_remote_path':sftp_remote_path })


# weather --code

def fetch_weather(city):
    # Consider moving this to Django settings or environment variable.
    api_key = '41f71975425d5fcbeaf58621d97c5428'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city},USA&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()

    if data['cod'] == 200:
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp'] * 9 / 5 + 32
        formatted_temperature = "{:.1f}".format(temperature)
        humidity = data['main']['humidity']
        weather_report = f"The weather in {city} is {weather_description}. Temperature is {formatted_temperature}°F with {humidity}% humidity."
        return weather_report
    else:
        return f"Failed to fetch weather for {city}."


def generate_speech(request):
    INTROS_LIST = [
        intro.intros for intro in Intros.objects.all()
    ]
    OUTROS_LIST = [
        outro.outros for outro in Outros.objects.all()

    ]
    if request.method == 'POST':
        sftp_host = request.POST.get('sftp_host')
        sftp_port = int(request.POST.get('sftp_port'))
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_remote_path = request.POST.get('sftp_remote_path')
        selected_cities = request.POST.getlist('cities')
        voice_gender = request.POST.get('voice_gender', 'NEUTRAL')
        intro_user = request.POST.get('intro_user')
        outro_user = request.POST.get('outro_user')
        schedule_time = request.POST.get('schedule_time')
        recurrence_type = request.POST.get('recurrence_type', 'onetime')
        intro_user = request.POST.get('intro_user')
        outro_user = request.POST.get('outro_user')
        print("*"*60)
        print("intros = ", intro_user)
        print("outros = ", outro_user)
        print("*"*60)

        obj = SchedulingTasksWeather.objects.create(
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_password=sftp_password,
            sftp_username=sftp_username,
            sftp_remote_path=sftp_remote_path,
            city_name=selected_cities,
            schedule_time=schedule_time,
            recurrence_type=recurrence_type,
            intros=intro_user,
            outros=outro_user,
            is_pending=True if schedule_time else False
        )
        obj.save()
        if schedule_time:
            return HttpResponse("Task scheduled successfully")

        weather_data = f'{intro_user} <break time="2s"/>'
        for city in selected_cities:
            weather_report = fetch_weather(city)
            weather_data += weather_report + "\n"
        weather_data += f' <break time="2s"/> {outro_user}'
        print(weather_data)
        # Convert this text to speech using Google Text-to-Speech
        audio_content = convert_text_to_audio(weather_data, voice_gender)

        # Overlay background music
        music_file_path = "music.mp3"
        output_file = "combined_weather_report.mp3"
        overlay_background_music(audio_content, music_file_path, output_file)

        # Upload the combined audio to SFTP instead of the raw speech audio
        remote_sftp_path = f'{sftp_remote_path}/combined_weather_report.mp3'
        upload_to_sftp(output_file, remote_sftp_path, sftp_host,
                       sftp_port, sftp_username, sftp_password)

        return FileResponse(open(output_file, 'rb'), as_attachment=True, filename='combined_weather_report.mp3')
        

    return render(request, 'weather.html', context={"intros": INTROS_LIST, "outros": OUTROS_LIST})


def home(request):
    return render(request, 'weather.html', context={"intros": INTROS_LIST, "outros": OUTROS_LIST})

# Login Page


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/Newscasters')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user has an active session
            active_session = ActiveSession.objects.filter(user=user).first()
            if active_session:
                error_message = 'User is already logged in from another device.'
                return render(request, 'login.html', {'error_message': error_message})

            # Log in the user and create an active session record
            login(request, user)
            ActiveSession.objects.create(
                user=user, session_key=request.session.session_key)

            # Change 'news/' to your desired redirect URL
            return redirect('Newscasters/')
        else:
            error_message = 'Invalid login credentials'
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')


def logout_view(request):
    # Remove the active session record for the current user
    ActiveSession.objects.filter(
        user=request.user, session_key=request.session.session_key).delete()

    # Log the user out
    logout(request)

    # Redirect to the logout success page or another appropriate page
    return redirect('logout_success')


# logut
class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # Remove the active session record for the current user
        ActiveSession.objects.filter(
            user=request.user, session_key=request.session.session_key).delete()

        # Call the parent class's dispatch method to handle the logout
        response = super().dispatch(request, *args, **kwargs)

        return response

    # Simple Login Page

# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             # Change 'home' to your desired redirect URL
#             return redirect('news/')
#         else:
#             error_message = 'Invalid login credentials'
#             return render(request, 'login.html', {'error_message': error_message})
#     return render(request, 'login.html')


# **************************GOOGLE CLOUD ON SERVER CONFIGURATIONS****************************


# GOOGLE_APPLICATION_CREDENTIALS=/root/actions-runner/_work/Radio-ai/Radio-ai/groundrush-labs-voices-5f4df2f4a0fc.json


# export GOOGLE_APPLICATION_CREDENTIALS="/root/actions-runner/_work/Radio-ai/Radio-ai/groundrush-labs-voices-5f4df2f4a0fc.json"

# echo $GOOGLE_APPLICATION_CREDENTIALS

# pip install google-cloud-texttospeech


# contact us


def contactus(request):
    if request.method == 'POST':
        # Define the form fields directly in the view function
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Send an email (adjust email settings in settings.py)
        try:
            # Send an email
            send_mail(
                f"Contact Form Submission from {name}",
                f"Name: {name}\nEmail: {email}\nMessage:\n{message}",
                'pranjal@groundrushinc.com',  # Replace with your email address
                # Replace with your recipient's email address
                ['mjohnson@groundrushinc.com'],
                fail_silently=False,
            )
        except BadHeaderError:
            return HttpResponse('Invalid header found.')

        return redirect('radioai:thankyou')

    return render(request, 'contactus.html')


def thank_you(request):
    return render(request, 'thankyou.html')


def aboutus(request):
    return render(request, 'aboutus.html')


# weather_zipcode


def fetch_weather_by_zip(zip_code):
    api_key = '41f71975425d5fcbeaf58621d97c5428'
    url = f'http://api.openweathermap.org/data/2.5/weather?zip={zip_code},US&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    


    if data['cod'] == 200:
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp'] * 9 / 5 + 32
        formatted_temperature = "{:.1f}".format(temperature)
        humidity = data['main']['humidity']
        city_name = data['name']
        weather_report = f"The weather in {city_name} is {weather_description}. Temperature is {formatted_temperature}°F with {humidity}% humidity."
        return weather_report
    else:
        return f"Failed to fetch weather for {zip_code}."


def zipcode_weather(request):
    # INTROS_LIST = [
    #     intro.intros for intro in Intros.objects.all()
    # ]
    # OUTROS_LIST = [
    #     outro.outros for outro in Outros.objects.all()

    # ]
    flag=False
    time_to_show=None
    recurr_type=None
    

    if request.method == 'POST':
        sftp_host = request.POST.get('sftp_host')
        sftp_port = int(request.POST.get('sftp_port'))
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_remote_path = request.POST.get('sftp_remote_path')
        city_zipcode = request.POST.get('city_zipcode')
        # voice_gender = request.POST.get('voice_gender', 'NEUTRAL')
        intro_user = request.POST.get('intros_user','')
        outro_user = request.POST.get('outro_user','')
        schedule_time = request.POST.get('schedule_time')
        recurrence_type = request.POST.get('recurrence_type', 'onetime')
        voice = request.POST.get('voice')
        news_caster=request.POST.get('news_caster')
        language=request.POST.get('language')
        print("city_zipcode = ", city_zipcode)
        obj = SchedulingTasksWeatherByZipcode.objects.create(
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_password=sftp_password,
            sftp_username=sftp_username,
            sftp_remote_path=sftp_remote_path,
            city_zipcode=city_zipcode,
            schedule_time=schedule_time,
            recurrence_type=recurrence_type,
            voice=voice,
            intros=intro_user,
            outros=outro_user,
            is_pending=True if schedule_time else False,
            news_caster=news_caster,
            language=language
        )
        obj.save()
        if schedule_time:
            flag = True
            schedule_time_datetime = datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")
            time_to_show = schedule_time_datetime.strftime("%A, %B %d, %Y %I:%M %p")
            recurr_type=recurrence_type
            all_intros = Intros.objects.all()
            all_outros=Outros.objects.all()
            if news_caster:
             # Filter intros based on the selected newscaster name
                intros = [intro for intro in all_intros if intro.news_caster == news_caster]
                outros=[outro for outro in all_outros if outro.news_caster==news_caster]
            else:
                intros = all_intros
                outros=all_outros
            
            
            return render(request, 'weather_zipcode.html', context={'intros': intros, 'all_intros': all_intros,'outros':outros,'all_outros':all_outros,  "flag": flag,"time_to_show":time_to_show,"recurr_type":recurr_type,"news_caster": news_caster,"language":language,})

        weather_data = f'{intro_user} <break time="1s"/>'
        weather_report = fetch_weather_by_zip(city_zipcode)
        weather_data += weather_report + "\n"
        # weather_data=translate_to_spanish(weather_data)
        weather_data += f'<break time="1s"/>{outro_user}'
        if language=="spanish":
           weather_data= translate_to_spanish(weather_data)


        # Convert this text to speech using Google Text-to-Speech
        audio_content = convert_text_to_audio(weather_data, voice)
        if audio_content is None:
            # Handle the case when audio content is not generated successfully
            return HttpResponse("Error generating audio content", status=500)

        # Overlay background music
        music_file_path = "music.mp3"
        output_file = "zipcode_weather_report.mp3"
        overlay_background_music(audio_content, music_file_path, output_file)

        # Upload the combined audio to SFTP instead of the raw speech audio
        remote_sftp_path = f'{sftp_remote_path}/zipcode_weather_report.mp3'
        upload_to_sftp(output_file, remote_sftp_path, sftp_host,
                       sftp_port, sftp_username, sftp_password)

        return FileResponse(open(output_file, 'rb'), as_attachment=True, filename='zipcode_weather_report.mp3')
    news_caster = request.GET.get('newscaster', '')
    language = request.GET.get('language', '')
    sftp_host = request.GET.get('sftp_host', '')
    sftp_port = request.GET.get('sftp_port', '')
    sftp_username = request.GET.get('sftp_username', '')
    sftp_password = request.GET.get('sftp_password', '')
    sftp_remote_path = request.GET.get('sftp_remote_path', '')
    all_intros = Intros.objects.all()
    all_outros=Outros.objects.all()
        
    if news_caster:
        # Filter intros based on the selected newscaster name
            intros = [intro for intro in all_intros if intro.news_caster == news_caster]
            outros=[outro for outro in all_outros if outro.news_caster==news_caster]
    else:
            intros = all_intros
            outros=all_outros


    return render(request, 'weather_zipcode.html', context={'intros': intros, 'all_intros': all_intros,'outros':outros,'all_outros':all_outros, "flag": flag,"time_to_show":time_to_show,"recurr_type":recurr_type,'news_caster':news_caster,'language':language,'sftp_host':sftp_host,'sftp_port':sftp_port,'sftp_username':sftp_username,'sftp_password':sftp_password,'sftp_remote_path':sftp_remote_path})


# chatbotdef chatgpt(request):
# chatgpt_integration/views.py


def chatgpt(request):
    if request.method == 'POST':
        user_message = request.POST.get('user_message')

        conversation = [
            {"role": "system", "content": "please respond."},
            {"role": "user", "content": user_message}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation
        )

        bot_message = response['choices'][0]['message']['content']
        return render(request, 'chatbot.html', {'user_message': user_message, 'bot_message': bot_message})

    return render(request, 'chatbot.html')


# Mix stories


def mixing_sources(request):
    start_time = datetime.now()

    if request.method == 'POST':
        # Retrieve data from the POST request
        rss_url1 = request.POST.get('rss_url1')
        rss_url2 = request.POST.get('rss_url2')
        limit = int(request.POST.get('limit', 2))
        sftp_host = request.POST.get('sftp_host')
        sftp_port = request.POST.get('sftp_port')
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_remote_path = request.POST.get('sftp_remote_path')
        voice_gender = request.POST.get('voice_gender', 'NEUTRAL')

        # Assume the code for file upload and other settings is here
        music_file_path = "music.mp3"
        intro = get_random_intro()
        outro = get_random_outro()

        # Fetch RSS feed content for both URLs
        root1 = fetch_xml_content(rss_url1)
        root2 = fetch_xml_content(rss_url2)

        news_items1 = extract_news_items(root1, limit)
        news_items2 = extract_news_items(root2, limit)

        # Mix stories from both feeds
        mixed_news_items = mix_stories(news_items1, news_items2)

        all_news_text = f"{intro}"

        for (description, content) in mixed_news_items:
            if content:
                rewritten_content = rewrite_with_chatgpt(content)
                all_news_text += f"{rewritten_content}\n"
            elif description:
                rewritten_description = rewrite_with_chatgpt(description)
                all_news_text += f"{rewritten_description}\n"

        all_news_text += f"{outro}"

        # Convert the combined text to audio using the selected voice gender
        audio_content = convert_text_to_audio(all_news_text, voice_gender)

        if audio_content:
            # Overlay background music
            BACKGROUND_MUSIC_PATH = music_file_path  # Use the uploaded music file path
            combined_audio_path = "combined_news_audio.mp3"
            overlay_background_music(
                audio_content, BACKGROUND_MUSIC_PATH, combined_audio_path)

            # Upload the audio file to the SFTP server
            remote_sftp_path = f'{sftp_remote_path}/news_with_music.mp3'
            upload_to_sftp(combined_audio_path, remote_sftp_path,
                           sftp_host, sftp_port, sftp_username, sftp_password)

            # Serve the combined audio file as an HTTP response
            with open(combined_audio_path, 'rb') as f:
                response_content = f.read()

            response = HttpResponse(content_type="audio/mpeg")
            response['Content-Disposition'] = 'attachment; filename="news_with_music.mp3"'
            response.write(response_content)

            # Optionally, remove the combined audio file if you don't want to keep it
            os.remove(combined_audio_path)

        print("Time taken: ", datetime.now() - start_time)
        return render(request, 'mix_feeds.html')

    else:
        # Handle non-POST requests here, possibly rendering a form for input
        return render(request, 'mix_feeds.html')


def mix_stories(news_items1, news_items2):
    mixed_news_items = []

    # Zip the two lists with fillvalue=None to handle different lengths
    for item1, item2 in zip_longest(news_items1, news_items2, fillvalue=None):
        if item1 is not None:
            mixed_news_items.append(item1)
        if item2 is not None:
            mixed_news_items.append(item2)

    return mixed_news_items


# intros and outros
def enter_intro(request):
    suggestions = ['This is Barbara Gordon, reporting live from our news desk. Lets get you up to speed on current events ', 'Good day, folks. Barbara Gordon here, and I m here to bring you the latest news from our studio', 'Greetings, Im Barbara Gordon, and I ll be your news anchor for today, bringing you the latest updates']
    All_data = Intros.objects.all() 
    if request.method == 'POST':
        intro_text = request.POST.get('intro_text')
        news_caster=request.POST.get('news_caster')
        Intros.objects.create(intros=intro_text,news_caster=news_caster)
       
        return redirect('/news')

    return render(request, 'enter_intro.html',{'suggestions':suggestions})


def enter_outro(request):
    suggestions = ['Bringing you real-time updates, Im Barbara Gordon. Appreciate your attention; now, lets return to the music', 'Bringing you real-time updates, I m Barbara Gordon. Appreciate your attention; now, lets return to the music','I m Barbara Gordon, providing you with live news coverage. Thank you for being here, and lets get back to the music','For up-to-the-minute news, I m Barbara Gordon. Grateful for your audience; now, let s resume the music','This is Barbara Gordon, delivering breaking news as it happens. Your presence is appreciated; now, let s enjoy some music.' ]
    if request.method == 'POST':
        outro_text = request.POST.get('outro_text')
        news_caster=request.POST.get('news_caster')
        Outros.objects.create(outros=outro_text,news_caster=news_caster)
        return redirect('/news')

    return render(request, 'enter_outro.html',{'suggestions':suggestions})


def enter_intro_weather(request):
    suggestions = ['This is Barbara Gordon, reporting live from our news desk. Lets get you up to speed on current events ', 'Good day, folks. Barbara Gordon here, and I m here to bring you the latest news from our studio', 'Greetings, Im Barbara Gordon, and I ll be your news anchor for today, bringing you the latest updates']
    if request.method == 'POST':
        intro_text = request.POST.get('intro_text')
        news_caster=request.POST.get('news_caster')
        Intros.objects.create(intros=intro_text,news_caster=news_caster)
        return redirect('/weather-zipcode')

    return render(request, 'enter_intro_weather.html',{'suggestions':suggestions})


def enter_outro_weather(request):
    suggestions = ['Bringing you real-time updates, Im Barbara Gordon. Appreciate your attention; now, lets return to the music', 'Bringing you real-time updates, I m Barbara Gordon. Appreciate your attention; now, lets return to the music','I m Barbara Gordon, providing you with live news coverage. Thank you for being here, and lets get back to the music','For up-to-the-minute news, I m Barbara Gordon. Grateful for your audience; now, let s resume the music','This is Barbara Gordon, delivering breaking news as it happens. Your presence is appreciated; now, let s enjoy some music.' ]
    if request.method == 'POST':
        outro_text = request.POST.get('outro_text')
        news_caster=request.POST.get('news_caster')
        Outros.objects.create(outros=outro_text,news_caster=news_caster)
        return redirect('/weather-zipcode')

    return render(request, 'enter_outro_weather.html',{'suggestions':suggestions})



def newscaster_list(request):
    newscasters = Newscaster.objects.all()
    return render(request, 'newscasters.html', {'newscasters': newscasters})

def add_newscaster(request):
    if request.method == 'POST':
        # Retrieve form data from POST request
        name = request.POST.get('name')
        language = request.POST.get('language')
        voice = request.POST.get('voice')
        sftp_host=request.POST.get('sftp_host')
        sftp_port=request.POST.get('sftp_port')
        sftp_username=request.POST.get('sftp_username')
        sftp_password=request.POST.get('sftp_password')
        sftp_remote_path=request.POST.get('sftp_remote_path')
        exsiting_newscaster=Newscaster.objects.filter(name=name).first()
        if exsiting_newscaster:
            return render(request, 'add_newscaster.html', {'error_message': 'Newscaster with the same name already exists'})

        # Create a new Newscaster object and save it
        Newscaster.objects.create(name=name, language=language, voice=voice,sftp_host=sftp_host,sftp_port=sftp_port,sftp_username=sftp_username,sftp_password=sftp_password,sftp_remote_path=sftp_remote_path)
        
        return redirect('/Newscasters')  # Redirect to the add_newscaster page after adding

    return render(request, 'add_newscaster.html')  # Correct template name

from django.contrib import messages

def delete_newscaster(request):
    if request.method == 'POST':
        newscaster_id = request.POST.get('newscaster_id')
        newscaster = Newscaster.objects.filter(id=newscaster_id).first()

        if newscaster:
            newscaster.delete()
            messages.success(request, 'Newscaster deleted successfully')
        else:
            messages.error(request, 'Newscaster not found')

    return redirect('/Newscasters')


def edit_newscaster(request, newscaster_id):
    newscaster = get_object_or_404(Newscaster, id=newscaster_id)

    if request.method == 'POST':
        newscaster.name = request.POST['name']
        newscaster.language = request.POST['language']
        newscaster.voice = request.POST['voice']
        newscaster.sftp_host = request.POST['sftp_host']
        newscaster.sftp_port = request.POST['sftp_port']
        newscaster.sftp_username = request.POST['sftp_username']
        newscaster.sftp_password = request.POST['sftp_password']
        newscaster.sftp_remote_path = request.POST['sftp_remote_path']


        newscaster.save()
        return redirect('/Newscasters')

    return render(request, 'edit_newscaster.html', {'newscaster': newscaster})




# Scheduling tasks page for news
def scheduling_news_task(request):
    tasks = SchedulingTasks.objects.all()
    return render(request, 'scheduling_tasks/scheduling_tasks.html', {'tasks': tasks})


def delete_scheduling_news_task(request):
    if request.method == 'POST':
        scheduling_tasks_id = request.POST.get('scheduling_tasks_id')
        scheduling_news_task = SchedulingTasks.objects.filter(id=scheduling_tasks_id).first()  # Use the correct model name

        if scheduling_news_task:
            scheduling_news_task.delete()
            messages.success(request, 'Newscaster deleted successfully')
        else:
            messages.error(request, 'Newscaster not found')

    return redirect('/scheduling_news_task')

def edit_scheduling_news_task(request, scheduling_news_task_id):
    scheduling_news_task = get_object_or_404(SchedulingTasks, id=scheduling_news_task_id)

    if request.method == 'POST':
        scheduling_news_task.sftp_host = request.POST['sftp_host']
        scheduling_news_task.sftp_port = request.POST['sftp_port']
        scheduling_news_task.sftp_username = request.POST['sftp_username']
        scheduling_news_task.sftp_password = request.POST['sftp_password']
        scheduling_news_task.sftp_remote_path = request.POST['sftp_remote_path']
        scheduling_news_task.rss_url = request.POST['rss_url']
        scheduling_news_task.schedule_time = request.POST['schedule_time']
        scheduling_news_task.recurrence_type = request.POST['recurrence_type']
        scheduling_news_task.voice = request.POST['voice']
        scheduling_news_task.intros = request.POST['intros']
        scheduling_news_task.outros = request.POST['outros']
        # scheduling_news_task.is_pending = request.POST['is_pending']
        
        scheduling_news_task.save()
        return redirect('/scheduling_news_task')

    return render(request, 'scheduling_tasks/edit_scheduling_tasks.html', {'scheduling_news_task': scheduling_news_task})



def add_scheduling_news_task(request):
    if request.method == 'POST':
        sftp_host = request.POST.get('sftp_host')
        sftp_port = request.POST.get('sftp_port')
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_remote_path = request.POST.get('sftp_remote_path')
        rss_url = request.POST.get('rss_url')
        limit = request.POST.get('limit')
        schedule_time = request.POST.get('schedule_time')
        recurrence_type = request.POST.get('recurrence_type')
        voice = request.POST.get('voice')
        intros = request.POST.get('intros')
        outros = request.POST.get('outros')
        # newscaster=request.POST.get('news_caster')
        # is_pending = request.POST.get('is_pending')
        news_caster = request.POST.get('news_caster')
        
        # exsiting_model=SchedulingTasks.objects.filter(sftp_host=sftp_host).first()
        # if exsiting_model:
        #     return render(request, 'scheduling_tasks/add_scheduling_tasks.html', {'error_message': 'This task is already scheduled with the same  already exists'})

        # Create a new Newscaster object and save it
        SchedulingTasks.objects.create(sftp_host=sftp_host,sftp_port=sftp_port,sftp_username=sftp_username,sftp_password=sftp_password,sftp_remote_path=sftp_remote_path,rss_url=rss_url,schedule_time=schedule_time,recurrence_type=recurrence_type,voice=voice,intros=intros,outros=outros,news_caster=news_caster,limit=limit)
        
        return redirect('/scheduling_news_task')  # Redirect to the add_newscaster page after adding

    return render(request, 'scheduling_tasks/add_scheduling_tasks.html')  # Correct template name


# Scheduling Tasks for weather

def scheduling_weather_task(request):
    tasks = SchedulingTasksWeatherByZipcode.objects.all()
    return render(request, 'scheduling_tasks_weather/scheduling_task_weather_list.html', {'tasks': tasks})


def delete_scheduling_weather_task(request):
    if request.method == 'POST':
        scheduling_tasks_id = request.POST.get('scheduling_tasks_id')
        scheduling_weather_task = SchedulingTasksWeatherByZipcode.objects.filter(id=scheduling_tasks_id).first()  # Use the correct model name

        if scheduling_weather_task:
            scheduling_weather_task.delete()
            messages.success(request, 'Newscaster deleted successfully')
        else:
            messages.error(request, 'Newscaster not found')

    return redirect('/scheduling_weather_task')
def edit_scheduling_weather_task(request,scheduling_weather_task_id):
    scheduling_weather_task = get_object_or_404(SchedulingTasksWeatherByZipcode, id=scheduling_weather_task_id)

    if request.method == 'POST':
        scheduling_weather_task.sftp_host = request.POST['sftp_host']
        scheduling_weather_task.sftp_port = request.POST['sftp_port']
        scheduling_weather_task.sftp_username = request.POST['sftp_username']
        scheduling_weather_task.sftp_password = request.POST['sftp_password']
        scheduling_weather_task.sftp_remote_path = request.POST['sftp_remote_path']
        scheduling_weather_task.city_zipcode = request.POST['city_zipcode']
        scheduling_weather_task.schedule_time = request.POST['schedule_time']
        scheduling_weather_task.recurrence_type = request.POST['recurrence_type']
        scheduling_weather_task.voice = request.POST['voice']
        scheduling_weather_task.intros = request.POST['intros']
        scheduling_weather_task.outros = request.POST['outros']
        # scheduling_news_task.is_pending = request.POST['is_pending']
        
        scheduling_weather_task.save()
        return redirect('/scheduling_weather_task')

    return render(request, 'scheduling_tasks_weather/edit_scheduling_tasks_weather.html', {'scheduling_weather_task': scheduling_weather_task})


def add_scheduling_weather_task(request):
    if request.method == 'POST':
        sftp_host = request.POST.get('sftp_host')
        sftp_port = request.POST.get('sftp_port')
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_remote_path = request.POST.get('sftp_remote_path')
        city_zipcode = request.POST.get('city_zipcode')
        schedule_time = request.POST.get('schedule_time')
        recurrence_type = request.POST.get('recurrence_type')
        voice = request.POST.get('voice')
        intros = request.POST.get('intros')
        outros = request.POST.get('outros')
        # newscaster=request.POST.get('news_caster')
        # is_pending = request.POST.get('is_pending')
        news_caster = request.POST.get('news_caster')
        
        # exsiting_model=SchedulingTasks.objects.filter(sftp_host=sftp_host).first()
        # if exsiting_model:
        #     return render(request, 'scheduling_tasks/add_scheduling_tasks.html', {'error_message': 'This task is already scheduled with the same  already exists'})

        # Create a new Newscaster object and save it
        SchedulingTasksWeatherByZipcode.objects.create(sftp_host=sftp_host,sftp_port=sftp_port,sftp_username=sftp_username,sftp_password=sftp_password,sftp_remote_path=sftp_remote_path,schedule_time=schedule_time,recurrence_type=recurrence_type,voice=voice,intros=intros,outros=outros,news_caster=news_caster,city_zipcode=city_zipcode)
        
        return redirect('/scheduling_weather_task')  # Redirect to the add_newscaster page after adding

    return render(request, 'scheduling_tasks_weather/add_scheduling_weather_tasks.html')  # Correct template name














def delete_all_scheduling_weather_tasks(request):
    if request.method == 'POST':
        # Delete all tasks
        SchedulingTasksWeatherByZipcode.objects.all().delete()
        return redirect('/scheduling_weather_task/')
    else:
        # Handle GET request (optional)
        return redirect('/scheduling_weather_task/')
    
# delete all for schedule news bot 
def delete_all_scheduling_news_tasks(request):
    if request.method == 'POST':
        # Delete all tasks
        SchedulingTasks.objects.all().delete()
        return redirect('/scheduling_news_task/')
    else:
        # Handle GET request (optional)
        return redirect('/scheduling_news_task/')    


# delete all for Newscaster
def delete_all_newscaster(request):
    if request.method == 'POST':
        # Delete all tasks
        Newscaster.objects.all().delete()
        return redirect('/Newscasters/')
    else:
        # Handle GET request (optional)
        return redirect('/Newscasters/')    
    



#convert english text to spanish text to spanish

def translate_to_spanish(text):
    translator = Translator(to_lang="es")
    translated_text = translator.translate(text)
    return translated_text





   
     


# DeepL tranlation
# import deepl

# def translate_to_spanish(text):
#     deepl_auth_key = 'YOUR_DEEPL_AUTH_KEY'  # Replace 'YOUR_DEEPL_AUTH_KEY' with your actual DeepL API key
#     translator = deepl.Translator(deepl_auth_key)
#     translated_text = translator.translate(text, target_lang='ES')
#     return translated_text


#Speech to Speech

def speech_to_speech(request):
    return render(request, 'speech_to_speech.html')








#Meta Song data 
import os
import paramiko
from datetime import datetime
from django.shortcuts import render
import concurrent.futures
import time

def fetching_song_meta_data(request):
    track_names = []
    if request.method == 'POST':
        # Start the timer for profiling
        start_time = time.time()
        print("************INSIDE META DATA SONG************")

        # SFTP server credentials
        sftp_host = request.POST.get('sftp_host')
        sftp_port = request.POST.get('sftp_port')
        sftp_username = request.POST.get('sftp_username')
        sftp_password = request.POST.get('sftp_password')
        sftp_path_playlist=request.POST.get('sftp_path_playlist')
        sftp_path_output=request.POST.get('sftp_path_output')
        recurrence_type=request.POST.get('recurrence_type')
        schedule_time=request.POST.get('schedule_time')
        extraedge=request.POST.get('extraedge')
        stationname=request.POST.get('stationname')
        voice=request.POST.get('voice')
        sftp_port=int(sftp_port)
        print(f"cred is{sftp_host},{sftp_port},{sftp_password},{sftp_username} ")
        print(f"The ex {extraedge}")
        print(f"The voice is ={voice}")
        obj = SchedulingSongsMetaData.objects.create(
            sftp_host=sftp_host,
            sftp_port=sftp_port,
            sftp_password=sftp_password,
            sftp_username=sftp_username,
            sftp_playlist_folder_name=sftp_path_playlist,
            sftp_output_folder_name=sftp_path_output,
            station_name=stationname,
            extra_edge=extraedge,
            is_pending=True if schedule_time else False,
            schedule_time=schedule_time,
            recurrence_type=recurrence_type,
        )
        obj.save()

        # Construct the remote path based on the current date
        today_date = datetime.now().strftime('%m%d%y')
        sftp_remote_path = f'/{sftp_path_playlist}/{today_date}/'
        print(f"SFTP remote path: {sftp_remote_path}")

        media_folder = os.path.join(BASE_DIR, "media")

        # Connect to the SFTP server
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # List files in the specific folder
        folder_files = sftp.listdir(sftp_remote_path)

        # Determine the name of the .pls file based on the current hour
        current_hour = datetime.now().hour
        pls_file_name = f"{(current_hour + 1):02}.pls"
        print(f"Expected .pls file based on current hour: {pls_file_name}")

        # Check if the .pls file exists in the folder
        if pls_file_name in folder_files:
            remote_file_path = os.path.join(sftp_remote_path, pls_file_name)
            local_file_path = os.path.join(media_folder, pls_file_name)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            sftp.get(remote_file_path, local_file_path)
            track_names = get_track_names(local_file_path)

            # Function to process each track
            def process_track(i):
                # print("*******INSIDE PROCESS TRACK*************")
                current_track = track_names[i]
                next_track = track_names[i + 1]
                fun_fact_current = rewrite_with_chatgpt_song_meta_data(current_track,current_track,next_track,stationname)
                fun_fact_next = rewrite_with_chatgpt_song_meta_data(next_track,current_track,next_track,stationname)
                extradata=extranews(extraedge)
                print(f"the extra news is {extraedge}")
                text = f"  {fun_fact_current}. Next song is {next_track} {fun_fact_next} {extradata}"
                audio_file = f"vo{(i // 3) + 1}.mp3"
                convert_text_to_audio_gtts(text, audio_file,'21m00Tcm4TlvDq8ikWAM')
                upload_to_sftp_for_meta_data(audio_file, f"{sftp_path_output}/VO{(i // 3) + 1}/{audio_file}", sftp_host, sftp_port, sftp_username, sftp_password)
                print(f"Processed track: {current_track}, Next track: {next_track}")

            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_track, range(2, len(track_names) - 1, 3))
            # for i in range(2, len(track_names) - 1, 3):
                # process_track(i)

        # Close the SFTP connection
        sftp.close()
        transport.close()

        # Clean up the local media folder
        empty_folder(media_folder)

        # Log the total execution time
        print(f"Total execution time: {time.time() - start_time} seconds")
        return render(request, 'Songs/fetching.html', {"track_names": track_names})
    news_caster = request.GET.get('newscaster', '')
    language = request.GET.get('language', '')
    sftp_host = request.GET.get('sftp_host', '')
    sftp_port = request.GET.get('sftp_port', '')
    sftp_username = request.GET.get('sftp_username', '')
    sftp_password = request.GET.get('sftp_password', '')
    sftp_remote_path = request.GET.get('sftp_remote_path', '')
    return render(request, 'Songs/fetching.html',{'news_caster':news_caster,'language':language,'sftp_host':sftp_host,'sftp_port':sftp_port,'sftp_username':sftp_username,'sftp_password':sftp_password,'sftp_remote_path':sftp_remote_path})


def empty_folder(folder_path):
    # List all files and subdirectories in the folder
    for root, dirs, files in os.walk(folder_path):
        # Remove files
        for file in files:
            os.remove(os.path.join(root, file))
        # Remove subdirectories
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))


def get_track_names(path):
    track_names = []

    # Open the file with the correct encoding
    with open(path, "r", encoding="latin-1") as file:
        # Read the lines of the file
        lines = file.readlines()

        # Iterate over each line
        for line in lines:
            # Check if the line starts with "TrackName"
            if line.startswith("TrackName"):
                # Split the line by "=" and get the second part (the value)
                track_name = line.split("=")[1].strip()
                # Append the track name to the list
                track_names.append(track_name)

    # Print the list of track names
    return track_names


def convert_text_to_audio_gtts(text, output_file, voice_id):
    ELEVEN_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"    
    try:
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": config('ELEVEN_API_KEY')
        }
        response = requests.post(ELEVEN_API_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
        else:
            print(f"Failed to convert text to audio with Eleven Labs. Status code: {response.status_code}")
    except RequestException as e:
        print(f"An error occurred with Eleven Labs: {str(e)}")
def rewrite_with_chatgpt_song_meta_data(text,current_track,next_track,stationname):
    # truncated_text = text[:4096]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": f"You are a radio dj female named Payton Brooks on {stationname} best country is the tag line  and you are backselling out of {current_track} song while giving a  bit of fun information then I would like you to front sell of this this {next_track} did give fun information about this song aor artist also.and keep it small"
        },
            {
            "role": "user",
            "content": str(text)
        }]
    )
    
    return response.choices[0].message['content'].strip()


def upload_to_sftp_for_meta_data(local_path, remote_path, sftp_host, sftp_port, sftp_username, sftp_password):
    print("**********INSIDE UPLOAD*******************")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(
            hostname=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password
        )

        with ssh_client.open_sftp() as sftp:
            sftp.put(local_path, remote_path)
        print("************upload successfully*************")

    except Exception as e:
        print(f"Error uploading file via SFTP: {e}")
    finally:
        ssh_client.close()
# import re
# import os
# def fetching_song_meta_data(request):
#     if request.method == 'POST':
#         print("************INSIDE META DATA SONG************")
#         # SFTP server credentials
#         sftp_host = '75.43.156.103'
#         sftp_port = 2227  # or any other port your SFTP server is running on
#         sftp_username = 'GRUser'
#         sftp_password = 'HOX45!!'
#         sftp_remote_path = '/Playlist/022224/'
#         # Connect to the SFTP server
#         transport = paramiko.Transport((sftp_host, sftp_port))
#         transport.connect(username=sftp_username, password=sftp_password)
#         sftp = paramiko.SFTPClient.from_transport(transport)
#         # List files in the specific folder
#         folder_files = sftp.listdir(sftp_remote_path)
#         # Read the .pls file from the folder
#         pls_file = None
#         for file_name in folder_files:
#             if file_name.endswith('.pls'):
#                 pls_file = file_name
#                 break
#         print(f"{pls_file}")
#         if pls_file:
#             pls_file_path = os.path.join(sftp_remote_path, pls_file)
#             pls_content = read_pls(pls_file_path)
#             # # Read the contents of the .pls file
#             # with sftp.open(pls_file_path, 'r') as file:
#             #  try:
#             #     pls_content = file.read().decode('utf-8')
#             #  except UnicodeDecodeError:
#             #     pls_content = file.read().decode('latin-1')
#             # Close SFTP connection
#             sftp.close()
#             transport.close()
#             # Extract 'TrackName' values from the .pls file content
#             print(f"pls content{pls_content}")
#             track_names = re.findall(r'TrackName\d+=(.*)', pls_content)
#             print(f" Track names is {track_names}")
#             track_names_list = [name.strip() for name in track_names]
#             # Pass track names to the template
#             return render(request, 'Songs/fetching.html', {
#                 'track_names_list': track_names_list
#             })
#         else:
#             # If no .pls file found in the folder
#             return render(request, 'Songs/no_pls_file.html')
#     return render(request, 'Songs/fetching.html')


def read_pls(file_path):
    print("file path = ", file_path)
    playlist = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()
        print("lines = ", lines)
        for line in lines:
            line = line.strip()
            if line.startswith("File"):
                parts = line.split("=")
                if len(parts) == 2:
                    file_index = int(parts[0].split("File")[1].strip())
                    file_path = parts[1].strip()
                    playlist[file_index] = file_path
    return playlist


def extranews(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": f"The text is as follows: {text}. Please read it and respond accordingly. Keep your reply concise."
        },
            {
            "role": "user",
            "content": str(text)
        }]
    )
    
    return response.choices[0].message['content'].strip()        


def upload_files(request):
    SFTP_HOST = '75.43.156.103'
    SFTP_PORT = 2227
    SFTP_USERNAME = 'GRUser'
    SFTP_PASSWORD = 'HOX45!!'
    SFTP_FOLDER = '/Test'

    if request.method == 'POST' and request.FILES.getlist('files'):
        try:
            transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
            transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)

            for file in request.FILES.getlist('files'):
                filename = file.name
                sftp.putfo(file, f'{SFTP_FOLDER}/{filename}')

            sftp.close()
            transport.close()

            return render(request, 'Songs/success.html')
        except Exception as e:
            return render(request, 'Songs/error.html', {'error': str(e)})
    return render(request, 'Songs/uploading_files.html')    





