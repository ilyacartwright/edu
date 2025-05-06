from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class User(AbstractUser):
    """
    Расширенная модель пользователя с дополнительными полями и ролями
    """
    USER_ROLES = (
        ('admin', _('Администратор')),
        ('teacher', _('Преподаватель')),
        ('student', _('Студент')),
        ('methodist', _('Методист')),
        ('dean', _('Декан/Заведующий кафедрой')),
    )
    
    # Переопределяем email чтобы сделать его уникальным и обязательным
    email = models.EmailField(_('Email адрес'), unique=True)
    
    # Дополнительные поля
    patronymic = models.CharField(_('Отчество'), max_length=150, blank=True)
    role = models.CharField(_('Роль'), max_length=20, choices=USER_ROLES)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Номер телефона должен быть в формате: '+999999999'. До 15 цифр разрешено.")
    )
    phone_number = models.CharField(_('Телефон'), validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(_('Дата рождения'), null=True, blank=True)
    profile_picture = models.ImageField(_('Фото профиля'), upload_to='profile_pictures/', null=True, blank=True)
    preferred_language = models.CharField(_('Предпочитаемый язык'), max_length=10, default='ru')
    
    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        """
        Возвращает полное имя пользователя с отчеством, если оно есть
        """
        full_name = f"{self.last_name} {self.first_name}"
        if self.patronymic:
            full_name = f"{full_name} {self.patronymic}"
        return full_name.strip()

class AdminProfile(models.Model):
    """
    Профиль администратора системы
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    position = models.CharField(_('Должность'), max_length=100)
    department = models.ForeignKey('university_structure.Department', on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='admins')
    ACCESS_LEVELS = (
        (1, _('Базовый')),
        (2, _('Расширенный')),
        (3, _('Продвинутый')),
        (4, _('Экспертный')),
        (5, _('Полный')),
    )
    access_level = models.IntegerField(_('Уровень доступа'), choices=ACCESS_LEVELS, default=1)
    responsibility_area = models.CharField(_('Область ответственности'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('профиль администратора')
        verbose_name_plural = _('профили администраторов')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

class TeacherProfile(models.Model):
    """
    Профиль преподавателя
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(_('Табельный номер'), max_length=20, unique=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.CASCADE, 
                                  related_name='teachers')
    
    POSITIONS = (
        ('assistant', _('Ассистент')),
        ('lecturer', _('Преподаватель')),
        ('senior_lecturer', _('Старший преподаватель')),
        ('docent', _('Доцент')),
        ('professor', _('Профессор')),
        ('head_of_department', _('Заведующий кафедрой')),
    )
    position = models.CharField(_('Должность'), max_length=50, choices=POSITIONS)
    
    ACADEMIC_DEGREES = (
        ('none', _('Нет')),
        ('candidate', _('Кандидат наук')),
        ('doctor', _('Доктор наук')),
    )
    academic_degree = models.CharField(_('Ученая степень'), max_length=20, choices=ACADEMIC_DEGREES, default='none')
    
    ACADEMIC_TITLES = (
        ('none', _('Нет')),
        ('docent', _('Доцент')),
        ('professor', _('Профессор')),
    )
    academic_title = models.CharField(_('Ученое звание'), max_length=20, choices=ACADEMIC_TITLES, default='none')
    
    EMPLOYMENT_TYPES = (
        ('full_time', _('Штатный')),
        ('part_time', _('Совместитель')),
        ('contract', _('Договор ГПХ')),
    )
    employment_type = models.CharField(_('Тип занятости'), max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    
    specialization = models.CharField(_('Специализация'), max_length=255, blank=True)
    hire_date = models.DateField(_('Дата приема на работу'))
    office_location = models.CharField(_('Местоположение кабинета'), max_length=100, blank=True)
    office_hours = models.TextField(_('Часы консультаций'), blank=True)
    bio = models.TextField(_('Биография'), blank=True)
    
    class Meta:
        verbose_name = _('профиль преподавателя')
        verbose_name_plural = _('профили преподавателей')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_position_display()}"

class TeacherSubject(models.Model):
    """
    Связь преподавателя с предметами по семестрам
    """
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='teaching_subjects')
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, related_name='teachers')
    academic_year = models.CharField(_('Учебный год'), max_length=9)  # Например: "2023-2024"
    semester = models.IntegerField(_('Семестр'))
    
    ROLES = (
        ('lecturer', _('Лектор')),
        ('seminar', _('Ведущий семинаров')),
        ('lab', _('Ведущий лабораторных')),
        ('practice', _('Ведущий практик')),
        ('all', _('Все виды занятий')),
    )
    role = models.CharField(_('Роль'), max_length=20, choices=ROLES)
    
    class Meta:
        verbose_name = _('назначение преподавателя')
        verbose_name_plural = _('назначения преподавателей')
        unique_together = ('teacher', 'subject', 'academic_year', 'semester', 'role')
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.subject.name} ({self.academic_year}, {self.semester} сем.)"

class StudentProfile(models.Model):
    """
    Профиль студента
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(_('Номер студенческого'), max_length=20, unique=True)
    group = models.ForeignKey('university_structure.Group', on_delete=models.CASCADE, related_name='students')
    enrollment_year = models.IntegerField(_('Год поступления'))
    
    EDUCATION_FORMS = (
        ('full_time', _('Очная')),
        ('part_time', _('Заочная')),
        ('evening', _('Вечерняя')),
        ('distance', _('Дистанционная')),
    )
    education_form = models.CharField(_('Форма обучения'), max_length=20, choices=EDUCATION_FORMS)
    
    EDUCATION_BASIS = (
        ('budget', _('Бюджет')),
        ('contract', _('Контракт')),
        ('targeted', _('Целевое обучение')),
    )
    education_basis = models.CharField(_('Основа обучения'), max_length=20, choices=EDUCATION_BASIS)
    
    current_semester = models.IntegerField(_('Текущий семестр'))
    
    ACADEMIC_STATUSES = (
        ('active', _('Учится')),
        ('academic_leave', _('Академический отпуск')),
        ('expelled', _('Отчислен')),
        ('graduated', _('Выпускник')),
        ('sabbatical', _('Академический отпуск')),
    )
    academic_status = models.CharField(_('Академический статус'), max_length=20, choices=ACADEMIC_STATUSES, default='active')
    
    SCHOLARSHIP_STATUSES = (
        ('none', _('Нет')),
        ('regular', _('Обычная')),
        ('elevated', _('Повышенная')),
        ('special', _('Именная')),
    )
    scholarship_status = models.CharField(_('Статус стипендии'), max_length=20, choices=SCHOLARSHIP_STATUSES, default='none')
    
    has_dormitory = models.BooleanField(_('Проживает в общежитии'), default=False)
    personal_info = models.TextField(_('Дополнительная информация'), blank=True)
    
    class Meta:
        verbose_name = _('профиль студента')
        verbose_name_plural = _('профили студентов')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.group.name} - {self.student_id}"

class MethodistProfile(models.Model):
    """
    Профиль методиста кафедры/деканата
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='methodist_profile')
    employee_id = models.CharField(_('Табельный номер'), max_length=20, unique=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.CASCADE, 
                                  related_name='methodists')
    responsibilities = models.TextField(_('Обязанности'))
    managed_specializations = models.ManyToManyField('university_structure.Specialization', 
                                                   related_name='methodists', blank=True)
    managed_groups = models.ManyToManyField('university_structure.Group', related_name='methodists', blank=True)
    
    class Meta:
        verbose_name = _('профиль методиста')
        verbose_name_plural = _('профили методистов')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - методист {self.department.name}"

class DeanProfile(models.Model):
    """
    Профиль декана/заведующего кафедрой
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dean_profile')
    employee_id = models.CharField(_('Табельный номер'), max_length=20, unique=True)
    faculty = models.ForeignKey('university_structure.Faculty', on_delete=models.CASCADE, 
                               related_name='deans', null=True, blank=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.CASCADE, 
                                  related_name='heads', null=True, blank=True)
    
    POSITIONS = (
        ('dean', _('Декан')),
        ('vice_dean', _('Заместитель декана')),
        ('head_of_department', _('Заведующий кафедрой')),
    )
    position = models.CharField(_('Должность'), max_length=20, choices=POSITIONS)
    
    ACADEMIC_DEGREES = (
        ('none', _('Нет')),
        ('candidate', _('Кандидат наук')),
        ('doctor', _('Доктор наук')),
    )
    academic_degree = models.CharField(_('Ученая степень'), max_length=20, choices=ACADEMIC_DEGREES)
    
    ACADEMIC_TITLES = (
        ('none', _('Нет')),
        ('docent', _('Доцент')),
        ('professor', _('Профессор')),
    )
    academic_title = models.CharField(_('Ученое звание'), max_length=20, choices=ACADEMIC_TITLES)
    
    appointment_date = models.DateField(_('Дата назначения'))
    term_end_date = models.DateField(_('Дата окончания срока'), null=True, blank=True)
    has_teaching_duties = models.BooleanField(_('Ведет преподавательскую деятельность'), default=True)
    
    class Meta:
        verbose_name = _('профиль декана/заведующего')
        verbose_name_plural = _('профили деканов/заведующих')
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(position='dean', faculty__isnull=False) |
                    models.Q(position='vice_dean', faculty__isnull=False) |
                    models.Q(position='head_of_department', department__isnull=False)
                ),
                name='position_matches_entity'
            )
        ]
    
    def __str__(self):
        if self.position in ['dean', 'vice_dean']:
            entity = self.faculty.name
        else:
            entity = self.department.name
        return f"{self.user.get_full_name()} - {self.get_position_display()} ({entity})"

class UserSession(models.Model):
    """
    Модель для отслеживания сессий пользователей
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(_('Ключ сессии'), max_length=40)
    ip_address = models.GenericIPAddressField(_('IP адрес'))
    user_agent = models.TextField(_('User Agent'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    expired_at = models.DateTimeField(_('Дата истечения'))
    is_active = models.BooleanField(_('Активна'), default=True)
    
    class Meta:
        verbose_name = _('сессия пользователя')
        verbose_name_plural = _('сессии пользователей')
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

class UserNotificationSetting(models.Model):
    """
    Настройки уведомлений пользователя
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    email_notifications = models.BooleanField(_('Email уведомления'), default=True)
    sms_notifications = models.BooleanField(_('SMS уведомления'), default=False)
    web_notifications = models.BooleanField(_('Веб уведомления'), default=True)
    grades_notification = models.BooleanField(_('Уведомления об оценках'), default=True)
    schedule_changes = models.BooleanField(_('Изменения расписания'), default=True)
    course_updates = models.BooleanField(_('Обновления курсов'), default=True)
    system_messages = models.BooleanField(_('Системные сообщения'), default=True)
    
    class Meta:
        verbose_name = _('настройка уведомлений')
        verbose_name_plural = _('настройки уведомлений')
    
    def __str__(self):
        return f"Настройки уведомлений - {self.user.username}"

# Сигналы для автоматического создания профилей и настроек при создании пользователя
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Создает соответствующий профиль при создании пользователя
    """
    if created:
        # Создание профиля в зависимости от роли
        if instance.role == 'admin':
            AdminProfile.objects.create(user=instance)
        elif instance.role == 'teacher':
            TeacherProfile.objects.create(user=instance)
        elif instance.role == 'student':
            StudentProfile.objects.create(user=instance)
        elif instance.role == 'methodist':
            MethodistProfile.objects.create(user=instance)
        elif instance.role == 'dean':
            DeanProfile.objects.create(user=instance)
        
        # Создание настроек уведомлений
        UserNotificationSetting.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Сохраняет соответствующий профиль при обновлении пользователя
    """
    if instance.role == 'admin' and hasattr(instance, 'admin_profile'):
        instance.admin_profile.save()
    elif instance.role == 'teacher' and hasattr(instance, 'teacher_profile'):
        instance.teacher_profile.save()
    elif instance.role == 'student' and hasattr(instance, 'student_profile'):
        instance.student_profile.save()
    elif instance.role == 'methodist' and hasattr(instance, 'methodist_profile'):
        instance.methodist_profile.save()
    elif instance.role == 'dean' and hasattr(instance, 'dean_profile'):
        instance.dean_profile.save()
    
    if hasattr(instance, 'notification_settings'):
        instance.notification_settings.save()