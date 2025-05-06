from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Аутентификация через email
    """
    def authenticate(self, request, username = None, password = None, **kwargs):
        try:
            user = User.objects.get(email=username)
            # Пробуем выполнить поиск по почте
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # если не нашли по почте, пробуем через логин
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        return None
                