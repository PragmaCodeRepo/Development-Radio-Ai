from datetime import datetime,timedelta
import os
from .models import *


def schedule_convert_to_audio(request_data):
    print(f"Executing task at {datetime.now()}")
    from .views import convert_text_to_audio, overlay_background_music, upload_to_sftp, fetch_xml_content, extract_news_items, rewrite_with_chatgpt

    # Code to handle the scheduled task
    # You might need to adjust how you pass request data to this function
    try:

        # Extract data from request_data
        sftp_host = request_data.get('sftp_host')
        sftp_port = int(request_data.get('sftp_port'))
        sftp_username = request_data.get('sftp_username')
        sftp_password = request_data.get('sftp_password')
        sftp_remote_path = request_data.get('sftp_remote_path')
        rss_url = request_data.get('rss_url')
        limit = int(request_data.get('limit', 2))
        voice_gender = request_data.get('voice_gender', 'NEUTRAL')
        # Default path or path from request_data
        voice=request_data.get('voice')
        music_file_path = request_data.get('music_file_path', 'music.mp3')
        intro = request_data.get('intros')
        outro = request_data.get('outros')
        

        # Your existing logic for processing RSS, converting text to audio, etc.
        

        root = fetch_xml_content(rss_url)
        news_items = extract_news_items(root, limit)

        all_news_text = f'{intro}<break time="1s"/>'
        for (description, content) in news_items:
            if content:
                rewritten_content = rewrite_with_chatgpt(content)
                all_news_text += f"{rewritten_content}\n"
            else:
                rewritten_description = rewrite_with_chatgpt(description)
                all_news_text += f"{rewritten_description}\n"

        all_news_text += f'<break time="1s"/>{outro}'
        audio_content = convert_text_to_audio(all_news_text, voice)
        

        if audio_content:
            BACKGROUND_MUSIC_PATH = music_file_path
            combined_audio_path = "combined_news_audio.mp3"
            overlay_background_music(
                audio_content, BACKGROUND_MUSIC_PATH, combined_audio_path)
            remote_sftp_path = f'{sftp_remote_path}/news_with_music.mp3'
            upload_to_sftp(combined_audio_path, remote_sftp_path,
                           sftp_host, sftp_port, sftp_username, sftp_password)

            # Optionally, remove the combined audio file if you don't want to keep it
            os.remove(combined_audio_path)
            print("successfully")
        print("Audio conversion and upload successful")
        print(f'the selected voice is {voice}')
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def fetchingscheduling():
    data = SchedulingTasks.objects.all()
    print("data = ", data)
    for task in data:
        print("Task = ", task)
        recurrence_type = task.recurrence_type
        schedule_time_str = task.schedule_time
        print("schedule_time_str (before paraphrase) = ", schedule_time_str)
        # Check if schedule_time_str is not empty
        if schedule_time_str:
            # Convert the timestamp string to a datetime object
            try:
                # Try to parse the timestamp using the first format
                schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    # If the first format fails, try the second format
                    schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Unable to parse schedule_time_str: {schedule_time_str}")
                    continue  # Skip this iteration if both formats fail

            # Compare with current time in the timezone of your application

            # adding reccuring types
            # if recurrence_type == 'weekly':
            #     schedule_time += timedelta(weeks=1)
            # elif recurrence_type == 'everyhour':
            #     schedule_time += timedelta(hours=1)
            # elif recurrence_type == 'monthly':
            #     # This is a rough estimate, adjust as needed
            #     schedule_time += timedelta(days=30)
            # else:
            #     schedule_time = None

            current_time = datetime.now()
            if current_time >= schedule_time and task.is_pending:
                request_data = {
                    'sftp_host': task.sftp_host,
                    'sftp_port': task.sftp_port,
                    'sftp_username': task.sftp_username,
                    'sftp_password': task.sftp_password,
                    'sftp_remote_path': task.sftp_remote_path,
                    'rss_url': task.rss_url,
                    'limit': task.limit,
                    'voice_gender': 'NEUTRAL',
                    'recurrence_type': task.recurrence_type,
                    'voice':task.voice,
                    'intros': task.intros,
                    'outros': task.outros,
                    
                }
                schedule_convert_to_audio(request_data)
                if task.recurrence_type == 'onetime':
                    task.is_pending = False
                    task.save()
                    print(f"Task {task.id} deleted after processing.")
                elif task.recurrence_type == 'weekly':
                    # Schedule for the next week
                    task.schedule_time = schedule_time + timedelta(weeks=1)
                    task.save()
                    print(f"Task {task.id} scheduled for the next week.")
                elif task.recurrence_type == 'everyhour':
                    # Schedule for the next hour
                    task.schedule_time = schedule_time + timedelta(hours=1)
                    task.save()
                    print(f"Task {task.id} scheduled for the next hour.")
                elif task.recurrence_type == 'monthly':
                    # Schedule for the next month
                    task.schedule_time = schedule_time + timedelta(days=30)  # Assuming a month has approximately 30 days
                    task.save()
                    print(f"Task {task.id} scheduled for the next month.")
                else:
                    print(f"Unknown recurrence type: {task.recurrence_type} for task {task.id}")
        else:
            print("Schedule time is empty or task is not pending:", task.id)
                
                # task.is_pending = False
                # task.save()
                # print(f"Task {task.id} deleted after processing.")




# Weather scheduling functions
from django.http import FileResponse
def schedule_convert_to_audio_weather(request_data):
    from .views import upload_to_sftp,overlay_background_music,convert_text_to_audio,fetch_weather

    try:

        # Extract data from request_data
        sftp_host = request_data.get('sftp_host')
        sftp_port = int(request_data.get('sftp_port'))
        sftp_username = request_data.get('sftp_username')
        sftp_password = request_data.get('sftp_password')
        sftp_remote_path = request_data.get('sftp_remote_path')
        city_name = request_data.get('city_name')
        voice_gender = request_data.get('voice_gender', 'NEUTRAL')
        # Default path or path from request_data
        music_file_path = request_data.get('music_file_path', 'music.mp3')
        intro = request_data.get('intros')
        outro = request_data.get('outros')
        print("intros and outro ",intro,outro)

        # Your existing logic for processing RSS, converting text to audio, etc.
        weather_data = f"{intro}"
        for city in city_name:
            weather_report = fetch_weather(city)
            weather_data += weather_report + "\n"
        weather_data += f"{outro}"

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
       
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# main scheduling function for weather
def fetchingschedulingWeather():
    data = SchedulingTasksWeather.objects.all()
    print("data = ", data)
    for task in data:
        print("Task = ", task)
        recurrence_type = task.recurrence_type
        schedule_time_str = task.schedule_time
        print("schedule_time_str (before paraphrase) = ", schedule_time_str)
        # Check if schedule_time_str is not empty
        if schedule_time_str:
            # Convert the timestamp string to a datetime object
            try:
                # Try to parse the timestamp using the first format
                schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    # If the first format fails, try the second format
                    schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Unable to parse schedule_time_str: {schedule_time_str}")
                    continue  # Skip this iteration if both formats fail

            # Compare with current time in the timezone of your application

            # adding reccuring types
            # if recurrence_type == 'weekly':
            #     schedule_time += timedelta(weeks=1)
            # elif recurrence_type == 'everyhour':
            #     schedule_time += timedelta(hours=1)
            # elif recurrence_type == 'monthly':
            #     # This is a rough estimate, adjust as needed
            #     schedule_time += timedelta(days=30)
            # else:
            #     schedule_time = None

            current_time = datetime.now()
            
            if current_time >= schedule_time and task.is_pending:
                print("current time",current_time)
                request_data = {
                    'sftp_host': task.sftp_host,
                    'sftp_port': task.sftp_port,
                    'sftp_username': task.sftp_username,
                    'sftp_password': task.sftp_password,
                    'sftp_remote_path': task.sftp_remote_path,
                    'city_name': task.city_name,
                    'voice_gender': 'NEUTRAL',
                    'recurrence_type': task.recurrence_type,
                    'intros': task.intros,
                    'outros': task.outros,
                }
                schedule_convert_to_audio_weather(request_data)
                if task.recurrence_type == 'onetime':
                    task.is_pending = False
                    task.save()
                    print(f"Task {task.id} deleted after processing.")
                elif task.recurrence_type == 'weekly':
                    # Schedule for the next week
                    task.schedule_time = schedule_time + timedelta(weeks=1)
                    task.save()
                    print(f"Task {task.id} scheduled for the next week.")
                elif task.recurrence_type == 'everyhour':
                    # Schedule for the next hour
                    task.schedule_time = schedule_time + timedelta(hours=1)
                    task.save()
                    print(f"Task {task.id} scheduled for the next hour.")
                elif task.recurrence_type == 'monthly':
                    # Schedule for the next month
                    task.schedule_time = schedule_time + timedelta(days=30)  # Assuming a month has approximately 30 days
                    task.save()
                    print(f"Task {task.id} scheduled for the next month.")
                else:
                    print(f"Unknown recurrence type: {task.recurrence_type} for task {task.id}")
        else:
            print("Schedule time is empty or task is not pending:", task.id)



# Adding scheduling things on  weather by zipcode            
import requests
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


def schedule_convert_to_audio_weatherbyzipcode(request_data):
    from .views import upload_to_sftp,overlay_background_music,convert_text_to_audio

    try:

        # Extract data from request_data
        sftp_host = request_data.get('sftp_host')
        sftp_port = int(request_data.get('sftp_port'))
        sftp_username = request_data.get('sftp_username')
        sftp_password = request_data.get('sftp_password')
        sftp_remote_path = request_data.get('sftp_remote_path')
        city_zipcode = request_data.get('city_zipcode')
        voice = request_data.get('voice')
        # Default path or path from request_data
        music_file_path = request_data.get('music_file_path', 'music.mp3')
        intro = request_data.get('intros')
        outro = request_data.get('outros')
        news_caster=request_data.get('news_caster')
        language=request_data.get('language')
        print("intros and outro ",intro,outro)
        print("language",language)

        # Your existing logic for processing RSS, converting text to audio, etc.
        weather_data = f'{intro}<break time="1s"/>'
        weather_report = fetch_weather_by_zip(city_zipcode)
        weather_data += weather_report + "\n"
        weather_data += f'<break time="1s"/>{outro}'

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
       
    except Exception as e:
        print(f"An error occurred: {str(e)}")



def fetchingschedulingWeatherByzipcode():
    data = SchedulingTasksWeatherByZipcode.objects.all()
    print("data = ", data)
    for task in data:
        print("Task = ", task)
        recurrence_type = task.recurrence_type
        schedule_time_str = task.schedule_time
        print("schedule_time_str (before paraphrase) = ", schedule_time_str)
        # Check if schedule_time_str is not empty
        if schedule_time_str:
            # Convert the timestamp string to a datetime object
            try:
                # Try to parse the timestamp using the first format
                schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    # If the first format fails, try the second format
                    schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Unable to parse schedule_time_str: {schedule_time_str}")
                    continue  # Skip this iteration if both formats fail

            # Compare with current time in the timezone of your application

            # adding reccuring types
            # if recurrence_type == 'weekly':
            #     schedule_time += timedelta(weeks=1)
            # elif recurrence_type == 'everyhour':
            #     schedule_time += timedelta(hours=1)
            # elif recurrence_type == 'monthly':
            #     # This is a rough estimate, adjust as needed
            #     schedule_time += timedelta(days=30)
            # else:
            #     schedule_time = None

            current_time = datetime.now()
            
            if current_time >= schedule_time and task.is_pending:
                print("current time",current_time)
                request_data = {
                    'sftp_host': task.sftp_host,
                    'sftp_port': task.sftp_port,
                    'sftp_username': task.sftp_username,
                    'sftp_password': task.sftp_password,
                    'sftp_remote_path': task.sftp_remote_path,
                    'city_zipcode':task.city_zipcode,
                    'voice_gender': 'NEUTRAL',
                    'recurrence_type': task.recurrence_type,
                    'voice':task.voice,
                    'intros': task.intros,
                    'outros': task.outros,
                    'news_caster':task.news_caster,
                    'language':task.language
                    
                }
                schedule_convert_to_audio_weatherbyzipcode(request_data)
                if task.recurrence_type == 'onetime':
                    task.is_pending = False
                    task.save()
                    print(f"Task {task.id} deleted after processing.")
                elif task.recurrence_type == 'weekly':
                    # Schedule for the next week
                    task.schedule_time = schedule_time + timedelta(weeks=1)
                    task.save()
                    print(f"Task {task.id} scheduled for the next week.")
                elif task.recurrence_type == 'everyhour':
                    # Schedule for the next hour
                    task.schedule_time = schedule_time + timedelta(hours=1)
                    task.save()
                    print(f"Task {task.id} scheduled for the next hour.")
                elif task.recurrence_type == 'monthly':
                    # Schedule for the next month
                    task.schedule_time = schedule_time + timedelta(days=30)  # Assuming a month has approximately 30 days
                    task.save()
                    print(f"Task {task.id} scheduled for the next month.")
                else:
                    print(f"Unknown recurrence type: {task.recurrence_type} for task {task.id}")
        else:
            print("Schedule time is empty or task is not pending:", task.id)