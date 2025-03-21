from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import MarkerForm, MessageForm
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.contrib.auth import logout
from .forms import UserForm, ProfileForm
from .models import Profile, Marker, Message
from django.contrib.auth.models import User

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

@login_required
def chat_page(request, marker_id, to_user_id):
    marker = get_object_or_404(Marker, pk=marker_id)
    to_user = get_object_or_404(User, pk=to_user_id)
    if request.user == to_user:
        return render(request, 'main/cannot_chat_with_self.html')
    return render(request, 'main/chat.html', {
        'marker': marker,
        'to_user': to_user,
    })

@login_required
def dialog_list(request):
    messages = Message.objects.filter(to_user=request.user).select_related('from_user', 'marker').order_by('-timestamp')
    unique_senders = {}
    for m in messages:
        key = (m.from_user.id, m.marker.id)
        if key not in unique_senders:
            unique_senders[key] = m

    return render(request, 'main/dialog_list.html', {'dialogs': unique_senders.values()})

@login_required
def get_messages(request, marker_id, to_user_id):
    messages = Message.objects.filter(
        marker_id=marker_id,
        from_user__in=[request.user.id, to_user_id],
        to_user__in=[request.user.id, to_user_id]
    ).order_by('timestamp')
    messages_data = [{
        'from': m.from_user.username,
        'text': m.text,
        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M'),
        'notify_type': m.notification_type
    } for m in messages]

    # пометить как прочитанные
    Message.objects.filter(to_user=request.user, is_read=False).update(is_read=True)

    return JsonResponse({'messages': messages_data})

@login_required
def send_message(request):
    if request.method == 'POST':
        if "notify_type" in request.POST:
            if request.POST['notify_type'] == 'user_query':
                notification_type = request.POST['notify_type']
                marker = Marker.objects.filter(id=request.POST['marker_id'])[0]
                text = f"Пользователь отправил Вам запрос на совместную поездку {marker.title}"
        else:
            notification_type = None
            text = request.POST['text']
            
        to_user_id = request.POST['to_user_id']
        marker_id = request.POST['marker_id']

        if int(to_user_id) != request.user.id:
            Message.objects.create(
                from_user=request.user,
                notification_type=notification_type,
                to_user_id=to_user_id,
                marker_id=marker_id,
                text=text
            )
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

@login_required(login_url='login')
def map_view(request):
    markers = Marker.objects.all()
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    print(markers)
    return render(request, 'main/map.html', {'markers': markers})

@login_required(login_url='login')
def add_marker(request):
    if request.method == 'POST':
        print(request.POST)
        form = MarkerForm(request.POST, request.FILES)
        if form.is_valid():
            marker = form.save(commit=False)
            marker.user = request.user
            marker.save()
            return redirect('map')
        else:
            print(form.errors)
    else:
        form = MarkerForm()
    return render(request, 'main/add_marker.html', {'form': form})

@login_required(login_url='login')
def profile(request, user_id):
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