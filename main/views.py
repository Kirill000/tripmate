from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from .models import *
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from math import radians, cos, sin, asin, sqrt
import os
# from TripMate.settings import os.getcwd()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    
    #проверка на диалог с самим собой
    if request.user != to_user:
            
        try:
            if marker.user.id == request.user.id:
                user_query_data = marker.users[str(to_user_id)]
            else:
                user_query_data = marker.users[str(request.user.id)]
        except KeyError:
            user_query_data = None
        
        return render(request, 'main/chat.html', {
            'marker': marker,
            'to_user': to_user,
            'user_query_data': user_query_data
        })
        
    else:
        
        return redirect('map')
        

@login_required
def dialog_list(request):
    #список диалогов
    messages = Message.objects.filter(to_user=request.user).select_related('from_user', 'marker').order_by('-timestamp')
    unique_senders = {}
    
    for m in messages:
        key = (m.from_user.id, m.marker.id)
        if key not in unique_senders:
            unique_senders[key] = m

    return render(request, 'main/dialog_list.html', {'dialogs': unique_senders.values()})

@login_required
def get_messages(request, marker_id, to_user_id):
    #получение сообщений для определенного диалога
    
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
    
    #если отправляем сообщение (метод принимает только post запросы)
    if request.method == 'POST':

        text = request.POST['text']
        
        if 'notify_type' in request.POST:
            #пробиваем на тип сообщения - бывают либо запрос на поездку, либо ответ от пользователя, создавшего метку на поездку
            if request.POST['notify_type'] == 'user_query':
                
                #тип сообщения для сохранения в диалог
                notification_type = request.POST['notify_type']
                
                #если это запрос от пользователя на совместную поездку - ищем маркер
                marker = Marker.objects.filter(id=request.POST['marker_id'])[0]
                
                #добавляем пользователю, от которого запрос, в поле trips айдишник этого маркера
                profile = Profile.objects.get(user=request.user)
                profile.trips[marker.id] = marker.title
                profile.save()
                
                #проверка на повторную отправку зарпроса
                if str(request.user.id) in marker.users.keys():
                    # return JsonResponse({'status': 'You cannot send query twice'})   
                    return redirect('profile', request.user.id)

                #добавляем пользователя в маркер
                marker.users[str(request.user.id)] = {"is_approved": None, "lat": request.POST['pickup_lat'], "lon": request.POST['pickup_lon'], 'point': request.POST['pickup_point']}
                marker.save()
                
                #текст сообщения в диалог
                text = f"Пользователь отправил Вам запрос на совместную поездку {marker.title}"
                
            elif request.POST['notify_type'] == 'approve' or request.POST['notify_type'] == 'decline':
                
                #тип сообщения для сохранения в диалог
                notification_type = request.POST['notify_type']
                
                #удаляем сообщение с запросом на поездку
                Message.objects.filter(notification_type='user_query').delete()
                
                marker = Marker.objects.filter(id=request.POST['marker_id'])[0]
                
                #если создатель согласился
                if request.POST['notify_type'] == 'approve':
                    
                    marker.users[request.POST['to_user_id']]['is_approved'] = True            
                    
                    #если оставался последний человек - скрываем метку с общего поиска        
                    if int(marker.people_count)-1 == 0:
                        marker.is_active = False
                    
                    #переназначаем количество человек
                    marker.people_count = (marker.people_count-1)
                    marker.save()
                    
                    #текст сообщения в диалог
                    text = f"Пользователь {request.user} подтвердил Ваш запрос на поездку!"
                else:
                    
                    marker.users[request.POST['to_user_id']]['is_approved'] = False
                    marker.save()
                    
                    #текст сообщения в диалог
                    text = f"К сожалению пользователь {request.user} отказал Вам в поездке :("
            else:
                notification_type = ""
        else:
            notification_type = ""
            
        to_user_id = request.POST['to_user_id']
        marker_id = request.POST['marker_id']
        
        #проверка на попытку отправить сообщение самому себе
        if int(to_user_id) != request.user.id:
            Message.objects.create(
                from_user=request.user,
                notification_type=notification_type,
                to_user_id=to_user_id,
                marker_id=marker_id,
                text=text
            )

            return JsonResponse({'status': 'ok'})
        
    #ошибка если пытаемся осуществить get запрос
    return JsonResponse({'status': 'error'})

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # радиус Земли в километрах
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

@login_required
def nearby_markers(request):
    try:
        lat = float(request.GET.get("lat"))
        lon = float(request.GET.get("lon"))
        radius = float(request.GET.get("radius", 10))  # радиус в км, по умолчанию 10 км
        print(lat, lon, radius)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid parameters"}, status=400)
    
    Marker.objects.filter(is_active=True, active_to__lt=request.GET.get("ctime")).update(is_active=False)

    markers = Marker.objects.filter(is_active=True)
    nearby = []
    
    for marker in markers:
        distance = haversine(lat, lon, marker.start_lat, marker.start_lon)
        if distance*1000 <= radius and radius < 10000:
            nearby.append({
                "id": marker.id,
                "is_active": marker.is_active,
                "title": marker.title,
                "user": marker.user.id,  # id пользователя
                "transport_type": marker.get_transport_type_display() if not marker.transport_type == None else marker.other_transport,
                "people_count": marker.people_count,
                "start_point": marker.start_point,
                "start_lat": marker.start_lat,
                "start_lon": marker.start_lon,
                "end_point": marker.end_point,
                "end_lat": marker.end_lat,
                "end_lon": marker.end_lon,
                "landmark_photo": marker.landmark_photo.url if marker.landmark_photo else None,
                "landmark_description": marker.landmark_description,
                "price": float(marker.price),
                "active_from": marker.active_from.isoformat(),
                "active_to": marker.active_to.isoformat(),
                "comment": marker.comment,
                "telegram": marker.telegram,
                "whatsapp": marker.whatsapp,
                "vk": marker.vk,
                "phone_number": marker.phone_number,
                "users": marker.users,  # JSON-поле
                "distance_km": round(distance, 2),
            })
            print(marker.start_lat, marker.start_lon, distance)

    nearby.sort(key=lambda x: x["distance_km"])  # сортируем по расстоянию
    return JsonResponse({"markers": nearby})

@login_required
def check_new_messages(request):
    #посик новых сообщений + вывод уведомлений на фронте
    new_messages_raw = Message.objects.filter(to_user=request.user)
    new_messages = {}
    for msg in new_messages_raw:
        if msg.is_read == False:
            new_messages[msg.from_user.username] = msg.text
            
    return JsonResponse({'new_messages': new_messages})

@login_required(login_url='login')
def map_view(request):
    return render(request, 'main/map.html', {"marker_image": "/static/images/marker.png", "marker_image_2": "/static/images/marker_x.png"})


@login_required(login_url='login')
def add_marker(request):
    
    #создание метки
    if request.method == 'POST':

        form = MarkerForm(request.POST, request.FILES)
        try:
            user = Profile.objects.get(id=request.user.id)
        except:
            return redirect('profile', request.user.id)
        if form.is_valid():
            marker = form.save(commit=False)
            marker.user = request.user
            
            #добавляем контакты из профиля            
            if marker.telegram == None:
                marker.telegram = user.telegram
            if marker.vk == None:
                marker.vk = user.vk
            if marker.phone_number == None:
                marker.phone_number = user.phone_number
            if marker.whatsapp == None:
                marker.whatsapp = user.whatsapp
                
            if marker.landmark_photo != None:
                os.rename(os.path.join(BASE_DIR, 'main'+marker.landmark_photo.url[5:]), os.path.join(BASE_DIR, f"main//static/images/landmark{request.user.id}"))
                marker.landmark_photo = f"/images/landmark{request.user.id}"
                
            marker.save()
            return redirect('map')
        else:
            print(form.errors)
    else:
        #форма для создания метки
        form = MarkerForm()

    return render(request, 'main/add_marker.html', {'form': form})

@login_required(login_url='login')
def profile(request, user_id):
    print(os.getcwd())
    cwd = os.getcwd()
    time_value = request.headers.get('X-Timestamp')
    print(time_value)
    
    #получаем объект просматриваемого пользователя из двух моделей
    viewed_user = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=viewed_user)
    
    #является ли страница его собственной
    is_owner = request.user == viewed_user

    #ищем свои метки и метки, на которые откликались
    own_markers = []
    own_markers_raw = Marker.objects.filter(user=viewed_user)
    responded_markers = []

    # Удаляем устаревшие поездки - после перевода их статуса в инактив они хранятся еще двое суток
    trips_raw = profile.trips.copy()
    for trip_id in list(trips_raw.keys()):
        try:
            marker = Marker.objects.get(id=int(trip_id))
            # if timezone.now()-marker.active_to >= timedelta(days=2):
            #     marker.delete()
            # elif marker.active_to <= timezone.now():
            #     marker.is_active = False
            #     marker.save()
            #     marker.refresh_from_db()
            #     responded_markers.append(marker)
            # else:
            responded_markers.append(marker)
        except Marker.DoesNotExist:
            del trips_raw[trip_id]
            
    for marker in own_markers_raw:
        if timezone.now()-marker.active_to >= timedelta(days=2):
            marker.delete()
        elif marker.active_to <= timezone.now():
            print(marker)
            marker.is_active = False
            marker.save()
            marker.refresh_from_db()
            own_markers.append(marker)
        else:
            own_markers.append(marker)
    
    own_markers = own_markers_raw
    # responded_markers
    
    profile.trips = trips_raw
    profile.save()

    #онлайн статус
    user_status, _ = UserStatus.objects.get_or_create(user=viewed_user)
    is_online = user_status.is_online()

    #на post запросы отвечаем только если пользователь собственник своей страницы
    if request.method == 'POST' and is_owner:
        
        #если отменяем выбранную поездку
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
        else:
            #принимаем форму
            user_form = UserForm(request.POST, instance=viewed_user)
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                
                profile.first_name = request.POST['first_name']
                profile.last_name = request.POST['last_name']

                os.rename(os.path.join(BASE_DIR, 'main'+profile.photo.url[5:]), os.path.join(BASE_DIR, f"main/static/images/profile_logo{request.user.id}.jpg"))
                profile.photo = f"/images/profile_logo{request.user.id}.jpg"
                
                profile.save()
                return redirect('profile', user_id=user_id)
            
    elif is_owner:
        user_form = UserForm(instance=viewed_user)
        profile_form = ProfileForm(instance=profile)
    else:
        user_form = []
        profile_form = []

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
            
        #делаем инактив статус
        marker.is_active = False
        marker.save()
        
    return redirect('profile', user_id=request.user.id)

# @login_required
# def cancel_participation(request, marker_id):
#     #отменяем поездку пользователем, выбравшим метку
#     marker = get_object_or_404(Marker, id=marker_id)

#     if str(request.user.id) in marker.users:
#         # Увеличить количество пассажиров
#         marker.people_count += 1

#         # Удалить пользователя из списка
#         del marker.users[str(request.user.id)]
#         marker.save()

#         # Уведомить создателя
#         Message.objects.create(
#             from_user=request.user,
#             to_user=marker.user,
#             marker=marker,
#             text=f"Пользователь {request.user.username} отказался от поездки '{marker.title}'.",
#             notification_type='user_left'
#         )

#         # Удалить поездку из профиля пользователя
#         profile = get_object_or_404(Profile, user=request.user)
#         if str(marker.id) in profile.trips:
#             del profile.trips[str(marker.id)]
#             profile.save()

#     return redirect('profile', user_id=request.user.id)

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