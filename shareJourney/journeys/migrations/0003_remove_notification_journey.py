# Generated by Django 4.2.11 on 2024-04-22 11:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journeys', '0002_likejourney_likepost_notification_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='journey',
        ),
    ]
