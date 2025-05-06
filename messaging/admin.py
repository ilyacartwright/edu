from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter
from django.db.models import Count

from .models import (
    Message, MessageAttachment, MessageThread, ThreadMessage,
    ThreadMessageReadStatus, ThreadMessageAttachment, GroupMessage,
    GroupMessageAttachment, GroupMessageReadStatus, Notification,
    NotificationPreference, Announcement, AnnouncementAttachment,
    AnnouncementCategory, AnnouncementReadStatus
)


class MessageAttachmentInline(admin.TabularInline):
    """
    Встраиваемая форма для вложений сообщений
    """
    model = MessageAttachment
    extra = 1
    fields = ('file', 'filename', 'file_size', 'content_type')
    readonly_fields = ('file_size', 'content_type')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Административная модель для личных сообщений
    """
    list_display = (
        'subject', 'sender', 'recipient', 'created_at', 
        'is_read', 'read_at', 'is_deleted_display'
    )
    list_filter = (
        'is_read', 'is_deleted_by_sender', 'is_deleted_by_recipient',
        'created_at', 'is_starred_by_sender', 'is_starred_by_recipient'
    )
    search_fields = (
        'subject', 'body', 'sender__username', 'sender__first_name', 'sender__last_name',
        'recipient__username', 'recipient__first_name', 'recipient__last_name'
    )
    date_hierarchy = 'created_at'
    inlines = [MessageAttachmentInline]
    fieldsets = (
        (_('Отправитель и получатель'), {
            'fields': ('sender', 'recipient')
        }),
        (_('Содержание'), {
            'fields': ('subject', 'body')
        }),
        (_('Статус сообщения'), {
            'fields': (
                'is_read', 'read_at', 'is_deleted_by_sender', 
                'is_deleted_by_recipient', 'is_starred_by_sender', 
                'is_starred_by_recipient'
            )
        }),
        (_('Метаданные'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'read_at')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def is_deleted_display(self, obj):
        """Отображает статус удаления сообщения"""
        if obj.is_completely_deleted:
            return _('Удалено полностью')
        elif obj.is_deleted_by_sender:
            return _('Удалено отправителем')
        elif obj.is_deleted_by_recipient:
            return _('Удалено получателем')
        return _('Активно')
    is_deleted_display.short_description = _('Статус удаления')
    
    def mark_as_read(self, request, queryset):
        """Отмечает выбранные сообщения как прочитанные"""
        now = timezone.now()
        queryset.filter(is_read=False).update(is_read=True, read_at=now)
        count = queryset.filter(is_read=False).count()
        self.message_user(request, _(f'Отмечено как прочитанные: {count} сообщений'))
    mark_as_read.short_description = _('Отметить как прочитанные')
    
    def mark_as_unread(self, request, queryset):
        """Отмечает выбранные сообщения как непрочитанные"""
        queryset.filter(is_read=True).update(is_read=False, read_at=None)
        count = queryset.filter(is_read=True).count()
        self.message_user(request, _(f'Отмечено как непрочитанные: {count} сообщений'))
    mark_as_unread.short_description = _('Отметить как непрочитанные')


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    """
    Административная модель для вложений сообщений
    """
    list_display = (
        'filename', 'message_display', 'file_size_display', 
        'content_type', 'file'
    )
    list_filter = ('content_type',)
    search_fields = (
        'filename', 'message__subject', 'message__sender__username',
        'message__recipient__username'
    )
    
    def message_display(self, obj):
        """Отображает информацию о сообщении"""
        url = reverse('admin:messaging_message_change', args=[obj.message.id])
        return format_html(
            '<a href="{}">{} → {}: {}</a>',
            url, obj.message.sender, obj.message.recipient, obj.message.subject
        )
    message_display.short_description = _('Сообщение')
    
    def file_size_display(self, obj):
        """Отображает размер файла в удобном формате"""
        if obj.file_size < 1024:
            return f"{obj.file_size} Б"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} КБ"
        else:
            return f"{obj.file_size / (1024 * 1024):.2f} МБ"
    file_size_display.short_description = _('Размер файла')
    file_size_display.admin_order_field = 'file_size'


class ThreadMessageInline(admin.TabularInline):
    """
    Встраиваемая форма для сообщений в цепочке
    """
    model = ThreadMessage
    extra = 1
    fields = ('sender', 'body', 'created_at', 'read_count')
    readonly_fields = ('created_at', 'read_count')
    
    def read_count(self, obj):
        """Отображает количество пользователей, прочитавших сообщение"""
        if obj.pk:
            return obj.read_by.count()
        return 0
    read_count.short_description = _('Прочитано')


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    """
    Административная модель для цепочек сообщений
    """
    list_display = (
        'subject', 'participants_display', 'messages_count',
        'created_at', 'last_message_at'
    )
    list_filter = ('created_at', 'last_message_at')
    search_fields = (
        'subject', 'participants__username', 'participants__first_name',
        'participants__last_name', 'messages__body'
    )
    filter_horizontal = ('participants',)
    inlines = [ThreadMessageInline]
    date_hierarchy = 'last_message_at'
    fieldsets = (
        (_('Информация о цепочке'), {
            'fields': ('subject', 'participants')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'last_message_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(messages_count=Count('messages'))
    
    def participants_display(self, obj):
        """Отображает список участников"""
        participants = list(obj.participants.all())
        if len(participants) <= 3:
            return ", ".join([str(p) for p in participants])
        else:
            return f"{', '.join([str(p) for p in participants[:3]])} и еще {len(participants) - 3}"
    participants_display.short_description = _('Участники')
    
    def messages_count(self, obj):
        """Отображает количество сообщений в цепочке"""
        return obj.messages_count
    messages_count.admin_order_field = 'messages_count'
    messages_count.short_description = _('Сообщений')


class ThreadMessageAttachmentInline(admin.TabularInline):
    """
    Встраиваемая форма для вложений сообщений в цепочке
    """
    model = ThreadMessageAttachment
    extra = 1
    fields = ('file', 'filename', 'file_size', 'content_type')
    readonly_fields = ('file_size', 'content_type')


class ThreadMessageReadStatusInline(admin.TabularInline):
    """
    Встраиваемая форма для статусов прочтения сообщений в цепочке
    """
    model = ThreadMessageReadStatus
    extra = 0
    fields = ('user', 'read_at')
    readonly_fields = ('read_at',)


@admin.register(ThreadMessage)
class ThreadMessageAdmin(admin.ModelAdmin):
    """
    Административная модель для сообщений в цепочке
    """
    list_display = (
        'thread_subject', 'sender', 'body_preview', 
        'created_at', 'read_by_count'
    )
    list_filter = ('created_at', 'thread')
    search_fields = (
        'body', 'sender__username', 'sender__first_name',
        'sender__last_name', 'thread__subject'
    )
    inlines = [ThreadMessageAttachmentInline, ThreadMessageReadStatusInline]
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Связь с цепочкой'), {
            'fields': ('thread', 'sender')
        }),
        (_('Содержание'), {
            'fields': ('body',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)
    filter_horizontal = ('read_by',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(read_by_count=Count('read_by'))
    
    def thread_subject(self, obj):
        """Отображает тему цепочки"""
        url = reverse('admin:messaging_messagethread_change', args=[obj.thread.id])
        return format_html('<a href="{}">{}</a>', url, obj.thread.subject)
    thread_subject.short_description = _('Тема цепочки')
    thread_subject.admin_order_field = 'thread__subject'
    
    def body_preview(self, obj):
        """Отображает предпросмотр текста сообщения"""
        if len(obj.body) > 50:
            return f"{obj.body[:50]}..."
        return obj.body
    body_preview.short_description = _('Текст')
    
    def read_by_count(self, obj):
        """Отображает количество пользователей, прочитавших сообщение"""
        return obj.read_by_count
    read_by_count.short_description = _('Прочитано')
    read_by_count.admin_order_field = 'read_by_count'


class GroupMessageAttachmentInline(admin.TabularInline):
    """
    Встраиваемая форма для вложений групповых сообщений
    """
    model = GroupMessageAttachment
    extra = 1
    fields = ('file', 'filename', 'file_size', 'content_type')
    readonly_fields = ('file_size', 'content_type')


class GroupMessageReadStatusInline(admin.TabularInline):
    """
    Встраиваемая форма для статусов прочтения групповых сообщений
    """
    model = GroupMessageReadStatus
    extra = 0
    fields = ('user', 'read_at')
    readonly_fields = ('read_at',)


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    """
    Административная модель для групповых сообщений
    """
    list_display = (
        'subject', 'sender', 'recipient_info', 'created_at',
        'read_by_count', 'is_important', 'is_announcement'
    )
    list_filter = (
        'created_at', 'recipient_type', 'is_important', 'is_announcement'
    )
    search_fields = (
        'subject', 'body', 'sender__username', 'sender__first_name',
        'sender__last_name', 'recipient_name'
    )
    inlines = [GroupMessageAttachmentInline, GroupMessageReadStatusInline]
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Отправитель и получатель'), {
            'fields': ('sender', 'content_type', 'object_id', 'recipient_type', 'recipient_name')
        }),
        (_('Содержание'), {
            'fields': ('subject', 'body')
        }),
        (_('Флаги'), {
            'fields': ('is_important', 'is_announcement')
        }),
        (_('Метаданные'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'recipient_type', 'recipient_name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(read_by_count=Count('read_by'))
    
    def recipient_info(self, obj):
        """Отображает информацию о получателе"""
        return f"{obj.recipient_type}: {obj.recipient_name}"
    recipient_info.short_description = _('Получатель')
    
    def read_by_count(self, obj):
        """Отображает количество пользователей, прочитавших сообщение"""
        return obj.read_by_count
    read_by_count.short_description = _('Прочитано')
    read_by_count.admin_order_field = 'read_by_count'


class NotificationTypeFilter(SimpleListFilter):
    """
    Фильтр по типу уведомления
    """
    title = _('тип уведомления')
    parameter_name = 'notification_type'

    def lookups(self, request, model_admin):
        return Notification.NOTIFICATION_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(notification_type=self.value())
        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Административная модель для уведомлений
    """
    list_display = (
        'title', 'user', 'notification_type', 'is_read',
        'created_at', 'read_at', 'is_important'
    )
    list_filter = (
        NotificationTypeFilter, 'is_read', 'is_important', 'created_at'
    )
    search_fields = (
        'title', 'message', 'user__username', 'user__first_name',
        'user__last_name'
    )
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Тип и связь'), {
            'fields': ('notification_type', 'content_type', 'object_id')
        }),
        (_('Содержание'), {
            'fields': ('title', 'message', 'link', 'icon', 'icon_color')
        }),
        (_('Статус'), {
            'fields': ('is_read', 'read_at', 'is_important')
        }),
        (_('Метаданные'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'read_at')
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_important', 'mark_as_normal']
    
    def mark_as_read(self, request, queryset):
        """Отмечает выбранные уведомления как прочитанные"""
        now = timezone.now()
        queryset.filter(is_read=False).update(is_read=True, read_at=now)
        count = queryset.filter(is_read=False).count()
        self.message_user(request, _(f'Отмечено как прочитанные: {count} уведомлений'))
    mark_as_read.short_description = _('Отметить как прочитанные')
    
    def mark_as_unread(self, request, queryset):
        """Отмечает выбранные уведомления как непрочитанные"""
        queryset.filter(is_read=True).update(is_read=False, read_at=None)
        count = queryset.filter(is_read=True).count()
        self.message_user(request, _(f'Отмечено как непрочитанные: {count} уведомлений'))
    mark_as_unread.short_description = _('Отметить как непрочитанные')
    
    def mark_as_important(self, request, queryset):
        """Отмечает выбранные уведомления как важные"""
        queryset.update(is_important=True)
        self.message_user(request, _('Выбранные уведомления отмечены как важные'))
    mark_as_important.short_description = _('Отметить как важные')
    
    def mark_as_normal(self, request, queryset):
        """Отмечает выбранные уведомления как обычные"""
        queryset.update(is_important=False)
        self.message_user(request, _('Выбранные уведомления отмечены как обычные'))
    mark_as_normal.short_description = _('Отметить как обычные')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Административная модель для настроек уведомлений
    """
    list_display = (
        'user', 'web_notifications', 'email_notifications', 
        'sms_notifications', 'push_notifications',
        'notification_time_range'
    )
    list_filter = (
        'web_notifications', 'email_notifications', 'sms_notifications',
        'push_notifications', 'system_notifications', 'academic_notifications',
        'message_notifications', 'schedule_notifications', 'grade_notifications',
        'course_notifications', 'announcement_notifications'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name'
    )
    fieldsets = (
        (_('Пользователь'), {
            'fields': ('user',)
        }),
        (_('Способы доставки'), {
            'fields': (
                'web_notifications', 'email_notifications',
                'sms_notifications', 'push_notifications'
            )
        }),
        (_('Типы уведомлений'), {
            'fields': (
                'system_notifications', 'academic_notifications',
                'message_notifications', 'schedule_notifications',
                'grade_notifications', 'course_notifications',
                'announcement_notifications'
            )
        }),
        (_('Время уведомлений'), {
            'fields': ('notification_start_time', 'notification_end_time')
        }),
    )
    actions = [
        'enable_all_notifications', 'disable_all_notifications',
        'enable_email_notifications', 'disable_email_notifications'
    ]
    
    def notification_time_range(self, obj):
        """Отображает диапазон времени для уведомлений"""
        return f"{obj.notification_start_time.strftime('%H:%M')} - {obj.notification_end_time.strftime('%H:%M')}"
    notification_time_range.short_description = _('Время уведомлений')
    
    def enable_all_notifications(self, request, queryset):
        """Включает все уведомления для выбранных настроек"""
        queryset.update(
            web_notifications=True,
            email_notifications=True,
            push_notifications=True,
            system_notifications=True,
            academic_notifications=True,
            message_notifications=True,
            schedule_notifications=True,
            grade_notifications=True,
            course_notifications=True,
            announcement_notifications=True
        )
        self.message_user(request, _('Все уведомления включены для выбранных пользователей'))
    enable_all_notifications.short_description = _('Включить все уведомления')
    
    def disable_all_notifications(self, request, queryset):
        """Выключает все уведомления для выбранных настроек"""
        queryset.update(
            web_notifications=False,
            email_notifications=False,
            sms_notifications=False,
            push_notifications=False,
            system_notifications=False,
            academic_notifications=False,
            message_notifications=False,
            schedule_notifications=False,
            grade_notifications=False,
            course_notifications=False,
            announcement_notifications=False
        )
        self.message_user(request, _('Все уведомления выключены для выбранных пользователей'))
    disable_all_notifications.short_description = _('Выключить все уведомления')
    
    def enable_email_notifications(self, request, queryset):
        """Включает email-уведомления для выбранных настроек"""
        queryset.update(email_notifications=True)
        self.message_user(request, _('Email-уведомления включены для выбранных пользователей'))
    enable_email_notifications.short_description = _('Включить email-уведомления')
    
    def disable_email_notifications(self, request, queryset):
        """Выключает email-уведомления для выбранных настроек"""
        queryset.update(email_notifications=False)
        self.message_user(request, _('Email-уведомления выключены для выбранных пользователей'))
    disable_email_notifications.short_description = _('Выключить email-уведомления')


class AnnouncementAttachmentInline(admin.TabularInline):
    """
    Встраиваемая форма для вложений объявлений
    """
    model = AnnouncementAttachment
    extra = 1
    fields = ('file', 'filename', 'file_size', 'content_type')
    readonly_fields = ('file_size', 'content_type')


class AnnouncementReadStatusInline(admin.TabularInline):
    """
    Встраиваемая форма для статусов прочтения объявлений
    """
    model = AnnouncementReadStatus
    extra = 0
    fields = ('user', 'read_at')
    readonly_fields = ('read_at',)


class AnnouncementStatusFilter(SimpleListFilter):
    """
    Фильтр по активности объявления
    """
    title = _('активность')
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Активные')),
            ('no', _('Неактивные')),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'yes':
            return queryset.filter(
                status='published',
                start_date__lte=today
            ).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
            )
        elif self.value() == 'no':
            return queryset.exclude(
                status='published',
                start_date__lte=today
            ).exclude(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
            )
        return queryset


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    Административная модель для объявлений
    """
    list_display = (
        'title', 'author', 'target_info', 'status',
        'priority', 'is_active_display', 'created_at', 'read_count'
    )
    list_filter = (
        'status', 'priority', AnnouncementStatusFilter, 'is_public',
        'category', 'send_notification', 'show_on_dashboard'
    )
    search_fields = (
        'title', 'content', 'author__username', 'author__first_name',
        'author__last_name', 'target_name'
    )
    date_hierarchy = 'created_at'
    inlines = [AnnouncementAttachmentInline, AnnouncementReadStatusInline]
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title', 'content', 'author', 'category')
        }),
        (_('Целевая аудитория'), {
            'fields': ('is_public', 'content_type', 'object_id', 'target_type', 'target_name')
        }),
        (_('Период действия'), {
            'fields': ('start_date', 'end_date', 'status')
        }),
        (_('Важность и настройки'), {
            'fields': ('priority', 'send_notification', 'show_on_dashboard')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'target_type', 'target_name')
    actions = [
        'publish_announcements', 'archive_announcements',
        'set_high_priority', 'set_normal_priority'
    ]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(read_count=Count('read_statuses'))
    
    def target_info(self, obj):
        """Отображает информацию о целевой аудитории"""
        if obj.is_public:
            return _('Все пользователи')
        elif obj.target_group:
            return f"{obj.target_type}: {obj.target_name}"
        return _('Не указано')
    target_info.short_description = _('Целевая аудитория')
    
    def is_active_display(self, obj):
        """Отображает активность объявления"""
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = _('Активно')
    
    def read_count(self, obj):
        """Отображает количество пользователей, прочитавших объявление"""
        return obj.read_count
    read_count.short_description = _('Прочитано')
    read_count.admin_order_field = 'read_count'
    
    def publish_announcements(self, request, queryset):
        """Публикует выбранные объявления"""
        queryset.update(status='published')
        self.message_user(request, _('Выбранные объявления опубликованы'))
    publish_announcements.short_description = _('Опубликовать')
    
    def archive_announcements(self, request, queryset):
        """Архивирует выбранные объявления"""
        queryset.update(status='archived')
        self.message_user(request, _('Выбранные объявления перемещены в архив'))
    archive_announcements.short_description = _('Переместить в архив')
    
    def set_high_priority(self, request, queryset):
        """Устанавливает высокий приоритет для выбранных объявлений"""
        queryset.update(priority='high')
        self.message_user(request, _('Установлен высокий приоритет для выбранных объявлений'))
    set_high_priority.short_description = _('Установить высокий приоритет')
    
    def set_normal_priority(self, request, queryset):
        """Устанавливает обычный приоритет для выбранных объявлений"""
        queryset.update(priority='normal')
        self.message_user(request, _('Установлен обычный приоритет для выбранных объявлений'))
    set_normal_priority.short_description = _('Установить обычный приоритет')


@admin.register(AnnouncementCategory)
class AnnouncementCategoryAdmin(admin.ModelAdmin):
    """
    Административная модель для категорий объявлений
    """
    list_display = ('name', 'slug', 'color_display', 'announcements_count')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Внешний вид'), {
            'fields': ('icon', 'color')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(announcements_count=Count('announcements'))
    
    def color_display(self, obj):
        """Отображает цвет категории с образцом"""
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = _('Цвет')
    
    def announcements_count(self, obj):
        """Отображает количество объявлений в категории"""
        return obj.announcements_count
    announcements_count.short_description = _('Объявлений')
    announcements_count.admin_order_field = 'announcements_count'


@admin.register(AnnouncementAttachment)
class AnnouncementAttachmentAdmin(admin.ModelAdmin):
    """
    Административная модель для вложений объявлений
    """
    list_display = (
        'filename', 'announcement_display', 'file_size_display', 
        'content_type', 'file'
    )
    list_filter = ('content_type',)
    search_fields = (
        'filename', 'announcement__title', 'announcement__author__username',
    )
    
    def announcement_display(self, obj):
        """Отображает информацию об объявлении"""
        url = reverse('admin:messaging_announcement_change', args=[obj.announcement.id])
        return format_html('<a href="{}">{}</a>', url, obj.announcement.title)
    announcement_display.short_description = _('Объявление')
    
    def file_size_display(self, obj):
        """Отображает размер файла в удобном формате"""
        if obj.file_size < 1024:
            return f"{obj.file_size} Б"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} КБ"
        else:
            return f"{obj.file_size / (1024 * 1024):.2f} МБ"
    file_size_display.short_description = _('Размер файла')
    file_size_display.admin_order_field = 'file_size'


@admin.register(AnnouncementReadStatus)
class AnnouncementReadStatusAdmin(admin.ModelAdmin):
    """
    Административная модель для статусов прочтения объявлений
    """
    list_display = ('user', 'announcement_title', 'read_at')
    list_filter = ('read_at',)
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'announcement__title'
    )
    date_hierarchy = 'read_at'
    
    def announcement_title(self, obj):
        """Отображает заголовок объявления"""
        url = reverse('admin:messaging_announcement_change', args=[obj.announcement.id])
        return format_html('<a href="{}">{}</a>', url, obj.announcement.title)
    announcement_title.short_description = _('Объявление')
    announcement_title.admin_order_field = 'announcement__title'


@admin.register(ThreadMessageReadStatus)
class ThreadMessageReadStatusAdmin(admin.ModelAdmin):
    """
    Административная модель для статусов прочтения сообщений в цепочке
    """
    list_display = ('user', 'message_preview', 'thread_title', 'read_at')
    list_filter = ('read_at',)
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'message__body', 'message__thread__subject'
    )
    date_hierarchy = 'read_at'
    
    def message_preview(self, obj):
        """Отображает предпросмотр сообщения"""
        text = obj.message.body[:50] + ('...' if len(obj.message.body) > 50 else '')
        url = reverse('admin:messaging_threadmessage_change', args=[obj.message.id])
        return format_html('<a href="{}">{}</a>', url, text)
    message_preview.short_description = _('Сообщение')
    
    def thread_title(self, obj):
        """Отображает тему цепочки"""
        url = reverse('admin:messaging_messagethread_change', args=[obj.message.thread.id])
        return format_html('<a href="{}">{}</a>', url, obj.message.thread.subject)
    thread_title.short_description = _('Тема цепочки')
    thread_title.admin_order_field = 'message__thread__subject'


@admin.register(GroupMessageReadStatus)
class GroupMessageReadStatusAdmin(admin.ModelAdmin):
    """
    Административная модель для статусов прочтения групповых сообщений
    """
    list_display = ('user', 'message_subject', 'read_at')
    list_filter = ('read_at',)
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'message__subject', 'message__body'
    )
    date_hierarchy = 'read_at'
    
    def message_subject(self, obj):
        """Отображает тему сообщения"""
        url = reverse('admin:messaging_groupmessage_change', args=[obj.message.id])
        return format_html('<a href="{}">{}</a>', url, obj.message.subject)
    message_subject.short_description = _('Сообщение')
    message_subject.admin_order_field = 'message__subject'


@admin.register(ThreadMessageAttachment)
class ThreadMessageAttachmentAdmin(admin.ModelAdmin):
    """
    Административная модель для вложений сообщений в цепочке
    """
    list_display = (
        'filename', 'message_preview', 'thread_title',
        'file_size_display', 'content_type', 'file'
    )
    list_filter = ('content_type',)
    search_fields = (
        'filename', 'message__body', 'message__thread__subject'
    )
    
    def message_preview(self, obj):
        """Отображает предпросмотр сообщения"""
        text = obj.message.body[:50] + ('...' if len(obj.message.body) > 50 else '')
        url = reverse('admin:messaging_threadmessage_change', args=[obj.message.id])
        return format_html('<a href="{}">{}</a>', url, text)
    message_preview.short_description = _('Сообщение')
    
    def thread_title(self, obj):
        """Отображает тему цепочки"""
        url = reverse('admin:messaging_messagethread_change', args=[obj.message.thread.id])
        return format_html('<a href="{}">{}</a>', url, obj.message.thread.subject)
    thread_title.short_description = _('Тема цепочки')
    
    def file_size_display(self, obj):
        """Отображает размер файла в удобном формате"""
        if obj.file_size < 1024:
            return f"{obj.file_size} Б"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} КБ"
        else:
            return f"{obj.file_size / (1024 * 1024):.2f} МБ"
    file_size_display.short_description = _('Размер файла')
    file_size_display.admin_order_field = 'file_size'


@admin.register(GroupMessageAttachment)
class GroupMessageAttachmentAdmin(admin.ModelAdmin):
    """
    Административная модель для вложений групповых сообщений
    """
    list_display = (
        'filename', 'message_subject', 'file_size_display', 
        'content_type', 'file'
    )
    list_filter = ('content_type',)
    search_fields = (
        'filename', 'message__subject', 'message__body'
    )
    
    def message_subject(self, obj):
        """Отображает тему сообщения"""
        url = reverse('admin:messaging_groupmessage_change', args=[obj.message.id])
        return format_html('<a href="{}">{}</a>', url, obj.message.subject)
    message_subject.short_description = _('Сообщение')
    message_subject.admin_order_field = 'message__subject'
    
    def file_size_display(self, obj):
        """Отображает размер файла в удобном формате"""
        if obj.file_size < 1024:
            return f"{obj.file_size} Б"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} КБ"
        else:
            return f"{obj.file_size / (1024 * 1024):.2f} МБ"
    file_size_display.short_description = _('Размер файла')
    file_size_display.admin_order_field = 'file_size'


# В самом низу файла добавляем дополнительные настройки админки
# для этого модуля

# Добавляем кастомный заголовок для админки этого приложения
admin.site.site_header = _('Система управления учебным процессом')
admin.site.site_title = _('Панель администратора')
admin.site.index_title = _('Модули системы')