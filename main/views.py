from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Marker, Message
from .forms import MarkerForm, MessageForm
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from .forms import UserForm, ProfileForm
from .models import Profile
from django.contrib.gis.geoip2 import GeoIP2

# g = GeoIP2('geoip')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('map')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

@login_required(login_url='login')
def map_view(request):
    markers = Marker.objects.all()
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    # g.city()
    return render(request, 'main/map.html', {'markers': markers})

@login_required(login_url='login')
def add_marker(request):
    if request.method == 'POST':
        form = MarkerForm(request.POST, request.FILES)
        # if form.is_valid():
        marker = form.save(commit=False)
        marker.user = request.user
        marker.save()
        return redirect('map')
        # else:
            # print(form.data)
    else:
        form = MarkerForm()
    return render(request, 'main/add_marker.html', {'form': form})

@login_required(login_url='login')
def send_message(request, marker_id):
    marker = get_object_or_404(Marker, id=marker_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.from_user = request.user
            message.to_user = marker.user
            message.marker = marker
            message.save()
            return redirect('map')
    else:
        form = MessageForm()
    return render(request, 'main/send_message.html', {'form': form, 'marker': marker})

@login_required(login_url='login')
def profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    return render(request, 'main/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('map')