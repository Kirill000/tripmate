from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    whatsapp = models.CharField(max_length=100, blank=True)
    vk = models.CharField(max_length=100, blank=True)
    successful_trips = models.IntegerField(default=0)
    unsuccessful_trips = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

class Marker(models.Model):
    TRANSPORT_CHOICES = [
        ('personal', 'Личный транспорт'),
        ('carsharing', 'Каршеринг'),
        ('taxi', 'Такси'),
        ('other', 'Другое'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transport_type = models.CharField(max_length=50, choices=TRANSPORT_CHOICES)
    other_transport = models.CharField(max_length=255, blank=True, null=True)
    people_count = models.IntegerField()
    start_point = models.CharField(max_length=255)
    end_point = models.CharField(max_length=255)
    landmark_photo = models.ImageField(upload_to='landmarks/', blank=True, null=True)
    landmark_description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    active_from = models.DateTimeField()
    active_to = models.DateTimeField()
    comment = models.TextField(blank=True, null=True)
    telegram = models.CharField(max_length=255, blank=True, null=True)
    whatsapp = models.CharField(max_length=255, blank=True, null=True)
    vk = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

class Message(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)