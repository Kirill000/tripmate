from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('add/', views.add_marker, name='add_marker'),
    path('send_message/<int:marker_id>/', views.send_message, name='send_message'),
]