# Generated by Django 4.2.11 on 2024-04-25 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journeys', '0005_notification_participation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participation',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
    ]