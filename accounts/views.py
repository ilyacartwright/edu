from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse
from .utils import get_nested_field_value

from .models import User, AdminProfile, TeacherProfile, StudentProfile, MethodistProfile, DeanProfile
from .forms import ProfileEditForm, UserEditForm

@login_required
def profile_view(request):
    """Представление для отображения профиля пользователя"""
    user = request.user
    
    # Определение типа профиля
    profile = None
    profile_settings = None
    
    if user.role == 'admin' and hasattr(user, 'admin_profile'):
        profile = user.admin_profile
        from site_settings.models import AdminProfileDisplaySettings
        profile_settings = AdminProfileDisplaySettings.get_settings()
    elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        profile = user.teacher_profile
        from site_settings.models import TeacherProfileDisplaySettings
        profile_settings = TeacherProfileDisplaySettings.get_settings()
    elif user.role == 'student' and hasattr(user, 'student_profile'):
        profile = user.student_profile
        from site_settings.models import StudentProfileDisplaySettings
        profile_settings = StudentProfileDisplaySettings.get_settings()
    elif user.role == 'methodist' and hasattr(user, 'methodist_profile'):
        profile = user.methodist_profile
        from site_settings.models import MethodistProfileDisplaySettings
        profile_settings = MethodistProfileDisplaySettings.get_settings()
    elif user.role == 'dean' and hasattr(user, 'dean_profile'):
        profile = user.dean_profile
        from site_settings.models import DeanProfileDisplaySettings
        profile_settings = DeanProfileDisplaySettings.get_settings()
    
    # Получаем конфигурацию полей и разделов
    fields_config = {}
    sections_config = {}
    
    if profile_settings:
        fields_config = profile_settings.get_fields_config()
        sections_config = profile_settings.get_sections_config()
    
    # Получаем значения полей
    fields_values = {}
    
    for field_name, config in fields_config.items():
        if config['visible']:
            value = get_nested_field_value(profile, field_name)
            if value is not None:
                fields_values[field_name] = {
                    'display_name': config['display_name'],
                    'value': value,
                    'is_choice': config.get('is_choice', False),
                    'is_boolean': config.get('is_boolean', False)
                }
    
    # Получаем значения разделов
    sections_values = {}
    
    for section_name, config in sections_config.items():
        if config['visible']:
            value = get_nested_field_value(profile, section_name)
            sections_values[section_name] = {
                'display_name': config['display_name'],
                'value': value
            }
    
    return render(request, 'account/profile.html', {
        'user': user,
        'profile': profile,
        'profile_settings': profile_settings,
        'fields_values': fields_values,
        'sections_values': sections_values
    })

@login_required
def profile_edit_view(request):
    """Представление для редактирования профиля пользователя"""
    user = request.user

    # Определение типа профиля
    profile = None
    if user.role == 'admin' and hasattr(user, 'admin_profile'):
        profile = user.admin_profile
    elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        profile = user.teacher_profile
    elif user.role == 'student' and hasattr(user, 'student_profile'):
        profile = user.student_profile
    elif user.role == 'methodist' and hasattr(user, 'methodist_profile'):
        profile = user.methodist_profile
    elif user.role == 'dean' and hasattr(user, 'dean_profile'):
        profile = user.dean_profile


    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=profile, role=user.role)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Профиль успешно обновлен'))
            return redirect('accounts:profile')
        
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile, role=user.role)

    return render(request, 'account/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

@login_required
def notification_settings_view(request):
    """Представление для обновления настроек уведомлений"""
    if request.method == 'POST':
        user = request.user
        settings = user.notification_settings
        
        # Обновляем настройки
        settings.email_notifications = 'email_notifications' in request.POST
        settings.sms_notifications = 'sms_notifications' in request.POST
        settings.web_notifications = 'web_notifications' in request.POST
        settings.grades_notification = 'grades_notification' in request.POST
        settings.schedule_changes = 'schedule_changes' in request.POST
        settings.course_updates = 'course_updates' in request.POST
        settings.system_messages = 'system_messages' in request.POST
        
        settings.save()
        messages.success(request, _('Настройки уведомлений успешно обновлены'))
        
    return redirect('accounts:profile')


def signup_redirect(request):
    """Перенаправляем со страницы регистрации на вход в систему"""
    return redirect(reverse('accounts:account_login'))