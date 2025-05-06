from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    SiteSettings, 
    StudentProfileDisplaySettings,
    TeacherProfileDisplaySettings,
    AdminProfileDisplaySettings,
    MethodistProfileDisplaySettings,
    DeanProfileDisplaySettings
)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Основные настройки'), {
            'fields': ('site_name', 'site_description', 'site_keywords', 'site_logo', 'site_favicon')
        }),
        (_('Контактная информация'), {
            'fields': ('contact_email', 'contact_phone', 'footer_text')
        }),
        (_('Социальные сети'), {
            'fields': ('social_vk', 'social_telegram', 'social_instagram', 'social_youtube')
        }),
        (_('Настройки дизайна'), {
            'fields': ('primary_color', 'secondary_color')
        }),
        (_('Системные настройки'), {
            'fields': ('enable_caching', 'maintenance_mode'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Ограничиваем создание только одной записи настроек
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление настроек
        return False

@admin.register(StudentProfileDisplaySettings)
class StudentProfileDisplaySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'show_faculty', 'show_specialization', 'show_group', 
                'show_student_id', 'show_education_form', 'show_education_basis',
                'show_enrollment_year', 'show_current_semester', 'show_academic_status',
                'show_scholarship_status', 'show_dormitory', 'show_personal_info'
            )
        }),
        (_('Разделы профиля'), {
            'fields': (
                'show_skills', 'show_certificates', 'show_achievements',
                'show_courses', 'show_activity', 'show_statistics'
            )
        }),
    )
    
    def has_add_permission(self, request):
        return not StudentProfileDisplaySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(TeacherProfileDisplaySettings)
class TeacherProfileDisplaySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'show_department', 'show_position', 'show_academic_degree',
                'show_academic_title', 'show_employment_type', 'show_specialization',
                'show_hire_date', 'show_office_location', 'show_office_hours', 'show_bio'
            )
        }),
        (_('Разделы профиля'), {
            'fields': ('show_courses', 'show_publications')
        }),
    )
    
    def has_add_permission(self, request):
        return not TeacherProfileDisplaySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AdminProfileDisplaySettings)
class AdminProfileDisplaySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Отображаемые поля'), {
            'fields': (
                'show_position', 'show_department', 'show_access_level',
                'show_responsibility_area'
            )
        }),
    )
    
    def has_add_permission(self, request):
        return not AdminProfileDisplaySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(MethodistProfileDisplaySettings)
class MethodistProfileDisplaySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Отображаемые поля'), {
            'fields': (
                'show_department', 'show_employee_id', 'show_responsibilities',
                'show_managed_specializations', 'show_managed_groups'
            )
        }),
    )
    
    def has_add_permission(self, request):
        return not MethodistProfileDisplaySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(DeanProfileDisplaySettings)
class DeanProfileDisplaySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Отображаемые поля'), {
            'fields': (
                'show_position', 'show_faculty', 'show_department',
                'show_academic_degree', 'show_academic_title', 'show_appointment_date',
                'show_term_end_date', 'show_has_teaching_duties'
            )
        }),
    )
    
    def has_add_permission(self, request):
        return not DeanProfileDisplaySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False