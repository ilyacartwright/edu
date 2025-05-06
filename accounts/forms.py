from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from .models import (
    User, AdminProfile, TeacherProfile, StudentProfile, 
    MethodistProfile, DeanProfile, UserNotificationSetting
)

class UserEditForm(forms.ModelForm):
    """Форма для редактирования основной информации пользователя"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'patronymic', 'email', 
                  'phone_number', 'date_of_birth', 'profile_picture', 
                  'preferred_language')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class ProfileEditForm(forms.ModelForm):
    """Динамическая форма для редактирования расширенного профиля"""
    def __init__(self, *args, **kwargs):
        role = kwargs.pop('role', None)
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        
        # Определяем класс модели в зависимости от роли
        if role == 'admin':
            self.Meta.model = AdminProfile
            self.fields = [field for field in self.fields if field in [
                'position', 'responsibility_area'
            ]]
        elif role == 'teacher':
            self.Meta.model = TeacherProfile
            self.fields = [field for field in self.fields if field in [
                'specialization', 'office_location', 'office_hours', 'bio'
            ]]
        elif role == 'student':
            self.Meta.model = StudentProfile
            self.fields = [field for field in self.fields if field in [
                'personal_info', 'has_dormitory'
            ]]
        elif role == 'methodist':
            self.Meta.model = MethodistProfile
            self.fields = [field for field in self.fields if field in [
                'responsibilities'
            ]]
        elif role == 'dean':
            self.Meta.model = DeanProfile
            self.fields = [field for field in self.fields if field in [
                'has_teaching_duties'
            ]]
    
    class Meta:
        model = None  # Будет установлено динамически
        fields = '__all__'
        exclude = ['user']

class UserCreationAdminForm(UserCreationForm):
    """Форма создания пользователя для администратора"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic', 
                  'role', 'phone_number', 'date_of_birth')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class NotificationSettingsForm(forms.ModelForm):
    """Форма настроек уведомлений пользователя"""
    class Meta:
        model = UserNotificationSetting
        exclude = ['user']