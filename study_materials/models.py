from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
import uuid
import os


def get_material_file_path(instance, filename):
    """
    Функция для определения пути к файлу учебного материала
    Сохраняет в структуре: materials/subject_code/type/filename
    """
    subject_code = instance.subject.code if instance.subject else 'common'
    material_type = instance.get_material_type_display().lower()
    # Добавляем уникальный идентификатор к имени файла для избежания коллизий
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    return f'materials/{subject_code}/{material_type}/{unique_filename}'


class MaterialCategory(models.Model):
    """
    Модель категории учебных материалов
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='subcategories', verbose_name=_('Родительская категория'))
    
    class Meta:
        verbose_name = _('категория материалов')
        verbose_name_plural = _('категории материалов')
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name


class Material(models.Model):
    """
    Модель учебного материала
    """
    title = models.CharField(_('Заголовок'), max_length=255)
    slug = models.SlugField(_('URL-идентификатор'), max_length=255, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    
    # Привязка к учебному процессу
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='materials', verbose_name=_('Предмет'))
    academic_plan_subject = models.ForeignKey('university_structure.AcademicPlanSubject', 
                                            on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='materials', verbose_name=_('Предмет учебного плана'))
    
    # Категория и тип материала
    category = models.ForeignKey(MaterialCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='materials', verbose_name=_('Категория'))
    
    MATERIAL_TYPES = (
        ('lecture', _('Лекция')),
        ('practice', _('Практическое занятие')),
        ('lab', _('Лабораторная работа')),
        ('seminar', _('Семинар')),
        ('textbook', _('Учебник')),
        ('manual', _('Методическое пособие')),
        ('article', _('Статья')),
        ('video', _('Видео')),
        ('presentation', _('Презентация')),
        ('test', _('Тест/Контрольная работа')),
        ('exam', _('Экзаменационные материалы')),
        ('literature', _('Литература')),
        ('other', _('Другое')),
    )
    material_type = models.CharField(_('Тип материала'), max_length=20, choices=MATERIAL_TYPES)
    
    # Основное содержимое
    content = models.TextField(_('Текстовое содержимое'), blank=True)
    
    # Файл материала
    file = models.FileField(_('Файл'), upload_to=get_material_file_path, null=True, blank=True)
    file_size = models.PositiveIntegerField(_('Размер файла (байт)'), null=True, blank=True)
    file_type = models.CharField(_('Тип файла'), max_length=100, blank=True)
    
    # Внешняя ссылка
    external_url = models.URLField(_('Внешняя ссылка'), blank=True)
    
    # Связи с курсами, группами и т.д.
    groups = models.ManyToManyField('university_structure.Group', blank=True,
                                  related_name='available_materials', verbose_name=_('Группы'))
    courses = models.ManyToManyField('courses.Course', blank=True,
                                   related_name='materials', verbose_name=_('Курсы'))
    
    # Права доступа
    ACCESS_LEVELS = (
        ('public', _('Публичный')),
        ('university', _('Для всего университета')),
        ('faculty', _('Для факультета')),
        ('department', _('Для кафедры')),
        ('group', _('Для групп')),
        ('course', _('Для курса')),
        ('private', _('Приватный')),
    )
    access_level = models.CharField(_('Уровень доступа'), max_length=20, choices=ACCESS_LEVELS, default='group')
    
    # Метаданные
    author = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='created_materials', verbose_name=_('Автор'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Тэги
    tags = models.ManyToManyField('MaterialTag', blank=True, related_name='materials', verbose_name=_('Теги'))
    
    # Флаги
    is_published = models.BooleanField(_('Опубликован'), default=True)
    is_featured = models.BooleanField(_('Рекомендуемый'), default=False)
    
    class Meta:
        verbose_name = _('учебный материал')
        verbose_name_plural = _('учебные материалы')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_material_type_display()})"
    
    def save(self, *args, **kwargs):
        # Генерируем slug если его нет
        if not self.slug:
            self.slug = slugify(self.title)
            if Material.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{uuid.uuid4().hex[:8]}"
        
        # Определяем размер и тип файла при его наличии
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


class MaterialTag(models.Model):
    """
    Модель тега для материалов
    """
    name = models.CharField(_('Название'), max_length=50, unique=True)
    slug = models.SlugField(_('URL-идентификатор'), max_length=50, unique=True, blank=True)
    
    class Meta:
        verbose_name = _('тег материала')
        verbose_name_plural = _('теги материалов')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MaterialAttachment(models.Model):
    """
    Модель для дополнительных вложений к материалу
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, 
                                related_name='attachments', verbose_name=_('Материал'))
    title = models.CharField(_('Заголовок'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    file = models.FileField(_('Файл'), upload_to='material_attachments/')
    file_size = models.PositiveIntegerField(_('Размер файла (байт)'), null=True, blank=True)
    file_type = models.CharField(_('Тип файла'), max_length=100, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('вложение к материалу')
        verbose_name_plural = _('вложения к материалам')
    
    def __str__(self):
        return f"{self.title} ({self.material.title})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
            
            file_name = self.file.name.lower()
            if file_name.endswith('.pdf'):
                self.file_type = 'application/pdf'
            elif file_name.endswith(('.doc', '.docx')):
                self.file_type = 'application/msword'
            # ... (аналогично как в модели Material)
        
        super().save(*args, **kwargs)


class MaterialDownload(models.Model):
    """
    Модель для отслеживания скачиваний материалов
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, 
                                related_name='downloads', verbose_name=_('Материал'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='material_downloads', verbose_name=_('Пользователь'))
    downloaded_at = models.DateTimeField(_('Дата скачивания'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    
    class Meta:
        verbose_name = _('скачивание материала')
        verbose_name_plural = _('скачивания материалов')
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"{self.material.title} - {self.user.username} ({self.downloaded_at})"


class MaterialView(models.Model):
    """
    Модель для отслеживания просмотров материалов
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, 
                                related_name='views', verbose_name=_('Материал'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='material_views', verbose_name=_('Пользователь'))
    viewed_at = models.DateTimeField(_('Дата просмотра'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('просмотр материала')
        verbose_name_plural = _('просмотры материалов')
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.material.title} - {self.user.username} ({self.viewed_at})"


class MaterialFavorite(models.Model):
    """
    Модель для избранных материалов пользователя
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, 
                                related_name='favorites', verbose_name=_('Материал'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='favorite_materials', verbose_name=_('Пользователь'))
    added_at = models.DateTimeField(_('Дата добавления'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('избранный материал')
        verbose_name_plural = _('избранные материалы')
        unique_together = ('material', 'user')
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.material.title} - {self.user.username}"


class MaterialComment(models.Model):
    """
    Модель комментария к материалу
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, 
                                related_name='comments', verbose_name=_('Материал'))
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                              related_name='material_comments', verbose_name=_('Автор'))
    text = models.TextField(_('Текст комментария'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    is_approved = models.BooleanField(_('Одобрен'), default=True)
    
    # Для иерархических комментариев
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='replies', verbose_name=_('Родительский комментарий'))
    
    class Meta:
        verbose_name = _('комментарий к материалу')
        verbose_name_plural = _('комментарии к материалам')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Комментарий от {self.author.username} к {self.material.title}"


class MaterialRating(models.Model):
    """
    Модель оценки материала пользователем
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE, 
                                related_name='ratings', verbose_name=_('Материал'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='material_ratings', verbose_name=_('Пользователь'))
    rating = models.PositiveSmallIntegerField(_('Оценка'), choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(_('Комментарий'), blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('оценка материала')
        verbose_name_plural = _('оценки материалов')
        unique_together = ('material', 'user')
    
    def __str__(self):
        return f"{self.material.title} - {self.user.username}: {self.rating}"


class Literature(models.Model):
    """
    Модель литературы для учебного процесса
    """
    title = models.CharField(_('Название'), max_length=255)
    authors = models.CharField(_('Авторы'), max_length=255)
    publication_year = models.PositiveSmallIntegerField(_('Год публикации'), null=True, blank=True)
    publisher = models.CharField(_('Издательство'), max_length=100, blank=True)
    isbn = models.CharField(_('ISBN'), max_length=20, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    
    # Тип литературы
    LITERATURE_TYPES = (
        ('textbook', _('Учебник')),
        ('manual', _('Учебное пособие')),
        ('monograph', _('Монография')),
        ('article', _('Статья')),
        ('reference', _('Справочник')),
        ('periodical', _('Периодическое издание')),
        ('other', _('Другое')),
    )
    literature_type = models.CharField(_('Тип литературы'), max_length=20, choices=LITERATURE_TYPES)
    
    # Привязка к учебному процессу
    subjects = models.ManyToManyField('university_structure.Subject', blank=True,
                                     related_name='literature', verbose_name=_('Дисциплины'))
    
    # Файл электронной версии
    file = models.FileField(_('Файл'), upload_to='literature/', null=True, blank=True)
    file_size = models.PositiveIntegerField(_('Размер файла (байт)'), null=True, blank=True)
    
    # Внешняя ссылка
    external_url = models.URLField(_('Внешняя ссылка'), blank=True)
    
    # Степень доступности
    AVAILABILITY_CHOICES = (
        ('available', _('В наличии')),
        ('limited', _('Ограниченное количество')),
        ('unavailable', _('Отсутствует')),
        ('electronic', _('Только электронная версия')),
    )
    availability = models.CharField(_('Доступность'), max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    
    # Количество экземпляров и местонахождение
    copies_available = models.PositiveSmallIntegerField(_('Доступных экземпляров'), default=0)
    location = models.CharField(_('Местонахождение'), max_length=100, blank=True)
    
    # Метаданные
    added_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='added_literature', verbose_name=_('Добавил'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('литература')
        verbose_name_plural = _('литература')
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} ({self.authors})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ElectronicLibrarySystem(models.Model):
    """
    Модель внешней электронной библиотечной системы (ЭБС)
    """
    name = models.CharField(_('Название'), max_length=100)
    url = models.URLField(_('URL системы'))
    description = models.TextField(_('Описание'), blank=True)
    logo = models.ImageField(_('Логотип'), upload_to='elib_logos/', null=True, blank=True)
    
    # Информация о доступе
    is_active = models.BooleanField(_('Активна'), default=True)
    subscription_start = models.DateField(_('Начало подписки'), null=True, blank=True)
    subscription_end = models.DateField(_('Окончание подписки'), null=True, blank=True)
    
    # Инструкции по авторизации
    access_instructions = models.TextField(_('Инструкции по доступу'), blank=True)
    
    class Meta:
        verbose_name = _('электронная библиотечная система')
        verbose_name_plural = _('электронные библиотечные системы')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def is_subscription_valid(self):
        """Проверяет, действует ли подписка на данный момент"""
        if not self.subscription_start or not self.subscription_end:
            return False
        return self.subscription_start <= timezone.now().date() <= self.subscription_end