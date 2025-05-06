from rest_framework import permissions

class IsAdminOrSelf(permissions.BasePermission):
    """
    Разрешение для доступа к данным пользователя:
    - Администраторы могут редактировать любого пользователя
    - Обычные пользователи могут редактировать только свои данные
    """
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Администраторы могут редактировать любого пользователя
        if request.user.is_staff or request.user.role == 'admin':
            return True
        
        # Пользователи могут редактировать только свои данные
        return obj == request.user

class IsAdminOrTeacher(permissions.BasePermission):
    """
    Разрешение для доступа к данным:
    - Администраторы могут выполнять любые действия
    - Преподаватели могут просматривать
    """
    def has_permission(self, request, view):
        # Только аутентифицированные пользователи
        if not request.user.is_authenticated:
            return False
        
        # Чтение разрешено преподавателям и администраторам
        if request.method in permissions.SAFE_METHODS:
            return request.user.role in ['admin', 'teacher', 'dean']
        
        # Изменения разрешены только администраторам
        return request.user.role == 'admin' or request.user.is_staff

class IsUserRoleMatch(permissions.BasePermission):
    """
    Разрешение для доступа в зависимости от роли пользователя
    """
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles or []
    
    def has_permission(self, request, view):
        # Только аутентифицированные пользователи
        if not request.user.is_authenticated:
            return False
        
        # Администраторы могут выполнять любые действия
        if request.user.is_staff or request.user.role == 'admin':
            return True
        
        # Проверка роли пользователя
        return request.user.role in self.allowed_roles