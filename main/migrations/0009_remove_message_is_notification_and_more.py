# Generated by Django 5.1.4 on 2025-03-17 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_message_is_notification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='is_notification',
        ),
        migrations.AddField(
            model_name='message',
            name='notification_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
