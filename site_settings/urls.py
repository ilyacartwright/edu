from django.urls import path
from . import views

app_name = 'site_settings'

urlpatterns = [
    path('favicon.ico', views.favicon_view, name='favicon'),
]