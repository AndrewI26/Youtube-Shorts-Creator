# Generated by Django 5.0.7 on 2024-08-08 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subreddit', models.CharField(max_length=255)),
                ('post_title', models.TextField()),
                ('content', models.TextField()),
                ('file_name', models.CharField(max_length=225)),
                ('video_choice', models.CharField(choices=[('subwaySurfers', 'subwaySurfers'), ('minecraftParkor', 'minecraftParkor'), ('mobileGame', 'mobileGame')], max_length=500)),
                ('video_file', models.FileField(upload_to='videos/')),
            ],
        ),
    ]
