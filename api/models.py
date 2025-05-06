from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid
import secrets
import datetime


class APIKey(models.Model):
    """
    Модель API-ключа для доступа к API
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name='api_keys', verbose_name=_('Пользователь'))
    
    # Ключ
    key = models.CharField(_('Ключ'), max_length=64, unique=True, editable=False)
    name = models.CharField(_('Название'), max_length=100)
    
    # Параметры доступа
    is_active = models.BooleanField(_('Активен'), default=True)
    
    # Ограничения
    requests_limit = models.PositiveIntegerField(_('Лимит запросов'), default=1000)
    expires_at = models.DateTimeField(_('Истекает'), null=True, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    last_used_at = models.DateTimeField(_('Последнее использование'), null=True, blank=True)
    
    # IP-адреса, с которых разрешен доступ (пустое значение = все адреса)
    allowed_ips = models.TextField(_('Разрешенные IP-адреса'), blank=True,
                                 help_text=_('Список IP-адресов через запятую. Пусто = все адреса.'))
    
    class Meta:
        verbose_name = _('API ключ')
        verbose_name_plural = _('API ключи')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        if not self.key:
            # Генерируем новый ключ при создании
            self.key = secrets.token_hex(32)  # 64 символа в hex-представлении
        super().save(*args, **kwargs)
    
    def is_valid(self, ip_address=None):
        """
        Проверяет, действителен ли ключ
        """
        # Проверяем активность
        if not self.is_active:
            return False
        
        # Проверяем срок действия
        if self.expires_at and self.expires_at < timezone.now():
            return False
        
        # Проверяем IP-адрес
        if ip_address and self.allowed_ips:
            allowed = [ip.strip() for ip in self.allowed_ips.split(',')]
            if ip_address not in allowed:
                return False
        
        return True
    
    def increment_usage(self):
        """
        Обновляет время последнего использования и счетчик использования
        """
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])
        
        # Создаем новую запись об использовании
        APIKeyUsage.objects.create(api_key=self)


class APIKeyPermission(models.Model):
    """
    Модель разрешений для API-ключа
    """
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE,
                               related_name='permissions', verbose_name=_('API ключ'))
    
    # Ресурс, к которому предоставляется доступ
    RESOURCE_CHOICES = (
        ('all', _('Все ресурсы')),
        ('students', _('Студенты')),
        ('teachers', _('Преподаватели')),
        ('courses', _('Курсы')),
        ('grades', _('Оценки')),
        ('attendance', _('Посещаемость')),
        ('schedule', _('Расписание')),
        ('reports', _('Отчеты')),
    )
    resource = models.CharField(_('Ресурс'), max_length=50, choices=RESOURCE_CHOICES)
    
    # Разрешенные действия
    can_read = models.BooleanField(_('Чтение'), default=True)
    can_create = models.BooleanField(_('Создание'), default=False)
    can_update = models.BooleanField(_('Обновление'), default=False)
    can_delete = models.BooleanField(_('Удаление'), default=False)
    
    class Meta:
        verbose_name = _('разрешение API-ключа')
        verbose_name_plural = _('разрешения API-ключа')
        unique_together = ['api_key', 'resource']
    
    def __str__(self):
        permissions = []
        if self.can_read:
            permissions.append('R')
        if self.can_create:
            permissions.append('C')
        if self.can_update:
            permissions.append('U')
        if self.can_delete:
            permissions.append('D')
        
        return f"{self.api_key.name} - {self.resource}: {','.join(permissions)}"


class APIKeyUsage(models.Model):
    """
    Модель для отслеживания использования API-ключа
    """
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE,
                               related_name='usage_logs', verbose_name=_('API ключ'))
    
    # Информация о запросе
    timestamp = models.DateTimeField(_('Время запроса'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    endpoint = models.CharField(_('Конечная точка'), max_length=255, blank=True)
    method = models.CharField(_('Метод'), max_length=10, blank=True)
    
    # Статус запроса
    status_code = models.PositiveSmallIntegerField(_('Код статуса'), null=True, blank=True)
    response_time = models.PositiveIntegerField(_('Время ответа (мс)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('использование API-ключа')
        verbose_name_plural = _('использование API-ключей')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.api_key.name} - {self.timestamp} - {self.endpoint}"


class APIEndpoint(models.Model):
    """
    Модель для документирования конечных точек API
    """
    path = models.CharField(_('Путь'), max_length=255, unique=True)
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'))
    
    # Методы
    METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('OPTIONS', 'OPTIONS'),
        ('HEAD', 'HEAD'),
    )
    allowed_methods = models.CharField(_('Разрешенные методы'), max_length=100,
                                     help_text=_('Методы через запятую, например: GET,POST'))
    
    # Информация о выдаваемых данных
    response_format = models.TextField(_('Формат ответа'), blank=True)
    
    # Ограничения
    rate_limit = models.PositiveIntegerField(_('Ограничение запросов (в час)'), default=100)
    cache_timeout = models.PositiveIntegerField(_('Время кэширования (сек)'), default=0)
    
    # Требования к аутентификации
    requires_authentication = models.BooleanField(_('Требуется аутентификация'), default=True)
    
    # Статус
    is_active = models.BooleanField(_('Активен'), default=True)
    is_deprecated = models.BooleanField(_('Устаревший'), default=False)
    version = models.CharField(_('Версия'), max_length=20, default='v1')
    
    class Meta:
        verbose_name = _('конечная точка API')
        verbose_name_plural = _('конечные точки API')
        ordering = ['path']
    
    def __str__(self):
        return f"{self.path} - {self.name}"
    
    @property
    def methods_list(self):
        """Возвращает список разрешенных методов"""
        return [m.strip() for m in self.allowed_methods.split(',')]


class APIEndpointParameter(models.Model):
    """
    Модель параметра конечной точки API
    """
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE,
                                related_name='parameters', verbose_name=_('Конечная точка'))
    
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'))
    
    # Тип параметра
    PARAM_TYPES = (
        ('path', _('В пути')),
        ('query', _('В запросе')),
        ('body', _('В теле')),
        ('header', _('В заголовке')),
        ('form', _('В форме')),
    )
    param_type = models.CharField(_('Тип параметра'), max_length=20, choices=PARAM_TYPES)
    
    # Тип данных
    DATA_TYPES = (
        ('string', _('Строка')),
        ('integer', _('Целое число')),
        ('boolean', _('Логическое')),
        ('float', _('Число с плавающей точкой')),
        ('array', _('Массив')),
        ('object', _('Объект')),
        ('date', _('Дата')),
        ('datetime', _('Дата и время')),
        ('file', _('Файл')),
    )
    data_type = models.CharField(_('Тип данных'), max_length=20, choices=DATA_TYPES)
    
    # Дополнительные параметры
    is_required = models.BooleanField(_('Обязательный'), default=False)
    default_value = models.CharField(_('Значение по умолчанию'), max_length=255, blank=True)
    example = models.CharField(_('Пример'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('параметр API')
        verbose_name_plural = _('параметры API')
        ordering = ['endpoint', 'name']
        unique_together = ['endpoint', 'name', 'param_type']
    
    def __str__(self):
        return f"{self.endpoint.path} - {self.name} ({self.get_param_type_display()})"


class APIClient(models.Model):
    """
    Модель клиента API (внешнее приложение)
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    
    # Информация о клиенте
    client_id = models.CharField(_('ID клиента'), max_length=64, unique=True, editable=False)
    client_secret = models.CharField(_('Секрет клиента'), max_length=128, blank=True, editable=False)
    
    # Владелец клиента
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='api_clients', verbose_name=_('Владелец'))
    
    # URL для OAuth2
    redirect_uris = models.TextField(_('URL перенаправления'), blank=True,
                                   help_text=_('URL перенаправления через запятую'))
    
    # Настройки
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    # Ограничения
    access_token_lifetime = models.PositiveIntegerField(_('Время жизни токена (мин)'), default=60)
    refresh_token_lifetime = models.PositiveIntegerField(_('Время жизни refresh токена (дни)'), default=30)
    
    # Лого клиента
    logo = models.ImageField(_('Логотип'), upload_to='api_client_logos/', null=True, blank=True)
    
    class Meta:
        verbose_name = _('клиент API')
        verbose_name_plural = _('клиенты API')
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.client_id:
            # Генерируем новый ID клиента при создании
            self.client_id = uuid.uuid4().hex
        
        if not self.client_secret:
            # Генерируем новый секрет клиента при создании
            self.client_secret = secrets.token_urlsafe(64)
        
        super().save(*args, **kwargs)


class APIToken(models.Model):
    """
    Модель токена доступа API
    """
    client = models.ForeignKey(APIClient, on_delete=models.CASCADE,
                              related_name='tokens', verbose_name=_('Клиент API'))
    
    # Информация о пользователе
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name='api_tokens', verbose_name=_('Пользователь'))
    
    # Токены
    access_token = models.CharField(_('Токен доступа'), max_length=255, unique=True)
    refresh_token = models.CharField(_('Refresh токен'), max_length=255, unique=True, null=True, blank=True)
    
    # Время действия
    expires_at = models.DateTimeField(_('Истекает'))
    refresh_expires_at = models.DateTimeField(_('Refresh истекает'), null=True, blank=True)
    
    # Статус
    is_active = models.BooleanField(_('Активен'), default=True)
    
    # Область действия
    scope = models.TextField(_('Область действия'), blank=True,
                           help_text=_('Разрешенные области через пробел'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    last_used_at = models.DateTimeField(_('Последнее использование'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('API токен')
        verbose_name_plural = _('API токены')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Токен {self.user.username} для {self.client.name}"
    
    def save(self, *args, **kwargs):
        if not self.access_token:
            # Генерируем новый токен доступа при создании
            self.access_token = secrets.token_urlsafe(43)  # ~64 символа в base64
        
        if not self.refresh_token and self.client.refresh_token_lifetime > 0:
            # Генерируем новый refresh токен при создании
            self.refresh_token = secrets.token_urlsafe(64)
        
        # Устанавливаем время истечения, если не задано
        if not self.expires_at:
            self.expires_at = timezone.now() + datetime.timedelta(minutes=self.client.access_token_lifetime)
        
        if not self.refresh_expires_at and self.refresh_token:
            self.refresh_expires_at = timezone.now() + datetime.timedelta(days=self.client.refresh_token_lifetime)
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Проверяет, истек ли токен"""
        return self.expires_at < timezone.now()
    
    def revoke(self):
        """Отзывает токен"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def update_usage(self):
        """Обновляет время последнего использования"""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class APITokenUsage(models.Model):
    """
    Модель для отслеживания использования токена
    """
    token = models.ForeignKey(APIToken, on_delete=models.CASCADE,
                             related_name='usage_logs', verbose_name=_('Токен'))
    
    # Информация о запросе
    timestamp = models.DateTimeField(_('Время запроса'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    endpoint = models.CharField(_('Конечная точка'), max_length=255, blank=True)
    method = models.CharField(_('Метод'), max_length=10, blank=True)
    
    # Статус запроса
    status_code = models.PositiveSmallIntegerField(_('Код статуса'), null=True, blank=True)
    response_time = models.PositiveIntegerField(_('Время ответа (мс)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('использование токена')
        verbose_name_plural = _('использование токенов')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.token} - {self.timestamp} - {self.endpoint}"


class WebhookSubscription(models.Model):
    """
    Модель подписки на webhook-уведомления
    """
    client = models.ForeignKey(APIClient, on_delete=models.CASCADE,
                              related_name='webhook_subscriptions', verbose_name=_('Клиент API'))
    
    # URL для отправки уведомлений
    target_url = models.URLField(_('URL назначения'))
    
    # Тип событий
    EVENT_TYPES = (
        ('student.created', _('Создание студента')),
        ('student.updated', _('Обновление студента')),
        ('grade.created', _('Создание оценки')),
        ('grade.updated', _('Обновление оценки')),
        ('attendance.created', _('Создание записи посещаемости')),
        ('attendance.updated', _('Обновление записи посещаемости')),
        ('course.updated', _('Обновление курса')),
        ('schedule.updated', _('Обновление расписания')),
    )
    event_types = models.TextField(_('Типы событий'),
                                 help_text=_('Типы событий через запятую'))
    
    # Секрет для подписи запросов
    secret = models.CharField(_('Секрет'), max_length=128, blank=True)
    
    # Настройки
    is_active = models.BooleanField(_('Активен'), default=True)
    
    # Статистика
    last_delivery_attempt = models.DateTimeField(_('Последняя попытка доставки'), null=True, blank=True)
    successful_deliveries = models.PositiveIntegerField(_('Успешных доставок'), default=0)
    failed_deliveries = models.PositiveIntegerField(_('Неудачных доставок'), default=0)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('webhook-подписка')
        verbose_name_plural = _('webhook-подписки')
        ordering = ['-created_at']
        unique_together = ['client', 'target_url']
    
    def __str__(self):
        return f"{self.client.name} - {self.target_url}"
    
    def save(self, *args, **kwargs):
        if not self.secret:
            # Генерируем новый секрет при создании
            self.secret = secrets.token_urlsafe(32)
        
        super().save(*args, **kwargs)
    
    @property
    def event_types_list(self):
        """Возвращает список типов событий"""
        return [et.strip() for et in self.event_types.split(',')]


class WebhookDelivery(models.Model):
    """
    Модель попытки доставки webhook-уведомления
    """
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.CASCADE,
                                    related_name='deliveries', verbose_name=_('Подписка'))
    
    # Информация о событии
    event_type = models.CharField(_('Тип события'), max_length=50)
    event_id = models.CharField(_('ID события'), max_length=100)
    payload = models.TextField(_('Содержимое запроса'))
    
    # Информация о доставке
    timestamp = models.DateTimeField(_('Время попытки'), auto_now_add=True)
    
    # Статус доставки
    STATUS_CHOICES = (
        ('pending', _('Ожидает отправки')),
        ('delivered', _('Доставлено')),
        ('failed', _('Ошибка доставки')),
        ('retrying', _('Повторная попытка')),
        ('dropped', _('Отброшено')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Информация об ответе
    response_code = models.PositiveSmallIntegerField(_('Код ответа'), null=True, blank=True)
    response_body = models.TextField(_('Тело ответа'), blank=True)
    
    # Дополнительная информация
    attempts = models.PositiveSmallIntegerField(_('Количество попыток'), default=0)
    next_retry = models.DateTimeField(_('Следующая попытка'), null=True, blank=True)
    error_message = models.TextField(_('Сообщение об ошибке'), blank=True)
    
    class Meta:
        verbose_name = _('доставка webhook')
        verbose_name_plural = _('доставки webhook')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.subscription.client.name} - {self.event_type} - {self.status}"


class APIErrorLog(models.Model):
    """
    Модель лога ошибок API
    """
    # Информация о запросе
    timestamp = models.DateTimeField(_('Время'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    endpoint = models.CharField(_('Конечная точка'), max_length=255)
    method = models.CharField(_('Метод'), max_length=10)
    
    # Информация об ошибке
    error_code = models.CharField(_('Код ошибки'), max_length=100)
    error_message = models.TextField(_('Сообщение об ошибке'))
    stack_trace = models.TextField(_('Стек вызовов'), blank=True)
    
    # Связь с пользователем или клиентом
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                            related_name='api_errors', null=True, blank=True,
                            verbose_name=_('Пользователь'))
    client = models.ForeignKey(APIClient, on_delete=models.SET_NULL,
                              related_name='api_errors', null=True, blank=True,
                              verbose_name=_('Клиент API'))
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL,
                               related_name='api_errors', null=True, blank=True,
                               verbose_name=_('API ключ'))
    token = models.ForeignKey(APIToken, on_delete=models.SET_NULL,
                             related_name='api_errors', null=True, blank=True,
                             verbose_name=_('Токен'))
    
    # Дополнительная информация
    request_data = models.TextField(_('Данные запроса'), blank=True)
    response_status = models.PositiveSmallIntegerField(_('Статус ответа'))
    response_data = models.TextField(_('Данные ответа'), blank=True)
    
    class Meta:
        verbose_name = _('лог ошибок API')
        verbose_name_plural = _('логи ошибок API')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.endpoint} - {self.error_code} - {self.timestamp}"