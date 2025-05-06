from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    APIKey,
    APIKeyPermission,
    APIKeyUsage,
    APIEndpoint,
    APIEndpointParameter,
    APIClient,
    APIToken,
    APITokenUsage,
    WebhookSubscription,
    WebhookDelivery,
    APIErrorLog,
)


class APIKeyPermissionInline(admin.TabularInline):
    """
    Встроенная админка для разрешений API-ключа
    """
    model = APIKeyPermission
    extra = 1
    fields = ('resource', 'can_read', 'can_create', 'can_update', 'can_delete')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """
    Админка для API-ключей
    """
    list_display = ('name', 'user', 'get_key_preview', 'is_active', 'requests_limit', 
                  'expires_at', 'created_at', 'get_usage_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username', 'key')
    readonly_fields = ('key', 'created_at', 'last_used_at')
    inlines = [APIKeyPermissionInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'key')
        }),
        (_('Настройки доступа'), {
            'fields': ('is_active', 'requests_limit', 'expires_at')
        }),
        (_('Ограничения IP'), {
            'fields': ('allowed_ips',),
            'description': _('Укажите разрешенные IP-адреса через запятую. Оставьте поле пустым для разрешения всех IP.'),
        }),
        (_('Статистика'), {
            'fields': ('created_at', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_key_preview(self, obj):
        """Возвращает затененный вид ключа"""
        if obj.key:
            visible_part = obj.key[:6]
            return f"{visible_part}...{obj.key[-4:]}"
        return "-"
    get_key_preview.short_description = _('Ключ')
    
    def get_usage_count(self, obj):
        """Получает количество использований ключа"""
        return obj.usage_logs.count()
    get_usage_count.short_description = _('Использований')
    
    def regenerate_key(self, request, queryset):
        """Действие для регенерации ключа"""
        for key in queryset:
            key.key = None  # Установка None вызовет генерацию нового ключа при сохранении
            key.save()
        self.message_user(request, _("Ключи успешно регенерированы"))
    regenerate_key.short_description = _("Регенерировать ключи")
    
    actions = ['regenerate_key']


@admin.register(APIKeyPermission)
class APIKeyPermissionAdmin(admin.ModelAdmin):
    """
    Админка для разрешений API-ключа
    """
    list_display = ('api_key', 'resource', 'can_read', 'can_create', 'can_update', 'can_delete')
    list_filter = ('resource', 'can_read', 'can_create', 'can_update', 'can_delete')
    search_fields = ('api_key__name', 'api_key__user__username')


@admin.register(APIKeyUsage)
class APIKeyUsageAdmin(admin.ModelAdmin):
    """
    Админка для отслеживания использования API-ключа
    """
    list_display = ('api_key', 'timestamp', 'endpoint', 'method', 'status_code', 'ip_address', 'response_time')
    list_filter = ('timestamp', 'method', 'status_code')
    search_fields = ('api_key__name', 'api_key__user__username', 'endpoint', 'ip_address')
    readonly_fields = ('api_key', 'timestamp', 'ip_address', 'user_agent', 'endpoint', 
                     'method', 'status_code', 'response_time')
    
    fieldsets = (
        (None, {
            'fields': ('api_key', 'timestamp')
        }),
        (_('Информация о запросе'), {
            'fields': ('endpoint', 'method', 'ip_address', 'user_agent')
        }),
        (_('Информация об ответе'), {
            'fields': ('status_code', 'response_time')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class APIEndpointParameterInline(admin.TabularInline):
    """
    Встроенная админка для параметров API
    """
    model = APIEndpointParameter
    extra = 1
    fields = ('name', 'param_type', 'data_type', 'is_required', 'default_value', 'example')


@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    """
    Админка для конечных точек API
    """
    list_display = ('path', 'name', 'version', 'allowed_methods', 
                  'requires_authentication', 'is_active', 'is_deprecated', 'get_parameters_count')
    list_filter = ('version', 'requires_authentication', 'is_active', 'is_deprecated')
    search_fields = ('path', 'name', 'description')
    inlines = [APIEndpointParameterInline]
    
    fieldsets = (
        (None, {
            'fields': ('path', 'name', 'description', 'version')
        }),
        (_('Методы и ответы'), {
            'fields': ('allowed_methods', 'response_format')
        }),
        (_('Ограничения'), {
            'fields': ('rate_limit', 'cache_timeout')
        }),
        (_('Настройки доступа'), {
            'fields': ('requires_authentication', 'is_active', 'is_deprecated')
        }),
    )
    
    def get_parameters_count(self, obj):
        """Получает количество параметров эндпоинта"""
        return obj.parameters.count()
    get_parameters_count.short_description = _('Кол-во параметров')


@admin.register(APIEndpointParameter)
class APIEndpointParameterAdmin(admin.ModelAdmin):
    """
    Админка для параметров конечных точек API
    """
    list_display = ('name', 'endpoint', 'param_type', 'data_type', 'is_required')
    list_filter = ('param_type', 'data_type', 'is_required')
    search_fields = ('name', 'description', 'endpoint__path', 'endpoint__name')


@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):
    """
    Админка для клиентов API
    """
    list_display = ('name', 'owner', 'get_client_id_preview', 'is_active', 
                  'created_at', 'get_tokens_count', 'get_webhooks_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'owner__username', 'client_id')
    readonly_fields = ('client_id', 'client_secret', 'created_at')
    # filter_horizontal = ('redirect_uris',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'owner', 'logo')
        }),
        (_('Идентификация'), {
            'fields': ('client_id', 'client_secret')
        }),
        (_('OAuth настройки'), {
            'fields': ('redirect_uris', 'access_token_lifetime', 'refresh_token_lifetime')
        }),
        (_('Статус'), {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    def get_client_id_preview(self, obj):
        """Возвращает затененный вид ID клиента"""
        if obj.client_id:
            visible_part = obj.client_id[:6]
            return f"{visible_part}...{obj.client_id[-4:]}"
        return "-"
    get_client_id_preview.short_description = _('ID клиента')
    
    def get_tokens_count(self, obj):
        """Получает количество токенов клиента"""
        return obj.tokens.count()
    get_tokens_count.short_description = _('Токенов')
    
    def get_webhooks_count(self, obj):
        """Получает количество webhook-подписок клиента"""
        return obj.webhook_subscriptions.count()
    get_webhooks_count.short_description = _('Webhooks')
    
    def regenerate_credentials(self, request, queryset):
        """Действие для регенерации учетных данных клиента"""
        for client in queryset:
            client.client_id = None  # Установка None вызовет генерацию новых данных при сохранении
            client.client_secret = None
            client.save()
        self.message_user(request, _("Учетные данные клиентов успешно регенерированы"))
    regenerate_credentials.short_description = _("Регенерировать учетные данные")
    
    actions = ['regenerate_credentials']


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    """
    Админка для токенов API
    """
    list_display = ('user', 'client', 'get_access_token_preview', 'is_active', 
                  'expires_at', 'created_at', 'scope')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'client__name', 'access_token')
    readonly_fields = ('access_token', 'refresh_token', 'expires_at', 
                     'refresh_expires_at', 'created_at', 'last_used_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'client', 'is_active')
        }),
        (_('Токены'), {
            'fields': ('access_token', 'refresh_token')
        }),
        (_('Сроки действия'), {
            'fields': ('expires_at', 'refresh_expires_at')
        }),
        (_('Дополнительно'), {
            'fields': ('scope', 'created_at', 'last_used_at')
        }),
    )
    
    def get_access_token_preview(self, obj):
        """Возвращает затененный вид токена доступа"""
        if obj.access_token:
            visible_part = obj.access_token[:6]
            return f"{visible_part}...{obj.access_token[-4:]}"
        return "-"
    get_access_token_preview.short_description = _('Токен доступа')
    
    def is_token_valid(self, obj):
        """Проверяет, действителен ли токен"""
        if not obj.is_active:
            return False
        return not obj.is_expired()
    is_token_valid.boolean = True
    is_token_valid.short_description = _('Действителен')
    
    def revoke_tokens(self, request, queryset):
        """Действие для отзыва токенов"""
        for token in queryset:
            token.revoke()
        self.message_user(request, _("Выбранные токены успешно отозваны"))
    revoke_tokens.short_description = _("Отозвать токены")
    
    actions = ['revoke_tokens']


@admin.register(APITokenUsage)
class APITokenUsageAdmin(admin.ModelAdmin):
    """
    Админка для отслеживания использования токенов
    """
    list_display = ('token', 'timestamp', 'endpoint', 'method', 'status_code', 'ip_address', 'response_time')
    list_filter = ('timestamp', 'method', 'status_code')
    search_fields = ('token__user__username', 'token__client__name', 'endpoint', 'ip_address')
    readonly_fields = ('token', 'timestamp', 'ip_address', 'user_agent', 'endpoint', 
                     'method', 'status_code', 'response_time')
    
    fieldsets = (
        (None, {
            'fields': ('token', 'timestamp')
        }),
        (_('Информация о запросе'), {
            'fields': ('endpoint', 'method', 'ip_address', 'user_agent')
        }),
        (_('Информация об ответе'), {
            'fields': ('status_code', 'response_time')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    """
    Админка для webhook-подписок
    """
    list_display = ('target_url', 'client', 'get_event_types', 'is_active', 
                  'successful_deliveries', 'failed_deliveries', 'last_delivery_attempt')
    list_filter = ('is_active', 'created_at')
    search_fields = ('target_url', 'client__name', 'event_types')
    readonly_fields = ('secret', 'successful_deliveries', 'failed_deliveries', 
                     'last_delivery_attempt', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('client', 'target_url', 'is_active')
        }),
        (_('События'), {
            'fields': ('event_types',),
            'description': _('Введите типы событий через запятую (например: student.created,grade.updated)')
        }),
        (_('Безопасность'), {
            'fields': ('secret',)
        }),
        (_('Статистика доставки'), {
            'fields': ('successful_deliveries', 'failed_deliveries', 'last_delivery_attempt')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_event_types(self, obj):
        """Получает список типов событий"""
        types = obj.event_types_list
        if len(types) > 3:
            return f"{', '.join(types[:3])} и еще {len(types) - 3}"
        return ', '.join(types)
    get_event_types.short_description = _('Типы событий')
    
    def regenerate_secret(self, request, queryset):
        """Действие для регенерации секрета webhook"""
        for subscription in queryset:
            subscription.secret = None  # Установка None вызовет генерацию нового секрета при сохранении
            subscription.save()
        self.message_user(request, _("Секреты успешно регенерированы"))
    regenerate_secret.short_description = _("Регенерировать секреты")
    
    actions = ['regenerate_secret']


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    """
    Админка для попыток доставки webhook
    """
    list_display = ('subscription', 'event_type', 'timestamp', 'status', 
                  'response_code', 'attempts', 'next_retry')
    list_filter = ('status', 'event_type', 'timestamp')
    search_fields = ('subscription__target_url', 'subscription__client__name', 
                   'event_type', 'event_id', 'error_message')
    readonly_fields = ('subscription', 'event_type', 'event_id', 'payload', 
                     'timestamp', 'status', 'response_code', 'response_body',
                     'attempts', 'next_retry', 'error_message')
    
    fieldsets = (
        (None, {
            'fields': ('subscription', 'timestamp', 'status')
        }),
        (_('Информация о событии'), {
            'fields': ('event_type', 'event_id')
        }),
        (_('Данные'), {
            'fields': ('payload',)
        }),
        (_('Информация об ответе'), {
            'fields': ('response_code', 'response_body')
        }),
        (_('Повторные попытки'), {
            'fields': ('attempts', 'next_retry', 'error_message')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def retry_deliveries(self, request, queryset):
        """Действие для повторной попытки доставки"""
        for delivery in queryset.filter(status__in=['failed', 'dropped']):
            delivery.status = 'retrying'
            delivery.next_retry = timezone.now()
            delivery.save(update_fields=['status', 'next_retry'])
        self.message_user(request, _("Выбранные доставки отправлены на повторную обработку"))
    retry_deliveries.short_description = _("Повторить доставку")
    
    actions = ['retry_deliveries']


@admin.register(APIErrorLog)
class APIErrorLogAdmin(admin.ModelAdmin):
    """
    Админка для логов ошибок API
    """
    list_display = ('endpoint', 'method', 'error_code', 'response_status', 
                  'timestamp', 'get_user_or_client')
    list_filter = ('response_status', 'error_code', 'method', 'timestamp')
    search_fields = ('endpoint', 'error_message', 'ip_address', 'user__username',
                   'client__name', 'api_key__name')
    readonly_fields = ('timestamp', 'ip_address', 'user_agent', 'endpoint', 'method',
                     'error_code', 'error_message', 'stack_trace', 'user', 'client',
                     'api_key', 'token', 'request_data', 'response_status', 'response_data')
    
    fieldsets = (
        (None, {
            'fields': ('timestamp', 'endpoint', 'method', 'response_status')
        }),
        (_('Информация об ошибке'), {
            'fields': ('error_code', 'error_message', 'stack_trace')
        }),
        (_('Инициатор запроса'), {
            'fields': ('user', 'client', 'api_key', 'token', 'ip_address', 'user_agent')
        }),
        (_('Данные запроса/ответа'), {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_or_client(self, obj):
        """Получает информацию о пользователе или клиенте"""
        if obj.user:
            return f"User: {obj.user.username}"
        elif obj.client:
            return f"Client: {obj.client.name}"
        elif obj.api_key:
            return f"API Key: {obj.api_key.name}"
        elif obj.token:
            return f"Token: {obj.token.user.username} ({obj.token.client.name})"
        return "-"
    get_user_or_client.short_description = _('Пользователь/клиент')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
