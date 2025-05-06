from django.urls import path, include
from django.contrib.auth.views import LogoutView
from allauth.account import views as allauth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Переопределяем URL-маршруты allauth
    path('login/', allauth_views.LoginView.as_view(), name='account_login'),
    path('logout/', allauth_views.LogoutView.as_view(), name='account_logout'),
    path('password/reset/', allauth_views.PasswordResetView.as_view(), name='account_reset_password'),
    path('password/reset/done/', allauth_views.PasswordResetDoneView.as_view(), name='account_reset_password_done'),
    path('password/reset/key/<uidb36>-<key>/', allauth_views.PasswordResetFromKeyView.as_view(), name='account_reset_password_from_key'),
    path('password/reset/key/done/', allauth_views.PasswordResetFromKeyDoneView.as_view(), name='account_reset_password_from_key_done'),
    path('password/change/', allauth_views.PasswordChangeView.as_view(), name='account_change_password'),
    path('signup/', views.signup_redirect, name='account_signup'),

    
    
    # Наши пути
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/notifications/', views.notification_settings_view, name='notification_settings'),
]