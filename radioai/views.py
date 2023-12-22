from itertools import zip_longest
from .models import SchedulingTasks
from django.core.mail import send_mail, BadHeaderError
import datetime
import requests
from xml.etree import ElementTree as ET
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
ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/EdRbIefwv6OnQZLNqQKI"
ELEVEN_API_KEY = "52336052b968f9a2cf5b75b888f518a0"
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


def convert_text_to_audio(text, voice_gender):
    try:
        logger.info("INSIDE CONVERT TO AUDIO")
        aws_access_key_id = config('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')
        aws_region = config('AWS_REGION', default='us-west-2')
        print(
            f'the credentials are access key is {aws_access_key_id} and aws_secret key is {aws_secret_access_key} and region is {aws_region}')
        # Initialize an AWS Polly client with access key, secret key, and region.
        client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )

        # Determine voice name based on gender preference
        # Polly has different voice IDs for male and female voices

        voice_id = voice_gender
        rate = "slow"
        print(voice_id)
        if rate == "slow":
            rate_value = "100%"

        # Construct the SSML with pitch, speed, and other attributes.
        # ssml = f'<speak><prosody rate="medium" pitch="-1st">{text}</prosody></speak>'

        # Request the synthesis with SSML.
        response = client.synthesize_speech(
            Engine='neural',
            OutputFormat='mp3',
            Text=f'<speak><prosody rate="{rate_value}">{text}</prosody></speak>',
            VoiceId=voice_id,
            TextType='ssml',

        )

        # Return the audio content
        return response['AudioStream'].read()
    except Exception as e:
        print(f"An error occurred: {str(e)}")


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
        intro_user = request.POST.get('intro_user')
        outro_user = request.POST.get('outro_user')

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
            is_pending=True if schedule_time else False
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
            return render(request, 'index.html', context={"intros": INTROS_LIST, "outros": OUTROS_LIST, "flag": flag,"time_to_show":time_to_show,"recurr_type":recurr_type})


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
        audio_content = convert_text_to_audio(all_news_text, voice)

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

    return render(request, 'index.html', context={"intros": INTROS_LIST, "outros": OUTROS_LIST, "flag": flag})


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
        return redirect('news/')
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
            return redirect('news/')
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
    INTROS_LIST = [
        intro.intros for intro in Intros.objects.all()
    ]
    OUTROS_LIST = [
        outro.outros for outro in Outros.objects.all()

    ]
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
        intro_user = request.POST.get('intro_user')
        outro_user = request.POST.get('outro_user')
        schedule_time = request.POST.get('schedule_time')
        recurrence_type = request.POST.get('recurrence_type', 'onetime')
        voice = request.POST.get('voice')
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
            is_pending=True if schedule_time else False
        )
        obj.save()
        if schedule_time:
            flag = True
            schedule_time_datetime = datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")
            time_to_show = schedule_time_datetime.strftime("%A, %B %d, %Y %I:%M %p")
            recurr_type=recurrence_type
            return render(request, 'weather_zipcode.html', context={"intros": INTROS_LIST, "outros": OUTROS_LIST, "flag": flag,"time_to_show":time_to_show,"recurr_type":recurr_type})

        weather_data = f'{intro_user} <break time="1s"/>'
        weather_report = fetch_weather_by_zip(city_zipcode)
        weather_data += weather_report + "\n"
        weather_data += f'<break time="1s"/>{outro_user}'

        # Convert this text to speech using Google Text-to-Speech
        audio_content = convert_text_to_audio(weather_data, voice)

        # Overlay background music
        music_file_path = "music.mp3"
        output_file = "zipcode_weather_report.mp3"
        overlay_background_music(audio_content, music_file_path, output_file)

        # Upload the combined audio to SFTP instead of the raw speech audio
        remote_sftp_path = f'{sftp_remote_path}/zipcode_weather_report.mp3'
        upload_to_sftp(output_file, remote_sftp_path, sftp_host,
                       sftp_port, sftp_username, sftp_password)

        return FileResponse(open(output_file, 'rb'), as_attachment=True, filename='zipcode_weather_report.mp3')

    return render(request, 'weather_zipcode.html', context={"intros": INTROS_LIST, "outros": OUTROS_LIST})


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
        Intros.objects.create(intros=intro_text)
       
        return redirect('/news')

    return render(request, 'enter_intro.html',{'suggestions':suggestions})


def enter_outro(request):
    suggestions = ['Bringing you real-time updates, Im Barbara Gordon. Appreciate your attention; now, lets return to the music', 'Bringing you real-time updates, I m Barbara Gordon. Appreciate your attention; now, lets return to the music','I m Barbara Gordon, providing you with live news coverage. Thank you for being here, and lets get back to the music','For up-to-the-minute news, I m Barbara Gordon. Grateful for your audience; now, let s resume the music','This is Barbara Gordon, delivering breaking news as it happens. Your presence is appreciated; now, let s enjoy some music.' ]
    if request.method == 'POST':
        outro_text = request.POST.get('outro_text')
        Outros.objects.create(outros=outro_text)
        return redirect('/news')

    return render(request, 'enter_outro.html',{'suggestions':suggestions})


def enter_intro_weather(request):
    suggestions = ['This is Barbara Gordon, reporting live from our news desk. Lets get you up to speed on current events ', 'Good day, folks. Barbara Gordon here, and I m here to bring you the latest news from our studio', 'Greetings, Im Barbara Gordon, and I ll be your news anchor for today, bringing you the latest updates']
    if request.method == 'POST':
        intro_text = request.POST.get('intro_text')
        Intros.objects.create(intros=intro_text)
        return redirect('/weather-zipcode')

    return render(request, 'enter_intro_weather.html',{'suggestions':suggestions})


def enter_outro_weather(request):
    suggestions = ['Bringing you real-time updates, Im Barbara Gordon. Appreciate your attention; now, lets return to the music', 'Bringing you real-time updates, I m Barbara Gordon. Appreciate your attention; now, lets return to the music','I m Barbara Gordon, providing you with live news coverage. Thank you for being here, and lets get back to the music','For up-to-the-minute news, I m Barbara Gordon. Grateful for your audience; now, let s resume the music','This is Barbara Gordon, delivering breaking news as it happens. Your presence is appreciated; now, let s enjoy some music.' ]
    if request.method == 'POST':
        outro_text = request.POST.get('outro_text')
        Outros.objects.create(outros=outro_text)
        return redirect('/weather-zipcode')

    return render(request, 'enter_outro_weather.html',{'suggestions':suggestions})



