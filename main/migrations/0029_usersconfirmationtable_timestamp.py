# Generated by Django 5.1.4 on 2025-03-29 08:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0028_alter_usersconfirmationtable_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersconfirmationtable',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 3, 29, 8, 50, 2, 917300, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
