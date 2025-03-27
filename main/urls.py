from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('add/', views.add_marker, name='add_marker'),
    # Страница диалога (чат с пользователем по маркеру)
    path('chat/<int:marker_id>/<int:to_user_id>/', views.chat_page, name='chat_page'),

    # AJAX — получение сообщений
    path('get-messages/<int:marker_id>/<int:to_user_id>/', views.get_messages, name='get_messages'),

    # AJAX — отправка сообщения
    path('send-message', views.send_message, name='send_message'),

    # Страница со списком всех диалогов
    path('dialogs/', views.dialog_list, name='dialog_list'),
    path('check-new-messages/', views.check_new_messages, name='check_new_messages'),
    path('marker/<int:marker_id>/delete/', views.delete_marker, name='delete_marker'),
    # path('marker/<int:marker_id>/cancel/', views.cancel_participation, name='cancel_participation'),
    path('marker/<int:marker_id>/edit/', views.edit_marker, name='edit_marker'),
    path('markers/', views.nearby_markers, name='get_markers'),

    # AJAX — получение количества непрочитанных сообщений (для уведомлений)
    # path('get-unread-count/', views.get_unread_count, name='get_unread_count'),
]