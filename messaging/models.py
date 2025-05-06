from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
User = get_user_model()

class Message(models.Model):
    """
    Модель личного сообщения между пользователями
    """
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                              related_name='sent_messages', verbose_name=_('Отправитель'))
    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                 related_name='received_messages', verbose_name=_('Получатель'))
    
    subject = models.CharField(_('Тема'), max_length=255)
    body = models.TextField(_('Текст сообщения'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_read = models.BooleanField(_('Прочитано'), default=False)
    read_at = models.DateTimeField(_('Дата прочтения'), null=True, blank=True)
    
    # Дополнительные флаги
    is_deleted_by_sender = models.BooleanField(_('Удалено отправителем'), default=False)
    is_deleted_by_recipient = models.BooleanField(_('Удалено получателем'), default=False)
    is_starred_by_sender = models.BooleanField(_('Помечено отправителем'), default=False)
    is_starred_by_recipient = models.BooleanField(_('Помечено получателем'), default=False)
    
    class Meta:
        verbose_name = _('личное сообщение')
        verbose_name_plural = _('личные сообщения')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.subject}"
    
    def mark_as_read(self):
        """Помечает сообщение как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def is_completely_deleted(self):
        """
        Проверяет, удалено ли сообщение и отправителем, и получателем
        """
        return self.is_deleted_by_sender and self.is_deleted_by_recipient


class MessageAttachment(models.Model):
    """
    Модель вложения к сообщению
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, 
                               related_name='attachments', verbose_name=_('Сообщение'))
    file = models.FileField(_('Файл'), upload_to='message_attachments/')
    filename = models.CharField(_('Имя файла'), max_length=255)
    file_size = models.PositiveIntegerField(_('Размер файла'), default=0)  # В байтах
    content_type = models.CharField(_('Тип содержимого'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('вложение к сообщению')
        verbose_name_plural = _('вложения к сообщениям')
    
    def __str__(self):
        return f"{self.filename} ({self.message})"


class MessageThread(models.Model):
    """
    Модель цепочки сообщений
    """
    participants = models.ManyToManyField('accounts.User', related_name='message_threads', 
                                         verbose_name=_('Участники'))
    subject = models.CharField(_('Тема'), max_length=255)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    last_message_at = models.DateTimeField(_('Дата последнего сообщения'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('цепочка сообщений')
        verbose_name_plural = _('цепочки сообщений')
        ordering = ['-last_message_at']
    
    def __str__(self):
        participant_names = ", ".join([user.get_full_name() for user in self.participants.all()[:3]])
        if self.participants.count() > 3:
            participant_names += f" и еще {self.participants.count() - 3}"
        return f"{self.subject} ({participant_names})"


class ThreadMessage(models.Model):
    """
    Модель сообщения в цепочке
    """
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, 
                              related_name='messages', verbose_name=_('Цепочка'))
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                              related_name='thread_messages', verbose_name=_('Отправитель'))
    body = models.TextField(_('Текст сообщения'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    # Читатели сообщения
    read_by = models.ManyToManyField('accounts.User', related_name='read_thread_messages', 
                                    through='ThreadMessageReadStatus', blank=True,
                                    verbose_name=_('Прочитано пользователями'))
    
    class Meta:
        verbose_name = _('сообщение в цепочке')
        verbose_name_plural = _('сообщения в цепочке')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender}: {self.body[:50]}"
    
    def save(self, *args, **kwargs):
        # Обновляем время последнего сообщения в цепочке
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        if is_new:
            self.thread.last_message_at = self.created_at
            self.thread.save(update_fields=['last_message_at'])


class ThreadMessageReadStatus(models.Model):
    """
    Модель статуса прочтения сообщения в цепочке
    """
    message = models.ForeignKey(ThreadMessage, on_delete=models.CASCADE, verbose_name=_('Сообщение'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name=_('Пользователь'))
    read_at = models.DateTimeField(_('Время прочтения'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('статус прочтения сообщения')
        verbose_name_plural = _('статусы прочтения сообщений')
        unique_together = ('message', 'user')
    
    def __str__(self):
        return f"{self.user} прочитал {self.message} в {self.read_at}"


class ThreadMessageAttachment(models.Model):
    """
    Модель вложения к сообщению в цепочке
    """
    message = models.ForeignKey(ThreadMessage, on_delete=models.CASCADE, 
                               related_name='attachments', verbose_name=_('Сообщение'))
    file = models.FileField(_('Файл'), upload_to='thread_message_attachments/')
    filename = models.CharField(_('Имя файла'), max_length=255)
    file_size = models.PositiveIntegerField(_('Размер файла'), default=0)  # В байтах
    content_type = models.CharField(_('Тип содержимого'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('вложение к сообщению в цепочке')
        verbose_name_plural = _('вложения к сообщениям в цепочке')
    
    def __str__(self):
        return f"{self.filename} ({self.message})"


class GroupMessage(models.Model):
    """
    Модель группового сообщения (для групп, кафедр, факультетов)
    """
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                              related_name='sent_group_messages', verbose_name=_('Отправитель'))
    
    # Тип получателя и ссылка на него (Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    recipient_group = GenericForeignKey('content_type', 'object_id')
    
    # Информация о группе-получателе (кэшированная)
    recipient_type = models.CharField(_('Тип получателя'), max_length=50)  # group, department, faculty, etc.
    recipient_name = models.CharField(_('Название получателя'), max_length=255)
    
    subject = models.CharField(_('Тема'), max_length=255)
    body = models.TextField(_('Текст сообщения'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    # Получатели, прочитавшие сообщение
    read_by = models.ManyToManyField('accounts.User', related_name='read_group_messages', 
                                    through='GroupMessageReadStatus', blank=True)
    
    # Дополнительные флаги
    is_important = models.BooleanField(_('Важное'), default=False)
    is_announcement = models.BooleanField(_('Объявление'), default=False)
    
    class Meta:
        verbose_name = _('групповое сообщение')
        verbose_name_plural = _('групповые сообщения')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender} -> {self.recipient_name}: {self.subject}"
    
    def save(self, *args, **kwargs):
        # Кэшируем информацию о получателе
        if self.recipient_group:
            self.recipient_type = self.content_type.model
            self.recipient_name = str(self.recipient_group)
        
        super().save(*args, **kwargs)


class GroupMessageAttachment(models.Model):
    """
    Модель вложения к групповому сообщению
    """
    message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE, 
                               related_name='attachments', verbose_name=_('Сообщение'))
    file = models.FileField(_('Файл'), upload_to='group_message_attachments/')
    filename = models.CharField(_('Имя файла'), max_length=255)
    file_size = models.PositiveIntegerField(_('Размер файла'), default=0)  # В байтах
    content_type = models.CharField(_('Тип содержимого'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('вложение к групповому сообщению')
        verbose_name_plural = _('вложения к групповым сообщениям')
    
    def __str__(self):
        return f"{self.filename} ({self.message})"


class GroupMessageReadStatus(models.Model):
    """
    Модель статуса прочтения группового сообщения
    """
    message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE, verbose_name=_('Сообщение'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name=_('Пользователь'))
    read_at = models.DateTimeField(_('Время прочтения'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('статус прочтения группового сообщения')
        verbose_name_plural = _('статусы прочтения групповых сообщений')
        unique_together = ('message', 'user')
    
    def __str__(self):
        return f"{self.user} прочитал {self.message} в {self.read_at}"


class Notification(models.Model):
    """
    Модель уведомления
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='notifications', verbose_name=_('Пользователь'))
    
    # Тип уведомления
    NOTIFICATION_TYPES = (
        ('system', _('Системное')),
        ('academic', _('Учебное')),
        ('message', _('Сообщение')),
        ('schedule', _('Расписание')),
        ('grade', _('Оценка')),
        ('course', _('Курс')),
        ('announcement', _('Объявление')),
        ('other', _('Другое')),
    )
    notification_type = models.CharField(_('Тип уведомления'), max_length=20, choices=NOTIFICATION_TYPES)
    
    # Связь с объектом уведомления (Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Содержимое уведомления
    title = models.CharField(_('Заголовок'), max_length=255)
    message = models.TextField(_('Сообщение'))
    link = models.CharField(_('Ссылка'), max_length=255, blank=True)
    
    # Иконка для отображения
    icon = models.CharField(_('Иконка'), max_length=50, blank=True)
    icon_color = models.CharField(_('Цвет иконки'), max_length=20, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_read = models.BooleanField(_('Прочитано'), default=False)
    read_at = models.DateTimeField(_('Дата прочтения'), null=True, blank=True)
    
    # Дополнительные флаги
    is_important = models.BooleanField(_('Важное'), default=False)
    
    class Meta:
        verbose_name = _('уведомление')
        verbose_name_plural = _('уведомления')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user}: {self.title}"
    
    def mark_as_read(self):
        """Помечает уведомление как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """
    Модель настроек уведомлений пользователя
    """
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, 
                               related_name='notification_preferences', 
                               verbose_name=_('Пользователь'))
    
    # Способы доставки уведомлений
    web_notifications = models.BooleanField(_('Уведомления на сайте'), default=True)
    email_notifications = models.BooleanField(_('Уведомления по email'), default=True)
    sms_notifications = models.BooleanField(_('SMS уведомления'), default=False)
    push_notifications = models.BooleanField(_('Push уведомления'), default=True)
    
    # Настройки типов уведомлений
    system_notifications = models.BooleanField(_('Системные уведомления'), default=True)
    academic_notifications = models.BooleanField(_('Учебные уведомления'), default=True)
    message_notifications = models.BooleanField(_('Уведомления о сообщениях'), default=True)
    schedule_notifications = models.BooleanField(_('Уведомления о расписании'), default=True)
    grade_notifications = models.BooleanField(_('Уведомления об оценках'), default=True)
    course_notifications = models.BooleanField(_('Уведомления о курсах'), default=True)
    announcement_notifications = models.BooleanField(_('Объявления'), default=True)
    
    # Время уведомлений
    notification_start_time = models.TimeField(_('Время начала уведомлений'), default='09:00')
    notification_end_time = models.TimeField(_('Время окончания уведомлений'), default='21:00')
    
    class Meta:
        verbose_name = _('настройки уведомлений')
        verbose_name_plural = _('настройки уведомлений')
    
    def __str__(self):
        return f"Настройки уведомлений: {self.user}"


class Announcement(models.Model):
    """
    Модель объявления (новости)
    """
    title = models.CharField(_('Заголовок'), max_length=255)
    content = models.TextField(_('Содержание'))
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                              related_name='announcements', 
                              verbose_name=_('Автор'))
    
    # Для кого предназначено объявление
    is_public = models.BooleanField(_('Публичное'), default=False)
    
    # Связь с целевой аудиторией (Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_group = GenericForeignKey('content_type', 'object_id')
    
    # Информация о группе-получателе (кэшированная)
    target_type = models.CharField(_('Тип целевой группы'), max_length=50, blank=True)  # group, department, faculty, etc.
    target_name = models.CharField(_('Название целевой группы'), max_length=255, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Период действия объявления
    start_date = models.DateField(_('Дата начала'), default=timezone.now)
    end_date = models.DateField(_('Дата окончания'), null=True, blank=True)
    
    # Важность
    PRIORITY_CHOICES = (
        ('low', _('Низкая')),
        ('normal', _('Обычная')),
        ('high', _('Высокая')),
        ('urgent', _('Срочная')),
    )
    priority = models.CharField(_('Приоритет'), max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Статус
    STATUS_CHOICES = (
        ('draft', _('Черновик')),
        ('published', _('Опубликовано')),
        ('archived', _('В архиве')),
    )
    status = models.CharField(_('Статус'), max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Дополнительные настройки
    send_notification = models.BooleanField(_('Отправить уведомление'), default=True)
    show_on_dashboard = models.BooleanField(_('Показывать на дашборде'), default=True)
    
    # Категории для фильтрации
    category = models.ForeignKey('AnnouncementCategory', on_delete=models.SET_NULL, 
                                null=True, blank=True, 
                                related_name='announcements', 
                                verbose_name=_('Категория'))
    
    class Meta:
        verbose_name = _('объявление')
        verbose_name_plural = _('объявления')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Кэшируем информацию о целевой группе
        if self.target_group:
            self.target_type = self.content_type.model
            self.target_name = str(self.target_group)
        
        # Проверяем, если конец действия не указан, устанавливаем на 30 дней
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Проверяет, активно ли объявление в текущую дату"""
        today = timezone.now().date()
        return (self.status == 'published' and 
                self.start_date <= today and 
                (not self.end_date or self.end_date >= today))


class AnnouncementAttachment(models.Model):
    """
    Модель вложения к объявлению
    """
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, 
                                    related_name='attachments', 
                                    verbose_name=_('Объявление'))
    file = models.FileField(_('Файл'), upload_to='announcement_attachments/')
    filename = models.CharField(_('Имя файла'), max_length=255)
    file_size = models.PositiveIntegerField(_('Размер файла'), default=0)  # В байтах
    content_type = models.CharField(_('Тип содержимого'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('вложение к объявлению')
        verbose_name_plural = _('вложения к объявлениям')
    
    def __str__(self):
        return f"{self.filename} ({self.announcement})"


class AnnouncementCategory(models.Model):
    """
    Модель категории объявлений
    """
    name = models.CharField(_('Название'), max_length=100)
    slug = models.SlugField(_('Идентификатор'), unique=True)
    description = models.TextField(_('Описание'), blank=True)
    icon = models.CharField(_('Иконка'), max_length=50, blank=True)
    color = models.CharField(_('Цвет'), max_length=20, default='#3498db')  # HEX или CSS цвет
    
    class Meta:
        verbose_name = _('категория объявлений')
        verbose_name_plural = _('категории объявлений')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AnnouncementReadStatus(models.Model):
    """
    Модель статуса прочтения объявления
    """
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, 
                                    related_name='read_statuses', 
                                    verbose_name=_('Объявление'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='read_announcements', 
                            verbose_name=_('Пользователь'))
    read_at = models.DateTimeField(_('Время прочтения'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('статус прочтения объявления')
        verbose_name_plural = _('статусы прочтения объявлений')
        unique_together = ('announcement', 'user')
    
    def __str__(self):
        return f"{self.user} прочитал {self.announcement} в {self.read_at}"


# Сигналы для автоматизации
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='accounts.User')
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Создает настройки уведомлений для новых пользователей
    """
    if created:
        NotificationPreference.objects.create(user=instance)

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Создает уведомление о новом сообщении
    """
    if created:
        # Получаем настройки уведомлений получателя
        try:
            preferences = instance.recipient.notification_preferences
            
            # Если уведомления о сообщениях включены
            if preferences.message_notifications:
                Notification.objects.create(
                    user=instance.recipient,
                    notification_type='message',
                    content_type=ContentType.objects.get_for_model(Message),
                    object_id=instance.id,
                    title=_('Новое сообщение'),
                    message=f"{instance.sender.get_full_name()}: {instance.subject}",
                    icon='envelope',
                    link=f"/messages/{instance.id}/",
                )
        except:
            # Если настройки не найдены, создаем уведомление по умолчанию
            Notification.objects.create(
                user=instance.recipient,
                notification_type='message',
                content_type=ContentType.objects.get_for_model(Message),
                object_id=instance.id,
                title=_('Новое сообщение'),
                message=f"{instance.sender.get_full_name()}: {instance.subject}",
                icon='envelope',
                link=f"/messages/{instance.id}/",
            )

# Дополнение к существующим сигналам
@receiver(post_save, sender=ThreadMessage)
def create_thread_message_notification(sender, instance, created, **kwargs):
    """
    Создает уведомления о новом сообщении в цепочке для всех участников, кроме отправителя
    """
    if created:
        # Получаем всех участников цепочки, кроме отправителя
        recipients = instance.thread.participants.exclude(id=instance.sender.id)
        
        # Создаем уведомления для каждого участника
        for recipient in recipients:
            try:
                preferences = recipient.notification_preferences
                
                # Если уведомления о сообщениях включены
                if preferences.message_notifications:
                    Notification.objects.create(
                        user=recipient,
                        notification_type='message',
                        content_type=ContentType.objects.get_for_model(ThreadMessage),
                        object_id=instance.id,
                        title=_('Новое сообщение в цепочке'),
                        message=f"{instance.sender.get_full_name()}: {instance.body[:100]}",
                        icon='comments',
                        link=f"/message-threads/{instance.thread.id}/",
                    )
            except:
                # Если настройки не найдены, создаем уведомление по умолчанию
                Notification.objects.create(
                    user=recipient,
                    notification_type='message',
                    content_type=ContentType.objects.get_for_model(ThreadMessage),
                    object_id=instance.id,
                    title=_('Новое сообщение в цепочке'),
                    message=f"{instance.sender.get_full_name()}: {instance.body[:100]}",
                    icon='comments',
                    link=f"/message-threads/{instance.thread.id}/",
                )

@receiver(post_save, sender=GroupMessage)
def create_group_message_notification(sender, instance, created, **kwargs):
    """
    Создает уведомления о новом групповом сообщении для всех участников группы
    """
    if created and instance.send_notification:
        # Получаем всех пользователей, которым нужно отправить уведомление
        # в зависимости от типа группы-получателя
        users = []
        
        # Определяем пользователей в зависимости от типа получателя
        if instance.content_type.model == 'group':
            # Если получатель - учебная группа
            users = [student.user for student in instance.recipient_group.students.all()]
        elif instance.content_type.model == 'department':
            # Если получатель - кафедра
            users = [teacher.user for teacher in instance.recipient_group.teachers.all()]
            users.extend([methodist.user for methodist in instance.recipient_group.methodists.all()])
            if hasattr(instance.recipient_group, 'heads'):
                users.extend([head.user for head in instance.recipient_group.heads.all()])
        elif instance.content_type.model == 'faculty':
            # Если получатель - факультет
            for department in instance.recipient_group.departments.all():
                users.extend([teacher.user for teacher in department.teachers.all()])
                users.extend([methodist.user for methodist in department.methodists.all()])
            if hasattr(instance.recipient_group, 'deans'):
                users.extend([dean.user for dean in instance.recipient_group.deans.all()])
        
        # Исключаем отправителя
        users = [user for user in users if user.id != instance.sender.id]
        
        # Создаем уведомления для каждого пользователя
        for user in users:
            try:
                preferences = user.notification_preferences
                
                # Если уведомления о сообщениях включены
                if preferences.message_notifications:
                    Notification.objects.create(
                        user=user,
                        notification_type='message',
                        content_type=ContentType.objects.get_for_model(GroupMessage),
                        object_id=instance.id,
                        title=_('Новое групповое сообщение'),
                        message=f"{instance.sender.get_full_name()} для {instance.recipient_name}: {instance.subject}",
                        icon='users',
                        link=f"/group-messages/{instance.id}/",
                        is_important=instance.is_important
                    )
            except:
                # Если настройки не найдены, создаем уведомление по умолчанию
                Notification.objects.create(
                    user=user,
                    notification_type='message',
                    content_type=ContentType.objects.get_for_model(GroupMessage),
                    object_id=instance.id,
                    title=_('Новое групповое сообщение'),
                    message=f"{instance.sender.get_full_name()} для {instance.recipient_name}: {instance.subject}",
                    icon='users',
                    link=f"/group-messages/{instance.id}/",
                    is_important=instance.is_important
                )

@receiver(post_save, sender=Announcement)
def create_announcement_notification(sender, instance, created, **kwargs):
    """
    Создает уведомления о новом объявлении для целевой аудитории
    """
    # Проверяем, нужно ли отправлять уведомление
    if instance.status == 'published' and instance.send_notification:
        # Список пользователей для уведомления
        users = []
        
        if instance.is_public:
            # Если объявление публичное, отправляем всем пользователям
            users = list(User.objects.all())
        elif instance.target_group:
            # Если есть целевая группа, определяем пользователей
            if instance.content_type.model == 'group':
                users = [student.user for student in instance.target_group.students.all()]
            elif instance.content_type.model == 'department':
                users = [teacher.user for teacher in instance.target_group.teachers.all()]
                users.extend([methodist.user for methodist in instance.target_group.methodists.all()])
                if hasattr(instance.target_group, 'heads'):
                    users.extend([head.user for head in instance.target_group.heads.all()])
            elif instance.content_type.model == 'faculty':
                for department in instance.target_group.departments.all():
                    users.extend([teacher.user for teacher in department.teachers.all()])
                    users.extend([methodist.user for methodist in department.methodists.all()])
                if hasattr(instance.target_group, 'deans'):
                    users.extend([dean.user for dean in instance.target_group.deans.all()])
        
        # Создаем уведомления для каждого пользователя
        for user in users:
            try:
                preferences = user.notification_preferences
                
                # Если уведомления о объявлениях включены
                if preferences.announcement_notifications:
                    Notification.objects.create(
                        user=user,
                        notification_type='announcement',
                        content_type=ContentType.objects.get_for_model(Announcement),
                        object_id=instance.id,
                        title=_('Новое объявление'),
                        message=f"{instance.title}",
                        icon='bullhorn',
                        link=f"/announcements/{instance.id}/",
                        is_important=instance.priority in ['high', 'urgent']
                    )
            except:
                # Если настройки не найдены, создаем уведомление по умолчанию
                Notification.objects.create(
                    user=user,
                    notification_type='announcement',
                    content_type=ContentType.objects.get_for_model(Announcement),
                    object_id=instance.id,
                    title=_('Новое объявление'),
                    message=f"{instance.title}",
                    icon='bullhorn',
                    link=f"/announcements/{instance.id}/",
                    is_important=instance.priority in ['high', 'urgent']
                )

# Добавим новые методы для моделей

def mark_as_read_for_user(self, user):
    """
    Отмечает групповое сообщение как прочитанное определенным пользователем
    """
    if not self.read_by.filter(id=user.id).exists():
        GroupMessageReadStatus.objects.create(message=self, user=user)

# Добавляем метод к модели GroupMessage
GroupMessage.mark_as_read_for_user = mark_as_read_for_user

# Аналогично для объявлений
def mark_announcement_as_read(self, user):
    """
    Отмечает объявление как прочитанное определенным пользователем
    """
    if not AnnouncementReadStatus.objects.filter(announcement=self, user=user).exists():
        AnnouncementReadStatus.objects.create(announcement=self, user=user)

# Добавляем метод к модели Announcement
Announcement.mark_as_read = mark_announcement_as_read

# Доработаем метод для модели Notification
def get_unread_count(user):
    """
    Получает количество непрочитанных уведомлений пользователя
    """
    return Notification.objects.filter(user=user, is_read=False).count()

# Добавим статический метод для модели Notification
Notification.get_unread_count = staticmethod(get_unread_count)

# Метод для получения обобщенного количества непрочитанных сообщений
def get_unread_messages_count(user):
    """
    Получает общее количество непрочитанных сообщений пользователя
    """
    # Личные сообщения
    personal_count = Message.objects.filter(recipient=user, is_read=False, is_deleted_by_recipient=False).count()
    
    # Сообщения в цепочках
    thread_ids = user.message_threads.all().values_list('id', flat=True)
    thread_count = ThreadMessage.objects.filter(
        thread_id__in=thread_ids
    ).exclude(
        sender=user
    ).exclude(
        read_by=user
    ).count()
    
    # Групповые сообщения
    group_count = GroupMessage.objects.filter(
        # Сложный фильтр для получения групповых сообщений, предназначенных для групп пользователя
        # Здесь нужно будет доработать логику в зависимости от ролей пользователя
    ).exclude(
        read_by=user
    ).count()
    
    return personal_count + thread_count + group_count

# Добавляем статический метод для модели Message
Message.get_unread_count = staticmethod(get_unread_messages_count)