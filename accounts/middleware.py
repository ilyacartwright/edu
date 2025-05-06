import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import UserSession

class UserSessionMiddleware(MiddlewareMixin):
    """
    Middleware для отслеживания сессий пользователей
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not is_ajax_request:
                # Получаем или создаем запись о сессии
                session_key = request.session.session_key
                
                # Проверка существующей сессии
                try:
                    session = UserSession.objects.get(
                        session_key=session_key,
                        user=request.user,
                        is_active=True
                    )
                    # Обновляем дату истечения
                    session.expired_at = timezone.now() + timedelta(
                        seconds=settings.SESSION_COOKIE_AGE
                    )
                    session.save(update_fields=['expired_at'])
                except UserSession.DoesNotExist:
                    # Создаем новую запись о сессии
                    ip_address = self.get_client_ip(request)
                    user_agent = request.META.get('HTTP_USER_AGENT', '')
                    
                    UserSession.objects.create(
                        user=request.user,
                        session_key=session_key,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        expired_at=timezone.now() + timedelta(
                            seconds=settings.SESSION_COOKIE_AGE
                        )
                    )
    
    def get_client_ip(self, request):
        """Получает IP-адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip