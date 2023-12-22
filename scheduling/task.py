from celery import shared_task

from datetime import datetime, timedelta

@shared_task
def handle_sleep():
    print('Handle sleep started')
    



@shared_task
def schedule_convert_to_audio(sftp_host, sftp_port, sftp_username, sftp_password, sftp_remote_path, rss_url, limit, music_file_path, voice_gender, intro, outro, user_selected_time):
    now = datetime.now()
    scheduled_time = now.replace(hour=user_selected_time.hour, minute=user_selected_time.minute, second=0, microsecond=0)
    
    if scheduled_time < now:
        scheduled_time += timedelta(days=1)  # Schedule for the next day if the time has already passed
    
    delay_seconds = (scheduled_time - now).total_seconds()
    
    schedule_convert_to_audio.apply_async(
        (sftp_host, sftp_port, sftp_username, sftp_password, sftp_remote_path, rss_url, limit, music_file_path, voice_gender, intro, outro),
        countdown=delay_seconds
    )


    # 8.25kia hai 918 schedule: