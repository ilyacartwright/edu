from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    """Декоратор для проверки роли пользователя"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator

def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """Декоратор для представлений, требующих роль администратора"""
    articul_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'admin',
        login_url=login_url,
        redirect_field_name=redirect_field_name   
    )
    if function:
        return articul_decorator(function)
    return articul_decorator

def teacher_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """Декоратор для представлений, требующих роль преподавателя"""
    articul_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'teacher',
        login_url=login_url,
        redirect_field_name=redirect_field_name   
    )
    if function:
        return articul_decorator(function)
    return articul_decorator

def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """Декоратор для представлений, требующих роль студента"""
    articul_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'student',
        login_url=login_url,
        redirect_field_name=redirect_field_name   
    )
    if function:
        return articul_decorator(function)
    return articul_decorator

def methodist_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """Декоратор для представлений, требующих роль методиста"""
    articul_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'methodist',
        login_url=login_url,
        redirect_field_name=redirect_field_name   
    )
    if function:
        return articul_decorator(function)
    return articul_decorator

def dean_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """Декоратор для представлений, требующих роль декана/заведующего кафедрой"""
    articul_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'dean',
        login_url=login_url,
        redirect_field_name=redirect_field_name   
    )
    if function:
        return articul_decorator(function)
    return articul_decorator

