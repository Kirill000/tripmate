# Generated by Django 5.1.4 on 2025-03-15 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_marker_end_lat_marker_end_lon_marker_start_lat_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='end_lat',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='marker',
            name='end_lon',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='marker',
            name='start_lat',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='marker',
            name='start_lon',
            field=models.CharField(max_length=255),
        ),
    ]
