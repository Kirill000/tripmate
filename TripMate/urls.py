from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from main import views as main_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('login/', main_views.login_user, name='login'),
    path('register/', main_views.register, name='register'),
    path('profile/<int:user_id>', main_views.profile, name='profile'),
    path('reset-password/', main_views.reset_password_request, name='reset-password'),
    path('reset-password-confirm/', main_views.reset_password_confirm, name='reset-password-confirm'),
]