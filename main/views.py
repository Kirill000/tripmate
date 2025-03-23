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
import json
from datetime import timedelta, datetime
from django.contrib import messages
import os

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            Profile.objects.get_or_create(user=user)
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
    
    try:
        user_query_data = marker.users[str(request.user.id)]
    except KeyError:
        user_query_data = None
    
    return render(request, 'main/chat.html', {
        'marker': marker,
        'to_user': to_user,
        'user_query_data': user_query_data
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
        'notify_type': m.notification_type,
    } for m in messages]

    # пометить как прочитанные
    Message.objects.filter(to_user=request.user, is_read=False).update(is_read=True)

    return JsonResponse({'messages': messages_data})

@login_required
def send_message(request): 
    if request.method == 'POST':

        text = request.POST['text']

        if request.POST['notify_type'] == 'user_query':
                        
            notification_type = request.POST['notify_type']             
            marker = Marker.objects.filter(id=request.POST['marker_id'])[0]
            
            profile = Profile.objects.get(user=request.user)
            profile.trips[marker.id] = marker.title
            profile.save()
            
            if str(request.user.id) in marker.users.keys():
                return JsonResponse({'status': 'You cannot send query twice'})   
            marker.users[str(request.user.id)] = {"is_approved": None, "lat": request.POST['pickup_lat'], "lon": request.POST['pickup_lon'], 'point': request.POST['pickup_point']}
            marker.save()
            text = f"Пользователь отправил Вам запрос на совместную поездку {marker.title}"
        elif request.POST['notify_type'] == 'approve' or request.POST['notify_type'] == 'decline':
            notification_type = request.POST['notify_type']
            Message.objects.filter(notification_type='user_query').delete()
            if request.POST['notify_type'] == 'approve':
                marker = Marker.objects.filter(id=request.POST['marker_id'])[0]
                
                marker.users[request.POST['to_user_id']]['is_approved'] = True                    
                if int(marker.people_count)-1 == 0:
                    marker.is_active = False
                marker.people_count = (marker.people_count-1)
                marker.save()
        else:
            notification_type = ""
            
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
            print('saved')
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

from django.utils import timezone

@login_required
def check_new_messages(request):
    new_messages_raw = Message.objects.filter(to_user=request.user)
    new_messages = {}
    for msg in new_messages_raw:
        if msg.is_read == False:
            new_messages[msg.from_user.username] = msg.text
            
    return JsonResponse({'new_messages': new_messages})

@login_required(login_url='login')
def map_view(request):
    # Проверка на просроченные метки
    now = timezone.now()
    Marker.objects.filter(is_active=True, active_to__lt=now).update(is_active=False)

    # Вывод только актуальных меток
    markers = Marker.objects.filter(is_active=True)
    
    return render(request, 'main/map.html', {'markers': markers})


@login_required(login_url='login')
def add_marker(request):
    if request.method == 'POST':
        print(request.POST)
        form = MarkerForm(request.POST, request.FILES)
        user = Profile.objects.get(id=request.user.id)
        if form.is_valid():
            marker = form.save(commit=False)
            marker.user = request.user
            
            if marker.telegram == None:
                marker.telegram = user.telegram
            if marker.vk == None:
                marker.vk == user.vk
            if marker.phone_number == None:
                marker.phone_number = user.phone_number
            if marker.whatsapp == None:
                marker.whatsapp = user.whatsapp
                
            marker.save()
            return redirect('map')
        else:
            print(form.errors)
    else:
        form = MarkerForm()

    return render(request, 'main/add_marker.html', {'form': form})

from .models import Marker, Profile, UserStatus

@login_required(login_url='login')
def profile(request, user_id):
    viewed_user = get_object_or_404(User, id=user_id)
    is_owner = request.user == viewed_user
    print(request.user == viewed_user)

    profile, _ = Profile.objects.get_or_create(user=viewed_user)

    own_markers = Marker.objects.filter(user=viewed_user)
    responded_markers = []

    # Удаляем устаревшие поездки
    trips_raw = profile.trips.copy()
    for trip_id in list(trips_raw.keys()):
        try:
            marker = Marker.objects.get(id=int(trip_id))
            if marker.active_to - timezone.now() >= timedelta(days=2):
                marker.delete()
            else:
                responded_markers.append(marker)
        except Marker.DoesNotExist:
            del trips_raw[trip_id]

    profile.trips = trips_raw
    profile.save()

    user_status, _ = UserStatus.objects.get_or_create(user=viewed_user)
    is_online = user_status.is_online()

    if request.method == 'POST' and is_owner:
        if 'cancel_trip_id' in request.POST:
            marker_id = request.POST.get('cancel_trip_id')
            marker = get_object_or_404(Marker, id=marker_id)

            # Увеличиваем количество пассажиров
            marker.people_count += 1

            # Удаляем пользователя из списка
            if str(request.user.id) in marker.users:
                del marker.users[str(request.user.id)]
                marker.save()

                # Уведомляем создателя маршрута
                Message.objects.create(
                    from_user=request.user,
                    to_user=marker.user,
                    marker=marker,
                    text=f"Пользователь {request.user.username} отказался от поездки '{marker.title}'.",
                    notification_type='user_left'
                )

                # Удаляем поездку из профиля
                if str(marker.id) in profile.trips:
                    del profile.trips[str(marker.id)]
                    profile.save()

            return redirect('profile', user_id=user_id)

        user_form = UserForm(request.POST, instance=viewed_user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        print(request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            profile.first_name = request.POST['first_name']
            profile.last_name = request.POST['last_name']
            profile.photo = profile.photo.url[12:]
            
            profile.save()
            return redirect('profile', user_id=user_id)
    else:
        user_form = UserForm(instance=viewed_user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'main/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'own_markers': own_markers,
        'responded_markers': responded_markers,
        'profile_data': profile,
        'is_online': is_online,
        'is_owner': is_owner,
    })

@login_required
def delete_marker(request, marker_id):
    marker = get_object_or_404(Marker, id=marker_id)

    if request.user == marker.user:
        # Уведомить всех участников
        for user_id in marker.users.keys():
            Message.objects.create(
                from_user=request.user,
                to_user_id=int(user_id),
                marker=marker,
                text=f"Метка '{marker.title}' была удалена её создателем.",
                notification_type='marker_deleted'
            )
        marker.is_active - False
        marker.save()
    return redirect('profile', user_id=request.user.id)

@login_required
def cancel_participation(request, marker_id):
    marker = get_object_or_404(Marker, id=marker_id)

    if str(request.user.id) in marker.users:
        # Увеличить количество пассажиров
        marker.people_count += 1

        # Удалить пользователя из списка
        del marker.users[str(request.user.id)]
        marker.save()

        # Уведомить создателя
        Message.objects.create(
            from_user=request.user,
            to_user=marker.user,
            marker=marker,
            text=f"Пользователь {request.user.username} отказался от поездки '{marker.title}'.",
            notification_type='user_left'
        )

        # Удалить поездку из профиля пользователя
        profile = get_object_or_404(Profile, user=request.user)
        if str(marker.id) in profile.trips:
            del profile.trips[str(marker.id)]
            profile.save()

    return redirect('profile', user_id=request.user.id)

@login_required
def edit_marker(request, marker_id):
    marker = get_object_or_404(Marker, id=marker_id)

    if marker.user != request.user:
        return redirect('map')  # Только автор может редактировать

    if request.method == 'POST':
        # Исключение пользователя
        if 'exclude_user_id' in request.POST:
            excluded_user_id = request.POST.get('exclude_user_id')
            if excluded_user_id in marker.users:
                # Отправить уведомление исключённому пользователю
                excluded_user = User.objects.get(id=excluded_user_id)
                Message.objects.create(
                    from_user=request.user,
                    to_user=excluded_user,
                    marker=marker,
                    notification_type='excluded',
                    text=f"Вы были исключены из поездки: {marker.title}"
                )

                # Удалить метку из trips исключённого
                try:
                    profile = Profile.objects.get(user=excluded_user)
                    if str(marker.id) in profile.trips:
                        del profile.trips[str(marker.id)]
                        profile.save()
                except Profile.DoesNotExist:
                    pass

                # Удалить из списка
                del marker.users[excluded_user_id]
                marker.save()
                messages.success(request, "Пользователь исключён.")
                return redirect('edit_marker', marker_id=marker.id)

        else:
            form = MarkerForm(request.POST, request.FILES, instance=marker)
            if form.is_valid():
                form.save()

                # Рассылка всем участникам об изменениях
                for uid in marker.users.keys():
                    if uid != str(request.user.id):
                        Message.objects.create(
                            from_user=request.user,
                            to_user_id=uid,
                            marker=marker,
                            notification_type='marker_updated',
                            text=f"Информация о поездке '{marker.title}' была обновлена. Подробнее на странице твоего профиля."
                        )

                messages.success(request, "Метка обновлена.")
                return redirect('profile', user_id=request.user.id)
    else:
        form = MarkerForm(instance=marker)

    return render(request, 'main/edit_marker.html', {
        'form': form,
        'marker': marker
    })

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('map')