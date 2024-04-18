# Generated by Django 4.2.4 on 2024-04-18 09:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Intros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intros', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('news_caster', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Newscaster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('language', models.CharField(choices=[('english', 'English'), ('spanish', 'Spanish')], max_length=100)),
                ('voice', models.CharField(max_length=100)),
                ('sftp_host', models.CharField(default='', max_length=255)),
                ('sftp_port', models.IntegerField(default='1')),
                ('sftp_username', models.CharField(default='', max_length=255)),
                ('sftp_password', models.CharField(default='', max_length=255)),
                ('sftp_remote_path', models.CharField(default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Outros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('outros', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('news_caster', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='SchedulingSongsMetaData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sftp_host', models.CharField(max_length=255)),
                ('sftp_port', models.IntegerField()),
                ('sftp_username', models.CharField(max_length=255)),
                ('sftp_password', models.CharField(max_length=255)),
                ('sftp_playlist_folder_name', models.CharField(max_length=255)),
                ('sftp_output_folder_name', models.CharField(max_length=255)),
                ('station_name', models.CharField(default='', max_length=255)),
                ('is_pending', models.BooleanField(default=True)),
                ('schedule_time', models.CharField(max_length=200)),
                ('recurrence_type', models.CharField(choices=[('weekly', 'Weekly'), ('everyhour', 'Every Hour'), ('monthly', 'Monthly'), ('onetime', 'Onetime')], default='onetime', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='SchedulingTasks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sftp_host', models.CharField(max_length=255)),
                ('sftp_port', models.IntegerField()),
                ('sftp_username', models.CharField(max_length=255)),
                ('sftp_password', models.CharField(max_length=255)),
                ('sftp_remote_path', models.CharField(max_length=255)),
                ('rss_url', models.URLField()),
                ('limit', models.IntegerField(default=2)),
                ('schedule_time', models.CharField(max_length=200)),
                ('recurrence_type', models.CharField(choices=[('weekly', 'Weekly'), ('everyhour', 'Every Hour'), ('monthly', 'Monthly'), ('onetime', 'Onetime')], default='onetime', max_length=20)),
                ('voice', models.CharField(choices=[('21m00Tcm4TlvDq8ikWAM', 'Rachel'), ('29vD33N1CtxCmqQRPOHJ', 'Drew'), ('2EiwWnXFnvU5JabPnv8n', 'Clyde'), ('AZnzlk1XvdvUeBnXmlld', 'Domi'), ('CYw3kZ02Hs0563khs1Fj', 'Dave'), ('D38z5RcWu1voky8WS1ja', 'Fin'), ('EXAVITQu4vr4xnSDxMaL', 'Sarah'), ('ErXwobaYiN019PkySvjV', 'Antoni'), ('GBv7mTt0atIp3Br8iCZE', 'Thomas'), ('IKne3meq5aSn9XLyUdCD', 'Charlie'), ('JBFqnCBsd6RMkjVDRZzb', 'George'), ('LcfcDJNUP1GQjkzn1xUU', 'Emily'), ('MF3mGyEYCl7XYWbV9V6O', 'Elli'), ('N2lVS1w4EtoT3dr4eOWO', 'Callum'), ('ODq5zmih8GrVes37Dizd', 'Patrick'), ('SOYHLrjzK2X1ezoPC6cr', 'Harry'), ('TX3LPaxmHKxFdv7VOQHJ', 'Liam'), ('ThT5KcBeYPX3keUQqHPh', 'Dorothy'), ('TxGEqnHWrfWFTfGW9XjX', 'Josh')], default='Neutral', max_length=2000)),
                ('intros', models.CharField(default='', max_length=200)),
                ('outros', models.CharField(default='', max_length=200)),
                ('is_pending', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('news_caster', models.CharField(default='', max_length=200)),
                ('language', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='SchedulingTasksWeather',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sftp_host', models.CharField(max_length=255)),
                ('sftp_port', models.IntegerField()),
                ('sftp_username', models.CharField(max_length=255)),
                ('sftp_password', models.CharField(max_length=255)),
                ('sftp_remote_path', models.CharField(max_length=255)),
                ('schedule_time', models.CharField(max_length=200)),
                ('recurrence_type', models.CharField(choices=[('weekly', 'Weekly'), ('everyhour', 'Every Hour'), ('monthly', 'Monthly'), ('onetime', 'Onetime')], default='onetime', max_length=20)),
                ('intros', models.CharField(default='', max_length=200)),
                ('outros', models.CharField(default='', max_length=200)),
                ('is_pending', models.BooleanField(default=True)),
                ('city_name', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SchedulingTasksWeatherByZipcode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sftp_host', models.CharField(max_length=255)),
                ('sftp_port', models.IntegerField()),
                ('sftp_username', models.CharField(max_length=255)),
                ('sftp_password', models.CharField(max_length=255)),
                ('sftp_remote_path', models.CharField(max_length=255)),
                ('schedule_time', models.CharField(max_length=200)),
                ('recurrence_type', models.CharField(choices=[('weekly', 'Weekly'), ('everyhour', 'Every Hour'), ('monthly', 'Monthly'), ('onetime', 'Onetime')], default='onetime', max_length=20)),
                ('voice', models.CharField(choices=[('21m00Tcm4TlvDq8ikWAM', 'Rachel'), ('29vD33N1CtxCmqQRPOHJ', 'Drew'), ('2EiwWnXFnvU5JabPnv8n', 'Clyde'), ('AZnzlk1XvdvUeBnXmlld', 'Domi'), ('CYw3kZ02Hs0563khs1Fj', 'Dave'), ('D38z5RcWu1voky8WS1ja', 'Fin'), ('EXAVITQu4vr4xnSDxMaL', 'Sarah'), ('ErXwobaYiN019PkySvjV', 'Antoni'), ('GBv7mTt0atIp3Br8iCZE', 'Thomas'), ('IKne3meq5aSn9XLyUdCD', 'Charlie'), ('JBFqnCBsd6RMkjVDRZzb', 'George'), ('LcfcDJNUP1GQjkzn1xUU', 'Emily'), ('MF3mGyEYCl7XYWbV9V6O', 'Elli'), ('N2lVS1w4EtoT3dr4eOWO', 'Callum'), ('ODq5zmih8GrVes37Dizd', 'Patrick'), ('SOYHLrjzK2X1ezoPC6cr', 'Harry'), ('TX3LPaxmHKxFdv7VOQHJ', 'Liam'), ('ThT5KcBeYPX3keUQqHPh', 'Dorothy'), ('TxGEqnHWrfWFTfGW9XjX', 'Josh')], default='Neutral', max_length=2000)),
                ('intros', models.CharField(default='', max_length=200)),
                ('outros', models.CharField(default='', max_length=200)),
                ('city_zipcode', models.CharField(max_length=200)),
                ('is_pending', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('news_caster', models.CharField(default='', max_length=200)),
                ('language', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ActiveSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, max_length=40, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
