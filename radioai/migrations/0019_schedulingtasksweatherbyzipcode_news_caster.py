# Generated by Django 4.2.4 on 2024-01-04 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radioai', '0018_newscaster_intros_news_caster_outros_news_caster_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedulingtasksweatherbyzipcode',
            name='news_caster',
            field=models.CharField(default='', max_length=200),
        ),
    ]
