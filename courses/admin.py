from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count
from django.contrib.admin.filters import SimpleListFilter
from django.utils import timezone


from .models import (
    Course,
    CourseSection,
    CourseElementType,
    CourseElement,
    CourseElementAttachment,
    CourseEnrollment,
    CourseElementProgress,
    CourseCertificate,
    CourseReview,
)


class CourseSectionInline(admin.TabularInline):
    """
    Встроенная админка для разделов курса
    """
    model = CourseSection
    extra = 1
    fields = ('title', 'description', 'order', 'is_published', 'is_visible')


class CourseElementInline(admin.TabularInline):
    """
    Встроенная админка для элементов курса в разделе
    """
    model = CourseElement
    extra = 0
    fields = ('title', 'element_type', 'order', 'is_published', 'is_visible', 'estimated_time')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('element_type',)


class CourseElementAttachmentInline(admin.TabularInline):
    """
    Встроенная админка для вложений элемента курса
    """
    model = CourseElementAttachment
    extra = 1
    fields = ('title', 'description', 'file', 'file_size', 'file_type')
    readonly_fields = ('file_size', 'file_type', 'created_at')


class IsActiveFilter(SimpleListFilter):
    """
    Фильтр курсов по статусу активности
    """
    title = _('Статус активности')
    parameter_name = 'is_active'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', _('Активен')),
            ('no', _('Неактивен')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_published=True)
        if self.value() == 'no':
            return queryset.filter(is_published=False)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Админка для курсов
    """
    list_display = ('title', 'subject', 'author', 'is_active_status', 'is_published', 
                  'start_date', 'end_date', 'get_students_count', 'completion_rate')
    list_filter = ('is_published', 'is_public', 'requires_enrollment', 
                 'provides_certificate', 'subject', IsActiveFilter)
    search_fields = ('title', 'description', 'author__username', 'author__first_name', 
                   'author__last_name')
    filter_horizontal = ('co_authors', 'groups')
    readonly_fields = ('created_at', 'updated_at', 'slug', 'completion_rate')
    inlines = [CourseSectionInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'subject', 'academic_plan_subject')
        }),
        (_('Описание'), {
            'fields': ('description', 'short_description')
        }),
        (_('Изображения'), {
            'fields': ('icon', 'cover_image')
        }),
        (_('Авторы'), {
            'fields': ('author', 'co_authors')
        }),
        (_('Группы'), {
            'fields': ('groups',)
        }),
        (_('Настройки доступа'), {
            'fields': ('is_published', 'is_public', 'requires_enrollment')
        }),
        (_('Сроки'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Настройки прохождения'), {
            'fields': ('sequential_progression', 'completion_threshold')
        }),
        (_('Сертификация'), {
            'fields': ('provides_certificate', 'certificate_template')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at', 'completion_rate'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_status(self, obj):
        """Отображение статуса активности с иконкой"""
        if obj.is_active:
            return format_html('<span style="color: green;">&#10004; Активен</span>')
        else:
            return format_html('<span style="color: red;">&#10008; Неактивен</span>')
    is_active_status.short_description = _('Активность')
    
    def get_students_count(self, obj):
        """Получение количества студентов"""
        return obj.enrollments.count()
    get_students_count.short_description = _('Кол-во студентов')
    
    def completion_rate(self, obj):
        """Отображение процента завершения курса"""
        rate = obj.completion_rate
        return f"{rate:.1f}%" if rate > 0 else "0%"
    completion_rate.short_description = _('Процент завершения')
    
    def save_model(self, request, obj, form, change):
        """Автоматическая установка автора при создании"""
        if not change:  # При создании нового объекта
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    """
    Админка для разделов курса
    """
    list_display = ('title', 'course', 'order', 'is_published', 'is_visible', 'get_elements_count')
    list_filter = ('is_published', 'is_visible', 'course')
    search_fields = ('title', 'description', 'course__title')
    inlines = [CourseElementInline]
    
    def get_elements_count(self, obj):
        """Получение количества элементов в разделе"""
        return obj.elements.count()
    get_elements_count.short_description = _('Кол-во элементов')


@admin.register(CourseElementType)
class CourseElementTypeAdmin(admin.ModelAdmin):
    """
    Админка для типов элементов курса
    """
    list_display = ('name', 'code', 'is_gradable', 'max_score', 'get_icon_preview')
    list_filter = ('is_gradable',)
    search_fields = ('name', 'code', 'description')
    
    def get_icon_preview(self, obj):
        """Отображение иконки типа элемента"""
        return format_html('<span style="color: {};">&#9632; {}</span>', 
                         obj.color, obj.icon)
    get_icon_preview.short_description = _('Иконка')


@admin.register(CourseElement)
class CourseElementAdmin(admin.ModelAdmin):
    """
    Админка для элементов курса
    """
    list_display = ('title', 'course', 'section', 'element_type', 'order', 
                  'is_published', 'is_visible', 'estimated_time')
    list_filter = ('is_published', 'is_visible', 'element_type', 'course', 'is_required')
    search_fields = ('title', 'description', 'content', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('course', 'section', 'element_type', 'scheduled_class')
    inlines = [CourseElementAttachmentInline]
    
    fieldsets = (
        (None, {
            'fields': ('course', 'section', 'element_type', 'title')
        }),
        (_('Содержимое'), {
            'fields': ('description', 'content', 'content_format')
        }),
        (_('Отображение'), {
            'fields': ('order', 'estimated_time')
        }),
        (_('Настройки доступа'), {
            'fields': ('is_published', 'is_visible', 'is_required', 'requires_previous_element', 'unlock_date')
        }),
        (_('Расписание'), {
            'fields': ('scheduled_class',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseElementAttachment)
class CourseElementAttachmentAdmin(admin.ModelAdmin):
    """
    Админка для вложений элементов курса
    """
    list_display = ('title', 'course_element', 'get_file_type', 'file_size_display', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('title', 'description', 'course_element__title')
    readonly_fields = ('file_size', 'file_type', 'created_at')
    
    def get_file_type(self, obj):
        """Отображение типа файла в удобочитаемом формате"""
        file_types = {
            'application/pdf': 'PDF',
            'application/msword': 'Word',
            'application/vnd.ms-excel': 'Excel',
            'application/vnd.ms-powerpoint': 'PowerPoint',
            'application/zip': 'ZIP',
            'image/jpeg': 'JPEG',
            'image/png': 'PNG',
            'video/mp4': 'MP4 Видео',
            'audio/mpeg': 'MP3 Аудио',
            'application/octet-stream': 'Файл'
        }
        return file_types.get(obj.file_type, obj.file_type)
    get_file_type.short_description = _('Тип файла')
    
    def file_size_display(self, obj):
        """Отображение размера файла в удобочитаемом формате"""
        if obj.file_size < 1024:
            return f"{obj.file_size} байт"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size/1024:.1f} КБ"
        else:
            return f"{obj.file_size/(1024*1024):.1f} МБ"
    file_size_display.short_description = _('Размер файла')


class EnrollmentStatusFilter(SimpleListFilter):
    """
    Фильтр для статуса записи на курс
    """
    title = _('Статус записи')
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return CourseEnrollment.ENROLLMENT_STATUSES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """
    Админка для записей на курсы
    """
    list_display = ('student', 'course', 'status', 'progress', 'enrolled_at', 
                  'last_accessed', 'completed_at', 'has_certificate')
    list_filter = (EnrollmentStatusFilter, 'course', 'enrolled_at')
    search_fields = ('student__user__username', 'student__user__first_name', 
                   'student__user__last_name', 'course__title')
    readonly_fields = ('enrolled_at', 'last_accessed', 'completed_at')
    
    fieldsets = (
        (None, {
            'fields': ('course', 'student')
        }),
        (_('Статус'), {
            'fields': ('status', 'progress')
        }),
        (_('Даты'), {
            'fields': ('enrolled_at', 'last_accessed', 'completed_at')
        }),
    )
    
    def has_certificate(self, obj):
        """Показывает, есть ли у студента сертификат"""
        try:
            cert = obj.certificate
            return format_html('<span style="color: green;">&#10004; Есть</span>')
        except CourseCertificate.DoesNotExist:
            return format_html('<span style="color: red;">&#10008; Нет</span>')
    has_certificate.short_description = _('Сертификат')
    
    def mark_as_completed(self, request, queryset):
        """Действие для отметки записи как завершенной"""
        for enrollment in queryset:
            enrollment.mark_as_completed()
        self.message_user(request, _("Выбранные записи отмечены как завершенные"))
    mark_as_completed.short_description = _("Отметить как завершенные")
    
    actions = [mark_as_completed]


class ElementProgressFilter(SimpleListFilter):
    """
    Фильтр для прогресса элемента
    """
    title = _('Статус прохождения')
    parameter_name = 'progress_status'
    
    def lookups(self, request, model_admin):
        return (
            ('viewed', _('Просмотрен')),
            ('not_viewed', _('Не просмотрен')),
            ('completed', _('Завершен')),
            ('not_completed', _('Не завершен')),
            ('graded', _('Оценен')),
            ('not_graded', _('Не оценен')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'viewed':
            return queryset.filter(is_viewed=True)
        if self.value() == 'not_viewed':
            return queryset.filter(is_viewed=False)
        if self.value() == 'completed':
            return queryset.filter(is_completed=True)
        if self.value() == 'not_completed':
            return queryset.filter(is_completed=False)
        if self.value() == 'graded':
            return queryset.filter(grade__isnull=False)
        if self.value() == 'not_graded':
            return queryset.filter(grade__isnull=True)
        return queryset


@admin.register(CourseElementProgress)
class CourseElementProgressAdmin(admin.ModelAdmin):
    """
    Админка для прогресса по элементам курса
    """
    list_display = ('course_element', 'enrollment', 'is_viewed', 'is_completed', 
                  'first_viewed_at', 'completed_at', 'time_spent_display', 'grade')
    list_filter = ('is_viewed', 'is_completed', ElementProgressFilter, 
                 'enrollment__course')
    search_fields = ('enrollment__student__user__username', 'enrollment__student__user__first_name', 
                   'enrollment__student__user__last_name', 'course_element__title')
    readonly_fields = ('first_viewed_at', 'last_viewed_at', 'completed_at', 'time_spent', 'graded_at')
    
    fieldsets = (
        (None, {
            'fields': ('enrollment', 'course_element')
        }),
        (_('Прогресс'), {
            'fields': ('is_viewed', 'is_completed', 'time_spent')
        }),
        (_('Даты'), {
            'fields': ('first_viewed_at', 'last_viewed_at', 'completed_at')
        }),
        (_('Оценка'), {
            'fields': ('grade', 'grade_percent', 'graded_by', 'graded_at', 'feedback')
        }),
    )
    
    def time_spent_display(self, obj):
        """Отображение затраченного времени в удобочитаемом формате"""
        if obj.time_spent < 60:
            return f"{obj.time_spent} сек."
        elif obj.time_spent < 3600:
            minutes = obj.time_spent // 60
            seconds = obj.time_spent % 60
            return f"{minutes} мин. {seconds} сек."
        else:
            hours = obj.time_spent // 3600
            minutes = (obj.time_spent % 3600) // 60
            return f"{hours} ч. {minutes} мин."
    time_spent_display.short_description = _('Затраченное время')
    
    def save_model(self, request, obj, form, change):
        """Автоматическая установка пользователя при выставлении оценки"""
        if 'grade' in form.changed_data or 'grade_percent' in form.changed_data:
            obj.graded_by = request.user
            obj.graded_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def mark_as_viewed(self, request, queryset):
        """Действие для отметки элемента как просмотренного"""
        for progress in queryset:
            progress.mark_as_viewed()
        self.message_user(request, _("Выбранные элементы отмечены как просмотренные"))
    mark_as_viewed.short_description = _("Отметить как просмотренные")
    
    def mark_as_completed(self, request, queryset):
        """Действие для отметки элемента как завершенного"""
        for progress in queryset:
            progress.mark_as_completed()
        self.message_user(request, _("Выбранные элементы отмечены как завершенные"))
    mark_as_completed.short_description = _("Отметить как завершенные")
    
    actions = [mark_as_viewed, mark_as_completed]


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    """
    Админка для сертификатов курсов
    """
    list_display = ('certificate_number', 'enrollment', 'issued_at', 'expiration_date', 'is_valid_status')
    list_filter = ('issued_at', 'expiration_date')
    search_fields = ('certificate_number', 'enrollment__student__user__username', 
                   'enrollment__student__user__first_name', 'enrollment__student__user__last_name', 
                   'enrollment__course__title')
    readonly_fields = ('certificate_number', 'issued_at')
    filter_horizontal = ('signed_by',)
    
    fieldsets = (
        (None, {
            'fields': ('enrollment', 'certificate_number')
        }),
        (_('Сертификат'), {
            'fields': ('certificate_file', 'additional_info')
        }),
        (_('Срок действия'), {
            'fields': ('issued_at', 'expiration_date')
        }),
        (_('Подписи'), {
            'fields': ('signed_by',)
        }),
    )
    
    def is_valid_status(self, obj):
        """Отображение статуса действительности сертификата"""
        if obj.is_valid:
            return format_html('<span style="color: green;">&#10004; Действителен</span>')
        else:
            return format_html('<span style="color: red;">&#10008; Недействителен</span>')
    is_valid_status.short_description = _('Статус')


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    """
    Админка для отзывов о курсах
    """
    list_display = ('student', 'course', 'rating', 'created_at', 'is_published')
    list_filter = ('rating', 'is_published', 'course')
    search_fields = ('text', 'student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('course', 'student')
        }),
        (_('Отзыв'), {
            'fields': ('rating', 'text', 'is_published')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Настройка административного сайта
admin.site.site_header = _('Система управления курсами')
admin.site.site_title = _('Администрирование курсов')
admin.site.index_title = _('Панель управления')