from django import forms 
from .models import Marker, Message
from django.contrib.auth.models import User
from .models import Profile

class MarkerForm(forms.ModelForm):
    class Meta:
        model = Marker
        exclude = ['user'] 
        fields = [
            'user',
            'start_point', 'start_lat', 'start_lon',
            'end_point', 'end_lat', 'end_lon',
            'transport_type', 'other_transport',
            'people_count',
            'landmark_photo', 'landmark_description',
            'price', 'active_from', 'active_to',
            'comment',
            'telegram', 'whatsapp', 'vk', 'phone_number',
        ]
        
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'telegram', 'whatsapp', 'vk']