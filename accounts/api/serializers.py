from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from accounts.models import (
    AdminProfile, TeacherProfile, StudentProfile, 
    MethodistProfile, DeanProfile, UserNotificationSetting
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для базовой информации пользователя"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'patronymic', 
                 'full_name', 'role', 'role_display', 'phone_number', 'date_of_birth', 
                 'profile_picture', 'preferred_language', 'date_joined', 'last_login')
        read_only_fields = ('date_joined', 'last_login')

class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 
                 'patronymic', 'role', 'phone_number', 'date_of_birth', 'preferred_language')
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": _("Пароли не совпадают")})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            patronymic=validated_data.get('patronymic', ''),
            role=validated_data['role'],
            phone_number=validated_data.get('phone_number', ''),
            date_of_birth=validated_data.get('date_of_birth', None),
            preferred_language=validated_data.get('preferred_language', 'ru')
        )
        return user

class AdminProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля администратора"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AdminProfile
        fields = ('id', 'user', 'position', 'department', 'access_level', 'responsibility_area')

class TeacherProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля преподавателя"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TeacherProfile
        fields = ('id', 'user', 'employee_id', 'department', 'position', 'academic_degree', 
                 'academic_title', 'employment_type', 'specialization', 'hire_date', 
                 'office_location', 'office_hours', 'bio')

class StudentProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля студента"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ('id', 'user', 'student_id', 'group', 'enrollment_year', 'education_form', 
                 'education_basis', 'current_semester', 'academic_status', 'scholarship_status', 
                 'has_dormitory', 'personal_info')

class MethodistProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля методиста"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MethodistProfile
        fields = ('id', 'user', 'employee_id', 'department', 'responsibilities', 
                 'managed_specializations', 'managed_groups')

class DeanProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля декана/заведующего"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DeanProfile
        fields = ('id', 'user', 'employee_id', 'faculty', 'department', 'position', 
                 'academic_degree', 'academic_title', 'appointment_date', 'term_end_date', 
                 'has_teaching_duties')

class UserNotificationSettingSerializer(serializers.ModelSerializer):
    """Сериализатор для настроек уведомлений пользователя"""
    class Meta:
        model = UserNotificationSetting
        fields = ('email_notifications', 'sms_notifications', 'web_notifications', 
                 'grades_notification', 'schedule_changes', 'course_updates', 'system_messages')
        read_only_fields = ('user',)