from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Profile(models.Model):
    photo = models.ImageField(upload_to='main/static/images/', default="images/default_profile.jpg")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=200, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    whatsapp = models.CharField(max_length=100, blank=True)
    vk = models.CharField(max_length=100, blank=True)
    successful_trips = models.IntegerField(default=0)
    unsuccessful_trips = models.IntegerField(default=0)
    trips = models.JSONField(blank=False, null=False, default=dict)

    def __str__(self):
        return self.user.username

class Marker(models.Model):
    TRANSPORT_CHOICES = [
        ('personal', 'Личный транспорт'),
        ('carsharing', 'Каршеринг'),
        ('taxi', 'Такси'),
        ('searching', 'Ищу транспорт'),
        ('other', 'Другое'),
    ]
    is_active = models.BooleanField(default=True)
    title = models.CharField(max_length=40, blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transport_type = models.CharField(max_length=50, choices=TRANSPORT_CHOICES)
    other_transport = models.CharField(max_length=255, blank=True, null=True)
    people_count = models.IntegerField()
    start_point = models.CharField(max_length=255)
    start_lat = models.FloatField()
    start_lon = models.FloatField()
    end_point = models.CharField(max_length=255)
    end_lat = models.FloatField()
    end_lon = models.FloatField()
    landmark_photo = models.ImageField(upload_to='main/static/images/', blank=True, null=True)
    landmark_description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    active_from = models.DateTimeField()
    active_to = models.DateTimeField()
    comment = models.TextField(blank=True, null=True)
    telegram = models.CharField(max_length=255, blank=True, null=True)
    whatsapp = models.CharField(max_length=255, blank=True, null=True)
    vk = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    users = models.JSONField(blank=False, null=False, default=dict)

class Message(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50, blank=True, null=True)

class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(default=timezone.now)

    def is_online(self):
        return timezone.now() - self.last_seen < timezone.timedelta(minutes=5)

class UsersConfirmationTable(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    conf_pwd = models.CharField(max_length=10)

@receiver(pre_delete, sender=Marker)
def image_model_delete(sender, instance, **kwargs):
    if instance.landmark_photo.name:
        try:
            os.remove(os.path.join(BASE_DIR, 'main/static'+instance.landmark_photo.url))
        except:
            pass