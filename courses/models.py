from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid
import os


def get_course_icon_path(instance, filename):
    """
    Функция для определения пути сохранения иконки курса
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('course_icons', filename)


def get_course_material_path(instance, filename):
    """
    Функция для определения пути сохранения материалов курса
    """
    course_slug = instance.course_element.course.slug
    element_id = instance.course_element.id
    return os.path.join('course_materials', course_slug, str(element_id), filename)


class Course(models.Model):
    """
    Модель курса
    """
    title = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('Идентификатор URL'), max_length=255, unique=True, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    short_description = models.CharField(_('Краткое описание'), max_length=255, blank=True)
    
    # Иконка и изображение для курса
    icon = models.ImageField(_('Иконка'), upload_to=get_course_icon_path, null=True, blank=True)
    cover_image = models.ImageField(_('Обложка'), upload_to='course_covers/', null=True, blank=True)
    
    # Связь с предметом из учебного плана
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='courses', verbose_name=_('Предмет'))
    academic_plan_subject = models.ForeignKey('university_structure.AcademicPlanSubject', 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True,
                                            related_name='courses', 
                                            verbose_name=_('Предмет учебного плана'))
    
    # Авторы курса
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                             related_name='authored_courses', verbose_name=_('Автор'))
    co_authors = models.ManyToManyField('accounts.User', 
                                      related_name='co_authored_courses', 
                                      blank=True, verbose_name=_('Соавторы'))
    
    # Группы, которым доступен курс
    groups = models.ManyToManyField('university_structure.Group', 
                                  related_name='assigned_courses', 
                                  blank=True, verbose_name=_('Группы'))
    
    # Параметры отображения и доступности
    is_published = models.BooleanField(_('Опубликован'), default=False)
    is_public = models.BooleanField(_('Публичный'), default=False)
    requires_enrollment = models.BooleanField(_('Требуется запись'), default=True)
    
    # Временные рамки
    start_date = models.DateField(_('Дата начала'), null=True, blank=True)
    end_date = models.DateField(_('Дата окончания'), null=True, blank=True)
    
    # Настройки прохождения
    sequential_progression = models.BooleanField(_('Последовательное прохождение'), default=True)
    completion_threshold = models.PositiveSmallIntegerField(
        _('Порог завершения (%)'), 
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Настройки сертификации
    provides_certificate = models.BooleanField(_('Выдает сертификат'), default=False)
    certificate_template = models.FileField(_('Шаблон сертификата'), 
                                          upload_to='certificate_templates/', 
                                          null=True, blank=True)
    
    class Meta:
        verbose_name = _('курс')
        verbose_name_plural = _('курсы')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Генерация slug при создании
        if not self.slug:
            self.slug = slugify(self.title)
            if Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{uuid.uuid4().hex[:8]}"
        
        super().save(*args, **kwargs)
    
    @property
    def completion_rate(self):
        """
        Вычисляет общий процент завершения курса всеми студентами
        """
        enrollments = self.enrollments.all()
        if not enrollments:
            return 0
        
        total_progress = sum(enrollment.progress for enrollment in enrollments)
        return total_progress / enrollments.count()
    
    @property
    def is_active(self):
        """
        Проверяет, активен ли курс в текущую дату
        """
        today = timezone.now().date()
        if not self.is_published:
            return False
        
        if self.start_date and self.start_date > today:
            return False
        
        if self.end_date and self.end_date < today:
            return False
        
        return True


class CourseSection(models.Model):
    """
    Модель раздела курса (для структурирования элементов)
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                              related_name='sections', verbose_name=_('Курс'))
    title = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    
    # Порядок отображения
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    # Доступность
    is_published = models.BooleanField(_('Опубликован'), default=True)
    is_visible = models.BooleanField(_('Видимый для студентов'), default=True)
    
    # Настройки открытия раздела
    unlock_date = models.DateTimeField(_('Дата открытия'), null=True, blank=True)
    requires_previous_section = models.BooleanField(_('Требуется завершение предыдущего раздела'), default=False)
    completion_threshold = models.PositiveSmallIntegerField(
        _('Порог завершения (%)'), 
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        verbose_name = _('раздел курса')
        verbose_name_plural = _('разделы курса')
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def is_available(self):
        """
        Проверяет, доступен ли раздел для просмотра
        """
        if not self.is_published or not self.is_visible:
            return False
        
        now = timezone.now()
        if self.unlock_date and self.unlock_date > now:
            return False
        
        return True


class CourseElementType(models.Model):
    """
    Модель типа элемента курса (лекция, тест, задание, и т.д.)
    """
    name = models.CharField(_('Название'), max_length=100)
    code = models.CharField(_('Код'), max_length=50, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    
    # Иконка
    icon = models.CharField(_('Иконка'), max_length=50, blank=True)
    color = models.CharField(_('Цвет'), max_length=20, default='#3498db')  # HEX или CSS цвет
    
    # Настройки оценивания
    is_gradable = models.BooleanField(_('Оцениваемый'), default=False)
    max_score = models.PositiveSmallIntegerField(_('Максимальный балл'), default=0)
    
    class Meta:
        verbose_name = _('тип элемента курса')
        verbose_name_plural = _('типы элементов курса')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CourseElement(models.Model):
    """
    Модель элемента курса (основной контент)
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                              related_name='elements', verbose_name=_('Курс'))
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, 
                               related_name='elements', verbose_name=_('Раздел'),
                               null=True, blank=True)
    element_type = models.ForeignKey(CourseElementType, on_delete=models.CASCADE, 
                                    related_name='elements', verbose_name=_('Тип элемента'))
    
    title = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    
    # Контент
    content = models.TextField(_('Содержимое'), blank=True)
    content_format = models.CharField(_('Формат содержимого'), max_length=20, 
                                    default='markdown',
                                    choices=[
                                        ('plain', _('Простой текст')),
                                        ('markdown', _('Markdown')),
                                        ('html', _('HTML')),
                                    ])
    
    # Порядок отображения
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    # Время прохождения
    estimated_time = models.PositiveSmallIntegerField(_('Ориентировочное время (мин)'), default=0)
    
    # Доступность
    is_published = models.BooleanField(_('Опубликован'), default=True)
    is_visible = models.BooleanField(_('Видимый для студентов'), default=True)
    
    # Настройки открытия элемента
    unlock_date = models.DateTimeField(_('Дата открытия'), null=True, blank=True)
    is_required = models.BooleanField(_('Обязательный элемент'), default=True)
    requires_previous_element = models.BooleanField(_('Требуется завершение предыдущего элемента'), default=False)
    
    # Связь с расписанием
    scheduled_class = models.ForeignKey('schedule.Class', on_delete=models.SET_NULL, 
                                      related_name='course_elements', 
                                      null=True, blank=True,
                                      verbose_name=_('Связанное занятие'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('элемент курса')
        verbose_name_plural = _('элементы курса')
        ordering = ['course', 'section', 'order']
    
    def __str__(self):
        return f"{self.title} ({self.element_type.name})"
    
    @property
    def is_available(self):
        """
        Проверяет, доступен ли элемент для просмотра
        """
        if not self.is_published or not self.is_visible:
            return False
        
        now = timezone.now()
        if self.unlock_date and self.unlock_date > now:
            return False
        
        # Проверка доступности раздела
        if self.section and not self.section.is_available:
            return False
        
        return True


class CourseElementAttachment(models.Model):
    """
    Модель вложений к элементу курса
    """
    course_element = models.ForeignKey(CourseElement, on_delete=models.CASCADE, 
                                      related_name='attachments', verbose_name=_('Элемент курса'))
    title = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    
    # Файл
    file = models.FileField(_('Файл'), upload_to=get_course_material_path)
    file_size = models.PositiveIntegerField(_('Размер файла'), default=0)  # В байтах
    file_type = models.CharField(_('Тип файла'), max_length=100, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('вложение элемента курса')
        verbose_name_plural = _('вложения элементов курса')
    
    def __str__(self):
        return f"{self.title} ({self.course_element.title})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
            
            file_name = self.file.name.lower()
            if file_name.endswith('.pdf'):
                self.file_type = 'application/pdf'
            elif file_name.endswith(('.doc', '.docx')):
                self.file_type = 'application/msword'
            elif file_name.endswith(('.xls', '.xlsx')):
                self.file_type = 'application/vnd.ms-excel'
            elif file_name.endswith(('.ppt', '.pptx')):
                self.file_type = 'application/vnd.ms-powerpoint'
            elif file_name.endswith('.zip'):
                self.file_type = 'application/zip'
            elif file_name.endswith(('.jpg', '.jpeg')):
                self.file_type = 'image/jpeg'
            elif file_name.endswith('.png'):
                self.file_type = 'image/png'
            elif file_name.endswith('.mp4'):
                self.file_type = 'video/mp4'
            elif file_name.endswith('.mp3'):
                self.file_type = 'audio/mpeg'
            else:
                self.file_type = 'application/octet-stream'
        
        super().save(*args, **kwargs)


class CourseEnrollment(models.Model):
    """
    Модель записи студента на курс
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                              related_name='enrollments', verbose_name=_('Курс'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='course_enrollments', verbose_name=_('Студент'))
    
    # Статус записи
    ENROLLMENT_STATUSES = (
        ('pending', _('Ожидает подтверждения')),
        ('active', _('Активна')),
        ('completed', _('Завершена')),
        ('dropped', _('Отчислен')),
        ('suspended', _('Приостановлена')),
    )
    status = models.CharField(_('Статус записи'), max_length=20, 
                             choices=ENROLLMENT_STATUSES, default='active')
    
    # Прогресс
    progress = models.PositiveSmallIntegerField(_('Прогресс (%)'), default=0, 
                                              validators=[MaxValueValidator(100)])
    last_accessed = models.DateTimeField(_('Последний доступ'), null=True, blank=True)
    
    # Метаданные
    enrolled_at = models.DateTimeField(_('Дата записи'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Дата завершения'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('запись на курс')
        verbose_name_plural = _('записи на курс')
        unique_together = ['course', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.course}"
    
    @property
    def is_completed(self):
        """
        Проверяет, завершен ли курс студентом
        """
        return self.progress >= self.course.completion_threshold
    
    def mark_as_completed(self):
        """
        Отмечает курс как завершенный
        """
        if not self.is_completed:
            self.progress = self.course.completion_threshold
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['progress', 'status', 'completed_at'])


class CourseElementProgress(models.Model):
    """
    Модель прогресса студента по элементу курса
    """
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, 
                                  related_name='element_progress', verbose_name=_('Запись на курс'))
    course_element = models.ForeignKey(CourseElement, on_delete=models.CASCADE, 
                                      related_name='student_progress', verbose_name=_('Элемент курса'))
    
    # Статус элемента
    is_viewed = models.BooleanField(_('Просмотрено'), default=False)
    is_completed = models.BooleanField(_('Завершено'), default=False)
    
    # Даты просмотра и завершения
    first_viewed_at = models.DateTimeField(_('Первый просмотр'), null=True, blank=True)
    last_viewed_at = models.DateTimeField(_('Последний просмотр'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Дата завершения'), null=True, blank=True)
    
    # Время, потраченное на элемент (в секундах)
    time_spent = models.PositiveIntegerField(_('Затраченное время (сек)'), default=0)
    
    # Оценка (если элемент оцениваемый)
    grade = models.DecimalField(_('Оценка'), max_digits=5, decimal_places=2, null=True, blank=True)
    grade_percent = models.PositiveSmallIntegerField(_('Оценка (%)'), null=True, blank=True,
                                                  validators=[MaxValueValidator(100)])
    
    # Метаданные оценки
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='graded_elements', 
                                 null=True, blank=True,
                                 verbose_name=_('Оценил'))
    graded_at = models.DateTimeField(_('Дата оценки'), null=True, blank=True)
    feedback = models.TextField(_('Отзыв/комментарий'), blank=True)
    
    class Meta:
        verbose_name = _('прогресс по элементу курса')
        verbose_name_plural = _('прогресс по элементам курса')
        unique_together = ['enrollment', 'course_element']
    
    def __str__(self):
        return f"{self.enrollment.student} - {self.course_element.title}"
    
    def mark_as_viewed(self):
        """
        Отмечает элемент как просмотренный
        """
        now = timezone.now()
        
        if not self.is_viewed:
            self.is_viewed = True
            self.first_viewed_at = now
        
        self.last_viewed_at = now
        self.save(update_fields=['is_viewed', 'first_viewed_at', 'last_viewed_at'])
    
    def mark_as_completed(self):
        """
        Отмечает элемент как завершенный
        """
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save(update_fields=['is_completed', 'completed_at'])
            
            # Обновляем общий прогресс курса
            self.update_course_progress()
    
    def update_course_progress(self):
        """
        Обновляет общий прогресс курса на основе прогресса по элементам
        """
        enrollment = self.enrollment
        course = enrollment.course
        
        # Получаем все обязательные элементы курса
        required_elements = course.elements.filter(is_required=True).count()
        
        if required_elements > 0:
            # Получаем завершенные обязательные элементы
            completed_elements = CourseElementProgress.objects.filter(
                enrollment=enrollment,
                course_element__course=course,
                course_element__is_required=True,
                is_completed=True
            ).count()
            
            # Вычисляем процент прогресса
            progress = int((completed_elements / required_elements) * 100)
            
            # Обновляем прогресс в записи на курс
            enrollment.progress = progress
            enrollment.last_accessed = timezone.now()
            enrollment.save(update_fields=['progress', 'last_accessed'])
            
            # Проверяем, завершен ли курс
            if progress >= course.completion_threshold and enrollment.status == 'active':
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
                enrollment.save(update_fields=['status', 'completed_at'])


class CourseCertificate(models.Model):
    """
    Модель сертификата о завершении курса
    """
    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE, 
                                     related_name='certificate', verbose_name=_('Запись на курс'))
    certificate_number = models.CharField(_('Номер сертификата'), max_length=50, unique=True)
    issued_at = models.DateTimeField(_('Дата выдачи'), auto_now_add=True)
    
    # Файл сертификата
    certificate_file = models.FileField(_('Файл сертификата'), upload_to='certificates/')
    
    # Дополнительная информация
    expiration_date = models.DateField(_('Дата окончания действия'), null=True, blank=True)
    additional_info = models.TextField(_('Дополнительная информация'), blank=True)
    
    # Подписавшие лица
    signed_by = models.ManyToManyField('accounts.User', 
                                     related_name='signed_certificates', 
                                     blank=True,
                                     verbose_name=_('Подписано'))
    
    class Meta:
        verbose_name = _('сертификат курса')
        verbose_name_plural = _('сертификаты курса')
    
    def __str__(self):
        return f"Сертификат {self.certificate_number} - {self.enrollment.student}"
    
    @property
    def is_valid(self):
        """
        Проверяет, действителен ли сертификат
        """
        if not self.expiration_date:
            return True
        
        return self.expiration_date >= timezone.now().date()


class CourseReview(models.Model):
    """
    Модель отзыва о курсе
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                              related_name='reviews', verbose_name=_('Курс'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='course_reviews', verbose_name=_('Студент'))
    
    # Содержимое отзыва
    rating = models.PositiveSmallIntegerField(_('Оценка'), validators=[MaxValueValidator(5)])
    text = models.TextField(_('Текст отзыва'), blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Статус отзыва
    is_published = models.BooleanField(_('Опубликован'), default=True)
    
    class Meta:
        verbose_name = _('отзыв о курсе')
        verbose_name_plural = _('отзывы о курсе')
        unique_together = ['course', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.course} - {self.rating}/5"


# Основные предопределенные типы элементов курса
PREDEFINED_ELEMENT_TYPES = [
    {
        'name': 'Лекция',
        'code': 'lecture',
        'description': 'Текстовый материал лекции с возможностью форматирования',
        'icon': 'file-text',
        'color': '#3498db',
        'is_gradable': False,
    },
    {
        'name': 'Видео',
        'code': 'video',
        'description': 'Видеоматериал с возможностью встраивания или загрузки',
        'icon': 'video',
        'color': '#e74c3c',
        'is_gradable': False,
    },
    {
        'name': 'Тест',
        'code': 'quiz',
        'description': 'Тестовое задание с автоматической проверкой',
        'icon': 'check-square',
        'color': '#2ecc71',
        'is_gradable': True,
        'max_score': 100,
    },
    {
        'name': 'Задание',
        'code': 'assignment',
        'description': 'Задание с загрузкой файла и ручной проверкой',
        'icon': 'upload',
        'color': '#f39c12',
        'is_gradable': True,
        'max_score': 100,
    },
    {
        'name': 'Опрос',
        'code': 'survey',
        'description': 'Опрос студентов без оценивания',
        'icon': 'list',
        'color': '#9b59b6',
        'is_gradable': False,
    },
    {
        'name': 'Обсуждение',
        'code': 'discussion',
        'description': 'Форум для обсуждения темы',
        'icon': 'message-circle',
        'color': '#1abc9c',
        'is_gradable': False,
    },
    {
        'name': 'Интерактивное упражнение',
        'code': 'interactive',
        'description': 'Интерактивное упражнение с встроенной проверкой',
        'icon': 'zap',
        'color': '#f1c40f',
        'is_gradable': True,
        'max_score': 100,
    },
    {
        'name': 'Вебинар',
        'code': 'webinar',
        'description': 'Запись или анонс онлайн-вебинара',
        'icon': 'video',
        'color': '#34495e',
        'is_gradable': False,
    },
]


# Сигналы для автоматизации работы
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver

@receiver(post_save, sender=Course)
def create_default_section(sender, instance, created, **kwargs):
    """
    Создает раздел по умолчанию при создании курса
    """
    if created:
        CourseSection.objects.create(
            course=instance,
            title=_('Основной раздел'),
            description=_('Основной раздел курса'),
            order=1,
        )

@receiver(post_save, sender=CourseElementProgress)
def update_enrollment_last_accessed(sender, instance, **kwargs):
    """
    Обновляет дату последнего доступа к курсу при просмотре элемента
    """
    if instance.last_viewed_at:
        enrollment = instance.enrollment
        enrollment.last_accessed = instance.last_viewed_at
        enrollment.save(update_fields=['last_accessed'])

@receiver(pre_save, sender=CourseEnrollment)
def check_course_completion(sender, instance, **kwargs):
    """
    Проверяет, завершен ли курс при обновлении прогресса
    """
    if instance.pk:  # Только для существующих объектов
        if instance.progress >= instance.course.completion_threshold and instance.status == 'active':
            instance.status = 'completed'
            instance.completed_at = timezone.now()

@receiver(post_save, sender=CourseEnrollment)
def generate_certificate(sender, instance, **kwargs):
    """
    Автоматически создает сертификат при завершении курса
    """
    if instance.status == 'completed' and instance.course.provides_certificate:
        # Проверяем, существует ли уже сертификат
        if not hasattr(instance, 'certificate'):
            # Создаем сертификат
            certificate_number = f"CERT-{instance.course.id}-{instance.student.id}-{uuid.uuid4().hex[:8]}"
            
            CourseCertificate.objects.create(
                enrollment=instance,
                certificate_number=certificate_number,
                # Здесь должна быть логика генерации файла сертификата
            )