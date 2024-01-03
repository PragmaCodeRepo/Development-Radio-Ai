# Generated by Django 4.2.4 on 2024-01-03 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radioai', '0017_alter_schedulingtasks_voice_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Newscaster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('language', models.CharField(max_length=100)),
                ('voice', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='intros',
            name='news_caster',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='outros',
            name='news_caster',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='schedulingtasks',
            name='news_caster',
            field=models.CharField(default='', max_length=200),
        ),
    ]