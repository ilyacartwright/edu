from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

# Создаем роутер для API
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'admin-profiles', views.AdminProfileViewSet)
router.register(r'teacher-profiles', views.TeacherProfileViewSet)
router.register(r'student-profiles', views.StudentProfileViewSet)
router.register(r'methodist-profiles', views.MethodistProfileViewSet)
router.register(r'dean-profiles', views.DeanProfileViewSet)

app_name = 'accounts_api'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Текущий пользователь
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    path('me/profile/', views.CurrentUserProfileView.as_view(), name='current-user-profile'),
    
    # Аутентификация с JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]