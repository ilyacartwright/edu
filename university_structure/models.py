from django.db import models
from django.utils.translation import gettext_lazy as _

class Faculty(models.Model):
    """
    Модель факультета
    """
    name = models.CharField(_('Название'), max_length=255)
    short_name = models.CharField(_('Сокращение'), max_length=20)
    code = models.CharField(_('Код'), max_length=20, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    foundation_date = models.DateField(_('Дата основания'), null=True, blank=True)
    is_active = models.BooleanField(_('Активен'), default=True)
    
    class Meta:
        verbose_name = _('факультет')
        verbose_name_plural = _('факультеты')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Department(models.Model):
    """
    Модель кафедры/подразделения
    """
    name = models.CharField(_('Название'), max_length=255)
    short_name = models.CharField(_('Сокращение'), max_length=20)
    code = models.CharField(_('Код'), max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    description = models.TextField(_('Описание'), blank=True)
    foundation_date = models.DateField(_('Дата основания'), null=True, blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    address = models.CharField(_('Адрес'), max_length=255, blank=True)
    room_number = models.CharField(_('Номер аудитории'), max_length=20, blank=True)
    is_active = models.BooleanField(_('Активен'), default=True)
    
    class Meta:
        verbose_name = _('кафедра')
        verbose_name_plural = _('кафедры')
        ordering = ['faculty', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.faculty.short_name})"

class EducationLevel(models.Model):
    """
    Модель уровня образования (бакалавриат, магистратура, аспирантура)
    """
    name = models.CharField(_('Название'), max_length=100)
    code = models.CharField(_('Код'), max_length=20, unique=True)
    study_duration = models.PositiveSmallIntegerField(_('Продолжительность (в годах)'))
    
    class Meta:
        verbose_name = _('уровень образования')
        verbose_name_plural = _('уровни образования')
    
    def __str__(self):
        return self.name

class Specialization(models.Model):
    """
    Модель направления подготовки/специальности
    """
    name = models.CharField(_('Название'), max_length=255)
    code = models.CharField(_('Код'), max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='specializations')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='specializations')
    qualification = models.CharField(_('Квалификация'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активна'), default=True)
    
    class Meta:
        verbose_name = _('направление подготовки')
        verbose_name_plural = _('направления подготовки')
        unique_together = ('code', 'education_level')
    
    def __str__(self):
        return f"{self.code} {self.name} ({self.education_level.name})"
    
class EducationalProfile(models.Model):
    """
    Модель профиля образовательной программы в рамках специальности/направления
    """
    name = models.CharField(_('Название'), max_length=255)
    code = models.CharField(_('Код'), max_length=30, blank=True)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='profiles')
    description = models.TextField(_('Описание'), blank=True)
    
    # Даты действия профиля
    start_year = models.PositiveIntegerField(_('Год начала'), null=True, blank=True)
    end_year = models.PositiveIntegerField(_('Год окончания'), null=True, blank=True)
    
    is_active = models.BooleanField(_('Активен'), default=True)
    
    class Meta:
        verbose_name = _('профиль образовательной программы')
        verbose_name_plural = _('профили образовательных программ')
        unique_together = ('specialization', 'name')
    
    def __str__(self):
        return f"{self.specialization.code} - {self.name}"


class AcademicPlan(models.Model):
    """
    Модель учебного плана
    """
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='academic_plans')
    profile = models.ForeignKey(EducationalProfile, on_delete=models.CASCADE, related_name='academic_plans',
                              null=True, blank=True)  # Профиль может быть необязательным для старых планов
    year = models.CharField(_('Год'), max_length=9)  # Например: "2023-2024"
    approval_date = models.DateField(_('Дата утверждения'))
    version = models.CharField(_('Версия'), max_length=20, default='1.0')
    description = models.TextField(_('Описание'), blank=True)
    file = models.FileField(_('Файл плана'), upload_to='academic_plans/', null=True, blank=True)
    is_active = models.BooleanField(_('Активен'), default=True)
    
    class Meta:
        verbose_name = _('учебный план')
        verbose_name_plural = _('учебные планы')
        unique_together = ('specialization', 'profile', 'year', 'version')
    
    def __str__(self):
        profile_name = f" - {self.profile.name}" if self.profile else ""
        return f"Учебный план {self.specialization.code}{profile_name} ({self.year}, v{self.version})"

class Subject(models.Model):
    """
    Модель учебной дисциплины
    """
    name = models.CharField(_('Название'), max_length=255)
    short_name = models.CharField(_('Сокращение'), max_length=50, blank=True)
    code = models.CharField(_('Код'), max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    description = models.TextField(_('Описание'), blank=True)
    
    SUBJECT_TYPES = (
        ('base', _('Базовая часть')),
        ('variable', _('Вариативная часть')),
        ('elective', _('По выбору')),
        ('faculty', _('Факультативная')),
    )
    subject_type = models.CharField(_('Тип'), max_length=20, choices=SUBJECT_TYPES, default='base')
    
    class Meta:
        verbose_name = _('дисциплина')
        verbose_name_plural = _('дисциплины')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.department.short_name})"

class AcademicPlanSubject(models.Model):
    """
    Модель для связи учебной дисциплины с учебным планом
    и указания нагрузки по семестрам
    """
    academic_plan = models.ForeignKey(AcademicPlan, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='academic_plans')
    semester = models.PositiveSmallIntegerField(_('Семестр'))
    
    # Нагрузка по видам занятий (в часах)
    lectures_hours = models.PositiveSmallIntegerField(_('Лекции'), default=0)
    seminars_hours = models.PositiveSmallIntegerField(_('Семинары'), default=0)
    labs_hours = models.PositiveSmallIntegerField(_('Лабораторные'), default=0)
    practices_hours = models.PositiveSmallIntegerField(_('Практики'), default=0)
    self_study_hours = models.PositiveSmallIntegerField(_('Самостоятельная работа'), default=0)
    
    # Зачетные единицы и форма контроля
    credits = models.PositiveSmallIntegerField(_('Зачетные единицы'))
    
    CONTROL_FORMS = (
        ('exam', _('Экзамен')),
        ('credit', _('Зачет')),
        ('credit_grade', _('Зачет с оценкой')),
        ('coursework', _('Курсовая работа')),
        ('coursework_project', _('Курсовой проект')),
        ('state_exam', _('Государственный экзамен')),
        ('practice', _('Практика')),
        ('vkr_protection', _('Защита ВКР')),
    )
    control_form = models.CharField(_('Форма контроля'), max_length=20, choices=CONTROL_FORMS)
    
    is_optional = models.BooleanField(_('Дисциплина по выбору'), default=False)
    
    class Meta:
        verbose_name = _('дисциплина учебного плана')
        verbose_name_plural = _('дисциплины учебного плана')
        unique_together = ('academic_plan', 'subject', 'semester')
    
    def __str__(self):
        return f"{self.subject.name} - {self.academic_plan} - {self.semester} сем."
    
    @property
    def total_hours(self):
        """Общее количество часов по дисциплине в семестре"""
        return (self.lectures_hours + self.seminars_hours + self.labs_hours + 
                self.practices_hours + self.self_study_hours)

class AcademicYear(models.Model):
    """
    Модель учебного года
    """
    name = models.CharField(_('Название'), max_length=9)  # Например: "2023-2024"
    start_date = models.DateField(_('Дата начала'))
    end_date = models.DateField(_('Дата окончания'))
    is_current = models.BooleanField(_('Текущий'), default=False)
    
    class Meta:
        verbose_name = _('учебный год')
        verbose_name_plural = _('учебные годы')
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name

class Semester(models.Model):
    """
    Модель семестра
    """
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    number = models.PositiveSmallIntegerField(_('Номер семестра'))  # 1, 2, ...
    
    SEMESTER_TYPES = (
        ('autumn', _('Осенний')),
        ('spring', _('Весенний')),
        ('summer', _('Летний')),
    )
    semester_type = models.CharField(_('Тип'), max_length=10, choices=SEMESTER_TYPES)
    
    start_date = models.DateField(_('Дата начала'))
    end_date = models.DateField(_('Дата окончания'))
    
    class_start_date = models.DateField(_('Дата начала занятий'))
    class_end_date = models.DateField(_('Дата окончания занятий'))
    
    exam_start_date = models.DateField(_('Дата начала сессии'))
    exam_end_date = models.DateField(_('Дата окончания сессии'))
    
    is_current = models.BooleanField(_('Текущий'), default=False)
    
    class Meta:
        verbose_name = _('семестр')
        verbose_name_plural = _('семестры')
        unique_together = ('academic_year', 'number')
        ordering = ['-academic_year__start_date', 'number']
    
    def __str__(self):
        return f"{self.number} семестр ({self.academic_year.name})"

class Group(models.Model):
    """
    Модель учебной группы
    """
    name = models.CharField(_('Название'), max_length=50)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='groups')
    profile = models.ForeignKey(EducationalProfile, on_delete=models.SET_NULL, related_name='groups',
                              null=True, blank=True)  # Профиль может быть необязательным
    academic_plan = models.ForeignKey(AcademicPlan, on_delete=models.CASCADE, related_name='groups')
    year_of_admission = models.PositiveIntegerField(_('Год набора'))
    current_semester = models.PositiveSmallIntegerField(_('Текущий семестр'))
    
    EDUCATION_FORMS = (
        ('full_time', _('Очная')),
        ('part_time', _('Заочная')),
        ('evening', _('Вечерняя')),
        ('distance', _('Дистанционная')),
    )
    education_form = models.CharField(_('Форма обучения'), max_length=20, choices=EDUCATION_FORMS)
    
    max_students = models.PositiveSmallIntegerField(_('Максимальное количество студентов'), default=30)
    is_active = models.BooleanField(_('Активна'), default=True)
    curator = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                               related_name='curated_groups', null=True, blank=True)
    
    class Meta:
        verbose_name = _('учебная группа')
        verbose_name_plural = _('учебные группы')
        unique_together = ('name', 'year_of_admission')
    
    def __str__(self):
        profile_info = f" ({self.profile.name})" if self.profile else ""
        return f"{self.name}{profile_info} ({self.year_of_admission}, {self.get_education_form_display()})"

class Subgroup(models.Model):
    """
    Модель подгруппы для проведения занятий
    """
    name = models.CharField(_('Название'), max_length=50)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='subgroups')
    
    SUBGROUP_TYPES = (
        ('general', _('Общая')),
        ('language', _('Языковая')),
        ('lab', _('Лабораторная')),
        ('elective', _('По выбору')),
    )
    subgroup_type = models.CharField(_('Тип'), max_length=20, choices=SUBGROUP_TYPES, default='general')
    
    max_students = models.PositiveSmallIntegerField(_('Максимальное количество студентов'), default=15)
    
    class Meta:
        verbose_name = _('подгруппа')
        verbose_name_plural = _('подгруппы')
        unique_together = ('group', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.group.name})"

class SubgroupStudent(models.Model):
    """
    Модель для связи студентов с подгруппами
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='subgroups')
    subgroup = models.ForeignKey(Subgroup, on_delete=models.CASCADE, related_name='students')
    
    class Meta:
        verbose_name = _('студент подгруппы')
        verbose_name_plural = _('студенты подгрупп')
        unique_together = ('student', 'subgroup')
    
    def __str__(self):
        return f"{self.student} - {self.subgroup}"

class Holiday(models.Model):
    """
    Модель праздничных и выходных дней
    """
    name = models.CharField(_('Название'), max_length=100)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='holidays')
    start_date = models.DateField(_('Дата начала'))
    end_date = models.DateField(_('Дата окончания'))
    
    HOLIDAY_TYPES = (
        ('public', _('Государственный праздник')),
        ('vacation', _('Каникулы')),
        ('university', _('Праздник университета')),
        ('other', _('Другое')),
    )
    holiday_type = models.CharField(_('Тип'), max_length=20, choices=HOLIDAY_TYPES)
    
    class Meta:
        verbose_name = _('праздник/выходной')
        verbose_name_plural = _('праздники/выходные')
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

class Building(models.Model):
    """
    Модель здания университета
    """
    name = models.CharField(_('Название'), max_length=100)
    number = models.CharField(_('Номер'), max_length=10)
    address = models.CharField(_('Адрес'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    floors = models.PositiveSmallIntegerField(_('Количество этажей'), default=1)
    latitude = models.DecimalField(_('Широта'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('Долгота'), max_digits=9, decimal_places=6, null=True, blank=True)
    
    class Meta:
        verbose_name = _('здание')
        verbose_name_plural = _('здания')
    
    def __str__(self):
        return f"{self.name} ({self.number})"

class Room(models.Model):
    """
    Модель аудитории/кабинета
    """
    number = models.CharField(_('Номер'), max_length=20)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    floor = models.PositiveSmallIntegerField(_('Этаж'))
    
    ROOM_TYPES = (
        ('lecture', _('Лекционная')),
        ('seminar', _('Семинарская')),
        ('lab', _('Лаборатория')),
        ('computer', _('Компьютерный класс')),
        ('sports', _('Спортивный зал')),
        ('assembly', _('Актовый зал')),
        ('office', _('Кабинет')),
        ('library', _('Библиотека')),
        ('other', _('Другое')),
    )
    room_type = models.CharField(_('Тип'), max_length=20, choices=ROOM_TYPES)
    
    capacity = models.PositiveSmallIntegerField(_('Вместимость'))
    has_projector = models.BooleanField(_('Проектор'), default=False)
    has_computers = models.BooleanField(_('Компьютеры'), default=False)
    computers_count = models.PositiveSmallIntegerField(_('Количество компьютеров'), default=0)
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активна'), default=True)
    
    class Meta:
        verbose_name = _('аудитория')
        verbose_name_plural = _('аудитории')
        unique_together = ('building', 'number')
    
    def __str__(self):
        return f"{self.number} ({self.building.number})"

class Equipment(models.Model):
    """
    Модель оборудования в аудитории
    """
    name = models.CharField(_('Название'), max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='equipment')
    inventory_number = models.CharField(_('Инвентарный номер'), max_length=50, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    purchase_date = models.DateField(_('Дата приобретения'), null=True, blank=True)
    last_service_date = models.DateField(_('Дата последнего ТО'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('оборудование')
        verbose_name_plural = _('оборудование')
    
    def __str__(self):
        return f"{self.name} ({self.room})"