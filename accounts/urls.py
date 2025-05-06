from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', include('allauth.urls')),
    path('profile/', views.profile_view, name='profile'),
    # path('profile/edit/', views.profile_edit_view, name='profile_edit'),

]