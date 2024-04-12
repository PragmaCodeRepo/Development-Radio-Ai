# Generated by Django 4.2.4 on 2024-04-03 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radioai', '0023_newscaster_sftp_host_newscaster_sftp_password_and_more'),
    ]

    operations = [
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
                ('is_pending', models.BooleanField(default=True)),
                ('schedule_time', models.CharField(max_length=200)),
                ('recurrence_type', models.CharField(choices=[('weekly', 'Weekly'), ('everyhour', 'Every Hour'), ('monthly', 'Monthly'), ('onetime', 'Onetime')], default='onetime', max_length=20)),
            ],
        ),
    ]