# Generated by Django 5.1.7 on 2025-03-21 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_marker_is_active_marker_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='users',
            field=models.JSONField(default=None),
        ),
    ]
