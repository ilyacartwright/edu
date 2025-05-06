from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import (
    AdminProfile, TeacherProfile, StudentProfile, 
    MethodistProfile, DeanProfile, UserNotificationSetting
)
from .serializers import (
    UserSerializer, UserCreateSerializer, AdminProfileSerializer, 
    TeacherProfileSerializer, StudentProfileSerializer, 
    MethodistProfileSerializer, DeanProfileSerializer,
    UserNotificationSettingSerializer
)
from .permissions import IsAdminOrSelf, IsAdminOrTeacher, IsUserRoleMatch

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """API для управления пользователями"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'username', 'email', 'last_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Получить профиль пользователя в зависимости от роли"""
        user = self.get_object()
        
        if user.role == 'admin' and hasattr(user, 'admin_profile'):
            serializer = AdminProfileSerializer(user.admin_profile)
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            serializer = TeacherProfileSerializer(user.teacher_profile)
        elif user.role == 'student' and hasattr(user, 'student_profile'):
            serializer = StudentProfileSerializer(user.student_profile)
        elif user.role == 'methodist' and hasattr(user, 'methodist_profile'):
            serializer = MethodistProfileSerializer(user.methodist_profile)
        elif user.role == 'dean' and hasattr(user, 'dean_profile'):
            serializer = DeanProfileSerializer(user.dean_profile)
        else:
            return Response({"error": "Профиль не найден"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def notification_settings(self, request, pk=None):
        """Получить или обновить настройки уведомлений пользователя"""
        user = self.get_object()
        
        if not hasattr(user, 'notification_settings'):
            return Response({"error": "Настройки уведомлений не найдены"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = UserNotificationSettingSerializer(user.notification_settings)
            return Response(serializer.data)
        
        serializer = UserNotificationSettingSerializer(
            user.notification_settings, data=request.data, partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminProfileViewSet(viewsets.ModelViewSet):
    """API для профилей администраторов"""
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['access_level', 'department']

class TeacherProfileViewSet(viewsets.ModelViewSet):
    """API для профилей преподавателей"""
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['department', 'position', 'academic_degree', 'academic_title', 'employment_type']

class StudentProfileViewSet(viewsets.ModelViewSet):
    """API для профилей студентов"""
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'enrollment_year', 'education_form', 'education_basis', 'current_semester', 'academic_status', 'scholarship_status']

class MethodistProfileViewSet(viewsets.ModelViewSet):
    """API для профилей методистов"""
    queryset = MethodistProfile.objects.all()
    serializer_class = MethodistProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['department', 'managed_groups', 'managed_specializations']

class DeanProfileViewSet(viewsets.ModelViewSet):
    """API для профилей деканов/заведующих"""
    queryset = DeanProfile.objects.all()
    serializer_class = DeanProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['faculty', 'department', 'position', 'academic_degree', 'academic_title']

class CurrentUserView(generics.RetrieveUpdateAPIView):
    """API для получения и обновления данных текущего пользователя"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    

class CurrentUserProfileView(generics.RetrieveAPIView):
    """API для получения профиля текущего пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        user = self.request.user
        
        if user.role == 'admin':
            return AdminProfileSerializer
        elif user.role == 'teacher':
            return TeacherProfileSerializer
        elif user.role == 'student':
            return StudentProfileSerializer
        elif user.role == 'methodist':
            return MethodistProfileSerializer
        elif user.role == 'dean':
            return DeanProfileSerializer
        
        return UserSerializer
    
    def get_object(self):
        user = self.request.user
        
        if user.role == 'admin' and hasattr(user, 'admin_profile'):
            return user.admin_profile
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            return user.teacher_profile
        elif user.role == 'student' and hasattr(user, 'student_profile'):
            return user.student_profile
        elif user.role == 'methodist' and hasattr(user, 'methodist_profile'):
            return user.methodist_profile
        elif user.role == 'dean' and hasattr(user, 'dean_profile'):
            return user.dean_profile
        
        # Если профиль не найден, возвращаем самого пользователя
        return user