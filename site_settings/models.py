from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

class SiteSettings(models.Model):
    """
    Основные настройки сайта
    """
    site_name = models.CharField(_('Название сайта'), max_length=100, default='EduPortal')
    site_description = models.TextField(_('Описание сайта'), blank=True)
    site_keywords = models.TextField(_('Ключевые слова'), blank=True, help_text=_('Через запятую'))
    site_logo = models.ImageField(_('Логотип сайта'), upload_to='site_settings/', blank=True, null=True)
    site_favicon = models.FileField(_('Favicon'), upload_to='site_settings/', blank=True, null=True)
    footer_text = models.TextField(_('Текст футера'), blank=True)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20, blank=True)
    
    # Социальные сети
    social_vk = models.URLField(_('ВКонтакте'), blank=True)
    social_telegram = models.URLField(_('Telegram'), blank=True)
    social_instagram = models.URLField(_('Instagram'), blank=True)
    social_youtube = models.URLField(_('YouTube'), blank=True)
    
    # Настройки дизайна
    primary_color = models.CharField(_('Основной цвет'), max_length=20, default='#3498db', 
                                    help_text=_('HEX или RGB код цвета'))
    secondary_color = models.CharField(_('Дополнительный цвет'), max_length=20, default='#2ecc71',
                                      help_text=_('HEX или RGB код цвета'))
    
    # Настройки производительности
    enable_caching = models.BooleanField(_('Включить кэширование'), default=True)
    maintenance_mode = models.BooleanField(_('Режим обслуживания'), default=False)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('настройки сайта')
        verbose_name_plural = _('настройки сайта')
    
    def __str__(self):
        return str(self.site_name)
    
    def save(self, *args, **kwargs):
        # Убедимся, что всегда есть только одна запись с настройками
        if not self.pk and SiteSettings.objects.exists():
            # Если запись уже существует, обновляем её
            self.pk = SiteSettings.objects.first().pk
        
        # Очистка кэша при обновлении настроек
        cache.delete('site_settings')
        
        # Сохраняем настройки
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """
        Получение настроек сайта с использованием кэша
        """
        settings = cache.get('site_settings')
        if not settings:
            try:
                settings = cls.objects.first()
                if not settings:
                    settings = cls.objects.create()
                cache.set('site_settings', settings)
            except:
                settings = cls()
        return settings

# Модели настроек профилей для разных ролей
class StudentProfileDisplaySettings(models.Model):
    """
    Настройки отображения данных в профиле студента
    """
    show_faculty = models.BooleanField(_('Показывать факультет'), default=True)
    show_specialization = models.BooleanField(_('Показывать направление'), default=True)
    show_group = models.BooleanField(_('Показывать группу'), default=True)
    show_student_id = models.BooleanField(_('Показывать номер студенческого'), default=True)
    show_education_form = models.BooleanField(_('Показывать форму обучения'), default=True)
    show_education_basis = models.BooleanField(_('Показывать основу обучения'), default=True)
    show_enrollment_year = models.BooleanField(_('Показывать год поступления'), default=True)
    show_current_semester = models.BooleanField(_('Показывать текущий семестр'), default=True)
    show_academic_status = models.BooleanField(_('Показывать статус'), default=True)
    show_scholarship_status = models.BooleanField(_('Показывать стипендию'), default=True)
    show_dormitory = models.BooleanField(_('Показывать проживание в общежитии'), default=True)
    show_personal_info = models.BooleanField(_('Показывать личную информацию'), default=True)
    
    # Разделы профиля
    show_skills = models.BooleanField(_('Показывать раздел навыков'), default=True)
    show_certificates = models.BooleanField(_('Показывать раздел сертификатов'), default=True)
    show_achievements = models.BooleanField(_('Показывать раздел достижений'), default=True)
    show_courses = models.BooleanField(_('Показывать раздел курсов'), default=True)
    show_activity = models.BooleanField(_('Показывать раздел активности'), default=True)
    show_statistics = models.BooleanField(_('Показывать раздел статистики'), default=True)
    
    class Meta:
        verbose_name = _('настройки отображения профиля студента')
        verbose_name_plural = _('настройки отображения профиля студента')
    
    def __str__(self):
        return str(_('Настройки отображения профиля студента'))
    
    def save(self, *args, **kwargs):
        # Убедимся, что всегда есть только одна запись настроек
        if not self.pk and StudentProfileDisplaySettings.objects.exists():
            self.pk = StudentProfileDisplaySettings.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        try:
            settings = cls.objects.first()
            if not settings:
                settings = cls.objects.create()
            return settings
        except:
            return cls()
        
    def get_fields_config(self):
        """Возвращает конфигурацию полей для отображения"""
        return {
            'group.specialization.department.faculty.name': {'display_name': _('Факультет'), 'visible': self.show_faculty},
            'group.specialization.name': {'display_name': _('Направление'), 'visible': self.show_specialization},
            'group.name': {'display_name': _('Группа'), 'visible': self.show_group},
            'student_id': {'display_name': _('Номер студенческого'), 'visible': self.show_student_id},
            'education_form': {'display_name': _('Форма обучения'), 'visible': self.show_education_form, 'is_choice': True},
            'education_basis': {'display_name': _('Основа обучения'), 'visible': self.show_education_basis, 'is_choice': True},
            'enrollment_year': {'display_name': _('Год поступления'), 'visible': self.show_enrollment_year},
            'current_semester': {'display_name': _('Текущий семестр'), 'visible': self.show_current_semester},
            'academic_status': {'display_name': _('Статус'), 'visible': self.show_academic_status, 'is_choice': True},
            'scholarship_status': {'display_name': _('Стипендия'), 'visible': self.show_scholarship_status, 'is_choice': True},
            'has_dormitory': {'display_name': _('Проживает в общежитии'), 'visible': self.show_dormitory, 'is_boolean': True}
        }

    def get_sections_config(self):
        """Возвращает конфигурацию разделов для отображения"""
        return {
            'personal_info': {'display_name': _('Дополнительная информация'), 'visible': self.show_personal_info},
            'skills': {'display_name': _('Навыки'), 'visible': self.show_skills},
            'certificates': {'display_name': _('Сертификаты'), 'visible': self.show_certificates},
            'achievements': {'display_name': _('Достижения'), 'visible': self.show_achievements},
            'courses': {'display_name': _('Курсы'), 'visible': self.show_courses},
            'activity': {'display_name': _('Активность'), 'visible': self.show_activity},
            'statistics': {'display_name': _('Статистика'), 'visible': self.show_statistics}
        }

class TeacherProfileDisplaySettings(models.Model):
    """
    Настройки отображения данных в профиле преподавателя
    """
    show_department = models.BooleanField(_('Показывать кафедру'), default=True)
    show_position = models.BooleanField(_('Показывать должность'), default=True)
    show_academic_degree = models.BooleanField(_('Показывать учёную степень'), default=True)
    show_academic_title = models.BooleanField(_('Показывать учёное звание'), default=True)
    show_employment_type = models.BooleanField(_('Показывать тип занятости'), default=True)
    show_specialization = models.BooleanField(_('Показывать специализацию'), default=True)
    show_hire_date = models.BooleanField(_('Показывать дату приёма на работу'), default=True)
    show_office_location = models.BooleanField(_('Показывать местоположение кабинета'), default=True)
    show_office_hours = models.BooleanField(_('Показывать часы консультаций'), default=True)
    show_bio = models.BooleanField(_('Показывать биографию'), default=True)
    
    # Разделы профиля
    show_courses = models.BooleanField(_('Показывать раздел курсов'), default=True)
    show_publications = models.BooleanField(_('Показывать раздел публикаций'), default=True)
    
    class Meta:
        verbose_name = _('настройки отображения профиля преподавателя')
        verbose_name_plural = _('настройки отображения профиля преподавателя')
    
    def __str__(self):
        return str(_('Настройки отображения профиля преподавателя'))
    
    def save(self, *args, **kwargs):
        if not self.pk and TeacherProfileDisplaySettings.objects.exists():
            self.pk = TeacherProfileDisplaySettings.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        try:
            settings = cls.objects.first()
            if not settings:
                settings = cls.objects.create()
            return settings
        except:
            return cls()
        
    def get_fields_config(self):
        return {
            'department.name': {'display_name': _('Кафедра'), 'visible': self.show_department},
            'position': {'display_name': _('Должность'), 'visible': self.show_position, 'is_choice': True},
            'academic_degree': {'display_name': _('Учёная степень'), 'visible': self.show_academic_degree, 'is_choice': True},
            'academic_title': {'display_name': _('Учёное звание'), 'visible': self.show_academic_title, 'is_choice': True},
            'employment_type': {'display_name': _('Тип занятости'), 'visible': self.show_employment_type, 'is_choice': True},
            'specialization': {'display_name': _('Специализация'), 'visible': self.show_specialization},
            'hire_date': {'display_name': _('Дата приема на работу'), 'visible': self.show_hire_date},
            'office_location': {'display_name': _('Местоположение кабинета'), 'visible': self.show_office_location},
            'office_hours': {'display_name': _('Часы консультаций'), 'visible': self.show_office_hours}
        }
    
    def get_sections_config(self):
        return {
            'bio': {'display_name': _('Биография'), 'visible': self.show_bio},
            'courses': {'display_name': _('Курсы'), 'visible': self.show_courses},
            'publications': {'display_name': _('Публикации'), 'visible': self.show_publications}
        }

class AdminProfileDisplaySettings(models.Model):
    """
    Настройки отображения данных в профиле администратора
    """
    show_position = models.BooleanField(_('Показывать должность'), default=True)
    show_department = models.BooleanField(_('Показывать подразделение'), default=True)
    show_access_level = models.BooleanField(_('Показывать уровень доступа'), default=True)
    show_responsibility_area = models.BooleanField(_('Показывать область ответственности'), default=True)
    
    class Meta:
        verbose_name = _('настройки отображения профиля администратора')
        verbose_name_plural = _('настройки отображения профиля администратора')
    
    def __str__(self):
        return str(_('Настройки отображения профиля администратора'))
    
    def save(self, *args, **kwargs):
        if not self.pk and AdminProfileDisplaySettings.objects.exists():
            self.pk = AdminProfileDisplaySettings.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        try:
            settings = cls.objects.first()
            if not settings:
                settings = cls.objects.create()
            return settings
        except:
            return cls()
    def get_fields_config(self):
        return {
            'position': {'display_name': _('Должность'), 'visible': self.show_position},
            'department.name': {'display_name': _('Подразделение'), 'visible': self.show_department},
            'access_level': {'display_name': _('Уровень доступа'), 'visible': self.show_access_level, 'is_choice': True}
        }
    
    def get_sections_config(self):
        return {
            'responsibility_area': {'display_name': _('Область ответственности'), 'visible': self.show_responsibility_area}
        }

class MethodistProfileDisplaySettings(models.Model):
    """
    Настройки отображения данных в профиле методиста
    """
    show_department = models.BooleanField(_('Показывать кафедру'), default=True)
    show_employee_id = models.BooleanField(_('Показывать табельный номер'), default=True)
    show_responsibilities = models.BooleanField(_('Показывать обязанности'), default=True)
    show_managed_specializations = models.BooleanField(_('Показывать курируемые специализации'), default=True)
    show_managed_groups = models.BooleanField(_('Показывать курируемые группы'), default=True)
    
    class Meta:
        verbose_name = _('настройки отображения профиля методиста')
        verbose_name_plural = _('настройки отображения профиля методиста')
    
    def __str__(self):
        return str(_('Настройки отображения профиля методиста'))
    
    def save(self, *args, **kwargs):
        if not self.pk and MethodistProfileDisplaySettings.objects.exists():
            self.pk = MethodistProfileDisplaySettings.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        try:
            settings = cls.objects.first()
            if not settings:
                settings = cls.objects.create()
            return settings
        except:
            return cls()
        
    def get_fields_config(self):
        return {
            'department.name': {'display_name': _('Кафедра'), 'visible': self.show_department},
            'employee_id': {'display_name': _('Табельный номер'), 'visible': self.show_employee_id}
        }
    
    def get_sections_config(self):
        return {
            'responsibilities': {'display_name': _('Обязанности'), 'visible': self.show_responsibilities},
            'managed_specializations': {'display_name': _('Курируемые специализации'), 'visible': self.show_managed_specializations},
            'managed_groups': {'display_name': _('Курируемые группы'), 'visible': self.show_managed_groups}
        }

class DeanProfileDisplaySettings(models.Model):
    """
    Настройки отображения данных в профиле декана/заведующего кафедрой
    """
    show_position = models.BooleanField(_('Показывать должность'), default=True)
    show_faculty = models.BooleanField(_('Показывать факультет'), default=True)
    show_department = models.BooleanField(_('Показывать кафедру'), default=True)
    show_academic_degree = models.BooleanField(_('Показывать учёную степень'), default=True)
    show_academic_title = models.BooleanField(_('Показывать учёное звание'), default=True)
    show_appointment_date = models.BooleanField(_('Показывать дату назначения'), default=True)
    show_term_end_date = models.BooleanField(_('Показывать срок окончания полномочий'), default=True)
    show_has_teaching_duties = models.BooleanField(_('Показывать преподавательскую деятельность'), default=True)
    
    class Meta:
        verbose_name = _('настройки отображения профиля декана/заведующего')
        verbose_name_plural = _('настройки отображения профиля декана/заведующего')
    
    def __str__(self):
        return str(_('Настройки отображения профиля декана/заведующего'))
    
    def save(self, *args, **kwargs):
        if not self.pk and DeanProfileDisplaySettings.objects.exists():
            self.pk = DeanProfileDisplaySettings.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        try:
            settings = cls.objects.first()
            if not settings:
                settings = cls.objects.create()
            return settings
        except:
            return cls()
        
    def get_fields_config(self):
        return {
            'position': {'display_name': _('Должность'), 'visible': self.show_position, 'is_choice': True},
            'faculty.name': {'display_name': _('Факультет'), 'visible': self.show_faculty},
            'department.name': {'display_name': _('Кафедра'), 'visible': self.show_department},
            'academic_degree': {'display_name': _('Учёная степень'), 'visible': self.show_academic_degree, 'is_choice': True},
            'academic_title': {'display_name': _('Учёное звание'), 'visible': self.show_academic_title, 'is_choice': True},
            'appointment_date': {'display_name': _('Дата назначения'), 'visible': self.show_appointment_date},
            'term_end_date': {'display_name': _('Срок окончания полномочий'), 'visible': self.show_term_end_date},
            'has_teaching_duties': {'display_name': _('Преподавательская деятельность'), 'visible': self.show_has_teaching_duties, 'is_boolean': True}
        }
    
    def get_sections_config(self):
        return {}