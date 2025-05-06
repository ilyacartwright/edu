from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Q

from .models import (
    User, AdminProfile, TeacherProfile, TeacherSubject,
    StudentProfile, MethodistProfile, DeanProfile,
    UserSession, UserNotificationSetting
)


class CustomUserAdmin(UserAdmin):
    """
    Административная модель для расширенного пользователя
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {
            'fields': ('last_name', 'first_name', 'patronymic', 'email', 
                       'phone_number', 'date_of_birth', 'profile_picture')
        }),
        (_('Роль и настройки'), {
            'fields': ('role', 'preferred_language')
        }),
        (_('Права доступа'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('Персональная информация'), {
            'fields': ('last_name', 'first_name', 'patronymic', 'role')
        }),
    )
    
    list_display = (
        'username', 'email', 'get_full_name', 'role', 
        'phone_number', 'is_active', 'is_staff', 'profile_link'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = (
        'username', 'email', 'last_name', 'first_name', 
        'patronymic', 'phone_number'
    )
    ordering = ('last_name', 'first_name')
    actions = ['activate_users', 'deactivate_users']
    
    def profile_link(self, obj):
        """
        Отображает ссылку на профиль пользователя в зависимости от его роли
        """
        if obj.role == 'admin' and hasattr(obj, 'admin_profile'):
            url = reverse('admin:accounts_adminprofile_change', args=[obj.admin_profile.id])
            return format_html('<a href="{}">{}</a>', url, _('Профиль администратора'))
        elif obj.role == 'teacher' and hasattr(obj, 'teacher_profile'):
            url = reverse('admin:accounts_teacherprofile_change', args=[obj.teacher_profile.id])
            return format_html('<a href="{}">{}</a>', url, _('Профиль преподавателя'))
        elif obj.role == 'student' and hasattr(obj, 'student_profile'):
            url = reverse('admin:accounts_studentprofile_change', args=[obj.student_profile.id])
            return format_html('<a href="{}">{}</a>', url, _('Профиль студента'))
        elif obj.role == 'methodist' and hasattr(obj, 'methodist_profile'):
            url = reverse('admin:accounts_methodistprofile_change', args=[obj.methodist_profile.id])
            return format_html('<a href="{}">{}</a>', url, _('Профиль методиста'))
        elif obj.role == 'dean' and hasattr(obj, 'dean_profile'):
            url = reverse('admin:accounts_deanprofile_change', args=[obj.dean_profile.id])
            return format_html('<a href="{}">{}</a>', url, _('Профиль декана/заведующего'))
        return '-'
    profile_link.short_description = _('Профиль')
    
    def activate_users(self, request, queryset):
        """Активирует выбранных пользователей"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные пользователи активированы'))
    activate_users.short_description = _('Активировать пользователей')
    
    def deactivate_users(self, request, queryset):
        """Деактивирует выбранных пользователей"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные пользователи деактивированы'))
    deactivate_users.short_description = _('Деактивировать пользователей')


class AdminProfileAdmin(admin.ModelAdmin):
    """
    Административная модель для профилей администраторов
    """
    list_display = (
        'user', 'position', 'department', 'access_level', 'responsibility_area'
    )
    list_filter = ('access_level', 'department')
    search_fields = (
        'user__username', 'user__last_name', 'user__first_name',
        'position', 'responsibility_area'
    )
    list_select_related = ('user', 'department')
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Должность и отдел'), {
            'fields': ('position', 'department')
        }),
        (_('Доступ и ответственность'), {
            'fields': ('access_level', 'responsibility_area')
        }),
    )


class TeacherSubjectInline(admin.TabularInline):
    """
    Встраиваемая форма для предметов, которые ведет преподаватель
    """
    model = TeacherSubject
    extra = 1
    fields = ('subject', 'academic_year', 'semester', 'role')
    autocomplete_fields = ('subject',)
    raw_id_fields = ('subject',)


class TeacherProfileAdmin(admin.ModelAdmin):
    """
    Административная модель для профилей преподавателей
    """
    list_display = (
        'user', 'employee_id', 'department', 'position', 
        'academic_degree', 'academic_title', 'employment_type',
        'subjects_count'
    )
    list_filter = (
        'department', 'position', 'academic_degree', 
        'academic_title', 'employment_type', 'hire_date'
    )
    search_fields = (
        'user__username', 'user__last_name', 'user__first_name',
        'employee_id', 'specialization', 'office_location'
    )
    list_select_related = ('user', 'department')
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Основная информация'), {
            'fields': ('employee_id', 'department', 'hire_date')
        }),
        (_('Должность и статус'), {
            'fields': (
                'position', 'academic_degree', 'academic_title', 
                'employment_type'
            )
        }),
        (_('Специализация и контакты'), {
            'fields': ('specialization', 'office_location', 'office_hours')
        }),
        (_('Дополнительная информация'), {
            'fields': ('bio',),
            'classes': ('collapse',)
        }),
    )
    inlines = [TeacherSubjectInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(subjects_count=Count('teaching_subjects'))
    
    def subjects_count(self, obj):
        """Отображает количество предметов, которые ведет преподаватель"""
        return obj.subjects_count
    subjects_count.short_description = _('Предметов')
    subjects_count.admin_order_field = 'subjects_count'


class StudentProfileAdmin(admin.ModelAdmin):
    """
    Административная модель для профилей студентов
    """
    list_display = (
        'user', 'student_id', 'group', 'enrollment_year', 
        'education_form', 'education_basis', 'current_semester',
        'academic_status', 'scholarship_status', 'has_dormitory'
    )
    list_filter = (
        'group__specialization', 'group', 'enrollment_year', 
        'education_form', 'education_basis', 'current_semester',
        'academic_status', 'scholarship_status', 'has_dormitory'
    )
    search_fields = (
        'user__username', 'user__last_name', 'user__first_name',
        'student_id', 'group__name', 'personal_info'
    )
    list_select_related = ('user', 'group', 'group__specialization')
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Основная информация'), {
            'fields': ('student_id', 'group', 'enrollment_year')
        }),
        (_('Форма обучения'), {
            'fields': ('education_form', 'education_basis', 'current_semester')
        }),
        (_('Статусы'), {
            'fields': ('academic_status', 'scholarship_status', 'has_dormitory')
        }),
        (_('Дополнительная информация'), {
            'fields': ('personal_info',),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'set_active_status', 'set_academic_leave', 'increment_semester',
        'grant_regular_scholarship', 'remove_scholarship'
    ]
    
    def set_active_status(self, request, queryset):
        """Устанавливает активный статус для выбранных студентов"""
        queryset.update(academic_status='active')
        self.message_user(request, _('Выбранные студенты отмечены как активные'))
    set_active_status.short_description = _('Установить статус "Учится"')
    
    def set_academic_leave(self, request, queryset):
        """Устанавливает статус академического отпуска для выбранных студентов"""
        queryset.update(academic_status='academic_leave')
        self.message_user(request, _('Выбранные студенты отправлены в академический отпуск'))
    set_academic_leave.short_description = _('Установить статус "Академический отпуск"')
    
    def increment_semester(self, request, queryset):
        """Увеличивает текущий семестр на 1 для выбранных студентов"""
        for student in queryset:
            student.current_semester += 1
            student.save(update_fields=['current_semester'])
        self.message_user(request, _('Семестр для выбранных студентов увеличен на 1'))
    increment_semester.short_description = _('Увеличить семестр на 1')
    
    def grant_regular_scholarship(self, request, queryset):
        """Назначает обычную стипендию выбранным студентам"""
        queryset.update(scholarship_status='regular')
        self.message_user(request, _('Выбранным студентам назначена обычная стипендия'))
    grant_regular_scholarship.short_description = _('Назначить обычную стипендию')
    
    def remove_scholarship(self, request, queryset):
        """Отменяет стипендию у выбранных студентов"""
        queryset.update(scholarship_status='none')
        self.message_user(request, _('У выбранных студентов отменена стипендия'))
    remove_scholarship.short_description = _('Отменить стипендию')


class MethodistProfileAdmin(admin.ModelAdmin):
    """
    Административная модель для профилей методистов
    """
    list_display = (
        'user', 'employee_id', 'department', 'managed_specializations_count',
        'managed_groups_count'
    )
    list_filter = ('department',)
    search_fields = (
        'user__username', 'user__last_name', 'user__first_name',
        'employee_id', 'responsibilities'
    )
    list_select_related = ('user', 'department')
    filter_horizontal = ('managed_specializations', 'managed_groups')
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Основная информация'), {
            'fields': ('employee_id', 'department', 'responsibilities')
        }),
        (_('Управляемые направления и группы'), {
            'fields': ('managed_specializations', 'managed_groups')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            specializations_count=Count('managed_specializations', distinct=True),
            groups_count=Count('managed_groups', distinct=True)
        )
    
    def managed_specializations_count(self, obj):
        """Отображает количество управляемых направлений"""
        return obj.specializations_count
    managed_specializations_count.short_description = _('Направлений')
    managed_specializations_count.admin_order_field = 'specializations_count'
    
    def managed_groups_count(self, obj):
        """Отображает количество управляемых групп"""
        return obj.groups_count
    managed_groups_count.short_description = _('Групп')
    managed_groups_count.admin_order_field = 'groups_count'


class DeanProfileAdmin(admin.ModelAdmin):
    """
    Административная модель для профилей деканов/заведующих кафедрой
    """
    list_display = (
        'user', 'employee_id', 'position', 'faculty', 'department',
        'academic_degree', 'academic_title', 'appointment_date',
        'term_end_date', 'has_teaching_duties'
    )
    list_filter = (
        'position', 'faculty', 'department', 'academic_degree',
        'academic_title', 'appointment_date', 'has_teaching_duties'
    )
    search_fields = (
        'user__username', 'user__last_name', 'user__first_name',
        'employee_id'
    )
    list_select_related = ('user', 'faculty', 'department')
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Основная информация'), {
            'fields': ('employee_id', 'position')
        }),
        (_('Факультет/Кафедра'), {
            'fields': ('faculty', 'department')
        }),
        (_('Ученые степени и звания'), {
            'fields': ('academic_degree', 'academic_title')
        }),
        (_('Сроки назначения'), {
            'fields': ('appointment_date', 'term_end_date')
        }),
        (_('Дополнительно'), {
            'fields': ('has_teaching_duties',)
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Динамически фильтрует поля факультет/кафедра в зависимости от позиции
        """
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(role='dean')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Проверяет, что указаны нужные поля в зависимости от позиции
        """
        if obj.position in ['dean', 'vice_dean'] and not obj.faculty:
            self.message_user(request, _('Для декана/заместителя декана должен быть указан факультет'), level='error')
            return
        if obj.position == 'head_of_department' and not obj.department:
            self.message_user(request, _('Для заведующего кафедрой должна быть указана кафедра'), level='error')
            return
        super().save_model(request, obj, form, change)


class UserSessionAdmin(admin.ModelAdmin):
    """
    Административная модель для сессий пользователей
    """
    list_display = (
        'user', 'ip_address', 'created_at', 'expired_at', 'is_active'
    )
    list_filter = ('is_active', 'created_at', 'expired_at')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    list_select_related = ('user',)
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent', 'created_at')
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Данные сессии'), {
            'fields': ('session_key', 'ip_address', 'user_agent')
        }),
        (_('Сроки и статус'), {
            'fields': ('created_at', 'expired_at', 'is_active')
        }),
    )
    actions = ['deactivate_sessions']
    
    def deactivate_sessions(self, request, queryset):
        """Деактивирует выбранные сессии"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные сессии деактивированы'))
    deactivate_sessions.short_description = _('Деактивировать сессии')
    
    def has_add_permission(self, request):
        """Запрещает добавление сессий вручную"""
        return False


class UserNotificationSettingAdmin(admin.ModelAdmin):
    """
    Административная модель для настроек уведомлений пользователей
    """
    list_display = (
        'user', 'email_notifications', 'sms_notifications', 'web_notifications',
        'grades_notification', 'schedule_changes', 'course_updates', 'system_messages'
    )
    list_filter = (
        'email_notifications', 'sms_notifications', 'web_notifications',
        'grades_notification', 'schedule_changes', 'course_updates', 'system_messages'
    )
    search_fields = ('user__username', 'user__last_name', 'user__first_name')
    list_select_related = ('user',)
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Способы уведомлений'), {
            'fields': ('email_notifications', 'sms_notifications', 'web_notifications')
        }),
        (_('Типы уведомлений'), {
            'fields': (
                'grades_notification', 'schedule_changes', 
                'course_updates', 'system_messages'
            )
        }),
    )
    actions = [
        'enable_email_notifications', 'disable_email_notifications',
        'enable_all_notifications', 'disable_all_notifications'
    ]
    
    def enable_email_notifications(self, request, queryset):
        """Включает email-уведомления для выбранных пользователей"""
        queryset.update(email_notifications=True)
        self.message_user(request, _('Email-уведомления включены для выбранных пользователей'))
    enable_email_notifications.short_description = _('Включить email-уведомления')
    
    def disable_email_notifications(self, request, queryset):
        """Выключает email-уведомления для выбранных пользователей"""
        queryset.update(email_notifications=False)
        self.message_user(request, _('Email-уведомления выключены для выбранных пользователей'))
    disable_email_notifications.short_description = _('Выключить email-уведомления')
    
    def enable_all_notifications(self, request, queryset):
        """Включает все уведомления для выбранных пользователей"""
        queryset.update(
            email_notifications=True,
            web_notifications=True,
            grades_notification=True,
            schedule_changes=True,
            course_updates=True,
            system_messages=True
        )
        self.message_user(request, _('Все уведомления включены для выбранных пользователей'))
    enable_all_notifications.short_description = _('Включить все уведомления')
    
    def disable_all_notifications(self, request, queryset):
        """Выключает все уведомления для выбранных пользователей"""
        queryset.update(
            email_notifications=False,
            sms_notifications=False,
            web_notifications=False,
            grades_notification=False,
            schedule_changes=False,
            course_updates=False,
            system_messages=False
        )
        self.message_user(request, _('Все уведомления выключены для выбранных пользователей'))
    disable_all_notifications.short_description = _('Выключить все уведомления')


# Регистрация моделей в админке
admin.site.register(User, CustomUserAdmin)
admin.site.register(AdminProfile, AdminProfileAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)
admin.site.register(TeacherSubject)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(MethodistProfile, MethodistProfileAdmin)
admin.site.register(DeanProfile, DeanProfileAdmin)
admin.site.register(UserSession, UserSessionAdmin)
admin.site.register(UserNotificationSetting, UserNotificationSettingAdmin)