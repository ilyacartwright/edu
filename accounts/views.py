from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import User, AdminProfile, TeacherProfile, StudentProfile, MethodistProfile, DeanProfile
from .forms import ProfileEditForm, UserEditForm

@login_required
def profile_view(request):
    """Представление для отображения профиля"""
    user = request.user

    # Определение типа профиля
    profile = None
    if user.role == 'admin' and hasattr(user, 'admin_profile'):
        profile = user.admin_profile
    elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        profile = user.teacher_profile
    elif user.role == 'student' and hasattr(user, 'student_profile'):
        profile = user.student_profile
    elif user.role == 'methodist' and hasattr(user, 'methodist_profile'):
        profile = user.methodist_profile
    elif user.role == 'dean' and hasattr(user, 'dean_profile'):
        profile = user.dean_profile

    return render(request, 'accounts/profile.html', {
        'user': user,
        'profile': profile,
    })


@login_required
def profile_edit_view(request):
    """Представление для редактирования профиля пользователя"""
    user = request.user

    # Определение типа профиля
    profile = None
    if user.role == 'admin' and hasattr(user, 'admin_profile'):
        profile = user.admin_profile
    elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        profile = user.teacher_profile
    elif user.role == 'student' and hasattr(user, 'student_profile'):
        profile = user.student_profile
    elif user.role == 'methodist' and hasattr(user, 'methodist_profile'):
        profile = user.methodist_profile
    elif user.role == 'dean' and hasattr(user, 'dean_profile'):
        profile = user.dean_profile


    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=profile, role=user.role)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Профиль успешно обновлен'))
            return redirect('accounts:profile')
        
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile, role=user.role)

    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })