# Generated by Django 4.2.4 on 2024-04-18 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radioai', '0029_schedulingsongsmetadata_dynamicfolder'),
    ]

    operations = [
        migrations.AddField(
            model_name='newscaster',
            name='shift_timing',
            field=models.CharField(default='', max_length=100),
        ),
    ]
