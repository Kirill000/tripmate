from django import forms 
from .models import Marker, Message
from django.contrib.auth.models import User
from .models import Profile 
from django.core.exceptions import ValidationError

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        
        if password != confirm_password:
            raise ValidationError("Пароли не совпадают")
        
        return confirm_password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже зарегистрирован")
        return email

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
        fields = ['photo', 'phone_number', 'telegram', 'whatsapp', 'vk']