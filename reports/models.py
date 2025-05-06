from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
import os


def get_report_file_path(instance, filename):
    """
    Функция для определения пути к файлу отчета
    Сохраняет в структуре: reports/report_type/YYYY-MM/filename
    """
    # Получаем текущую дату для организации файлов по папкам
    today = timezone.now()
    date_path = today.strftime('%Y-%m')
    
    # Добавляем уникальный идентификатор к имени файла для избежания коллизий
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    
    return f'reports/{instance.report_type}/{date_path}/{unique_filename}'


class ReportTemplate(models.Model):
    """
    Модель шаблона отчета
    """
    name = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    
    REPORT_TYPES = (
        ('academic_performance', _('Успеваемость')),
        ('attendance', _('Посещаемость')),
        ('workload', _('Нагрузка преподавателей')),
        ('grade_sheet', _('Ведомость')),
        ('transcript', _('Зачетная книжка')),
        ('schedule', _('Расписание')),
        ('contingent', _('Контингент студентов')),
        ('custom', _('Пользовательский отчет')),
    )
    report_type = models.CharField(_('Тип отчета'), max_length=30, choices=REPORT_TYPES)
    
    # Шаблон для генерации отчета
    template_file = models.FileField(_('Файл шаблона'), upload_to='report_templates/')
    
    # Параметры шаблона
    parameters_schema = models.JSONField(_('Схема параметров'), default=dict)
    
    # Доступность шаблона для разных ролей
    ROLE_CHOICES = (
        ('admin', _('Администратор')),
        ('dean', _('Декан/Зав. кафедрой')),
        ('teacher', _('Преподаватель')),
        ('methodist', _('Методист')),
        ('student', _('Студент')),
    )
    available_for = models.JSONField(_('Доступен для ролей'), default=list)
    
    # Метаданные
    is_active = models.BooleanField(_('Активен'), default=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='created_report_templates', 
                                  null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('шаблон отчета')
        verbose_name_plural = _('шаблоны отчетов')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class Report(models.Model):
    """
    Модель сгенерированного отчета
    """
    # Базовая информация
    title = models.CharField(_('Название'), max_length=255)
    template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, 
                                related_name='generated_reports', 
                                null=True, blank=True)
    
    # Тип отчета (если нет шаблона)
    REPORT_TYPES = (
        ('academic_performance', _('Успеваемость')),
        ('attendance', _('Посещаемость')),
        ('workload', _('Нагрузка преподавателей')),
        ('grade_sheet', _('Ведомость')),
        ('transcript', _('Зачетная книжка')),
        ('schedule', _('Расписание')),
        ('contingent', _('Контингент студентов')),
        ('custom', _('Пользовательский отчет')),
    )
    report_type = models.CharField(_('Тип отчета'), max_length=30, choices=REPORT_TYPES)
    
    # Параметры отчета
    parameters = models.JSONField(_('Параметры'), default=dict)
    
    # Результат генерации
    file = models.FileField(_('Файл отчета'), upload_to=get_report_file_path, null=True, blank=True)
    content = models.TextField(_('Содержимое (HTML)'), blank=True)
    
    # Период отчета
    period_start = models.DateField(_('Начало периода'), null=True, blank=True)
    period_end = models.DateField(_('Конец периода'), null=True, blank=True)
    
    # Связь с семестром
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.SET_NULL, 
                                related_name='reports', null=True, blank=True)
    
    # Генерик-связь с объектом отчета (группа, студент, преподаватель и т.д.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                    null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Статус отчета
    STATUS_CHOICES = (
        ('generating', _('Генерируется')),
        ('completed', _('Завершен')),
        ('failed', _('Ошибка')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='generating')
    error_message = models.TextField(_('Сообщение об ошибке'), blank=True)
    
    # Метаданные
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='generated_reports', 
                                  null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    # Настройки доступа
    is_public = models.BooleanField(_('Публичный'), default=False)
    access_code = models.CharField(_('Код доступа'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('отчет')
        verbose_name_plural = _('отчеты')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%d.%m.%Y')})"
    
    def save(self, *args, **kwargs):
        # Генерируем код доступа при создании отчета
        if not self.id and not self.access_code:
            self.access_code = str(uuid.uuid4().hex)[:10].upper()
        super().save(*args, **kwargs)


class ReportAccess(models.Model):
    """
    Модель для отслеживания доступа к отчету
    """
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            related_name='report_access_logs')
    accessed_at = models.DateTimeField(_('Дата доступа'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    
    class Meta:
        verbose_name = _('доступ к отчету')
        verbose_name_plural = _('доступы к отчетам')
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.report} - {self.user} ({self.accessed_at.strftime('%d.%m.%Y %H:%M')})"


class AcademicPerformanceReport(models.Model):
    """
    Модель отчета об академической успеваемости
    """
    base_report = models.OneToOneField(Report, on_delete=models.CASCADE, 
                                      related_name='academic_performance_details')
    
    # Период отчета
    academic_year = models.ForeignKey('university_structure.AcademicYear', on_delete=models.SET_NULL, 
                                     related_name='academic_performance_reports', 
                                     null=True, blank=True)
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.SET_NULL, 
                                related_name='academic_performance_reports', 
                                null=True, blank=True)
    
    # Фильтры для отчета
    DETAIL_LEVEL_CHOICES = (
        ('faculty', _('Факультет')),
        ('department', _('Кафедра')),
        ('group', _('Группа')),
        ('student', _('Студент')),
        ('subject', _('Предмет')),
    )
    detail_level = models.CharField(_('Уровень детализации'), max_length=20, choices=DETAIL_LEVEL_CHOICES)
    
    # Ссылки на объекты отчета
    faculty = models.ForeignKey('university_structure.Faculty', on_delete=models.SET_NULL, 
                               related_name='academic_performance_reports', 
                               null=True, blank=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.SET_NULL, 
                                  related_name='academic_performance_reports', 
                                  null=True, blank=True)
    group = models.ForeignKey('university_structure.Group', on_delete=models.SET_NULL, 
                             related_name='academic_performance_reports', 
                             null=True, blank=True)
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.SET_NULL, 
                               related_name='academic_performance_reports', 
                               null=True, blank=True)
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.SET_NULL, 
                               related_name='academic_performance_reports', 
                               null=True, blank=True)
    
    # Данные отчета
    data = models.JSONField(_('Данные отчета'), default=dict)
    
    # Показатели
    average_grade = models.DecimalField(_('Средний балл'), max_digits=5, decimal_places=2, null=True, blank=True)
    passing_rate = models.DecimalField(_('Процент успеваемости'), max_digits=5, decimal_places=2, null=True, blank=True)
    excellence_rate = models.DecimalField(_('Процент отличников'), max_digits=5, decimal_places=2, null=True, blank=True)
    failure_rate = models.DecimalField(_('Процент неуспевающих'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = _('отчет об успеваемости')
        verbose_name_plural = _('отчеты об успеваемости')
    
    def __str__(self):
        return f"Отчет об успеваемости: {self.base_report.title}"


class AttendanceReport(models.Model):
    """
    Модель отчета о посещаемости
    """
    base_report = models.OneToOneField(Report, on_delete=models.CASCADE, 
                                      related_name='attendance_details')
    
    # Период отчета
    academic_year = models.ForeignKey('university_structure.AcademicYear', on_delete=models.SET_NULL, 
                                     related_name='attendance_reports', 
                                     null=True, blank=True)
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.SET_NULL, 
                                related_name='attendance_reports', 
                                null=True, blank=True)
    
    # Фильтры для отчета
    DETAIL_LEVEL_CHOICES = (
        ('faculty', _('Факультет')),
        ('department', _('Кафедра')),
        ('group', _('Группа')),
        ('student', _('Студент')),
        ('subject', _('Предмет')),
    )
    detail_level = models.CharField(_('Уровень детализации'), max_length=20, choices=DETAIL_LEVEL_CHOICES)
    
    # Ссылки на объекты отчета
    faculty = models.ForeignKey('university_structure.Faculty', on_delete=models.SET_NULL, 
                               related_name='attendance_reports', 
                               null=True, blank=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.SET_NULL, 
                                  related_name='attendance_reports', 
                                  null=True, blank=True)
    group = models.ForeignKey('university_structure.Group', on_delete=models.SET_NULL, 
                             related_name='attendance_reports', 
                             null=True, blank=True)
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.SET_NULL, 
                               related_name='attendance_reports', 
                               null=True, blank=True)
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.SET_NULL, 
                               related_name='attendance_reports', 
                               null=True, blank=True)
    
    # Данные отчета
    data = models.JSONField(_('Данные отчета'), default=dict)
    
    # Показатели
    attendance_rate = models.DecimalField(_('Процент посещаемости'), max_digits=5, decimal_places=2, null=True, blank=True)
    absence_rate = models.DecimalField(_('Процент пропусков'), max_digits=5, decimal_places=2, null=True, blank=True)
    excused_absence_rate = models.DecimalField(_('Процент уважительных причин'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = _('отчет о посещаемости')
        verbose_name_plural = _('отчеты о посещаемости')
    
    def __str__(self):
        return f"Отчет о посещаемости: {self.base_report.title}"


class GradeSheet(models.Model):
    """
    Модель ведомости оценок (зачетная, экзаменационная)
    """
    base_report = models.OneToOneField(Report, on_delete=models.CASCADE, 
                                      related_name='grade_sheet_details')
    
    # Информация о предмете и группе
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='grade_sheets')
    group = models.ForeignKey('university_structure.Group', on_delete=models.CASCADE, 
                             related_name='grade_sheets')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, 
                               related_name='grade_sheets')
    
    # Информация о семестре и контроле
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='grade_sheets')
    
    CONTROL_FORM_CHOICES = (
        ('exam', _('Экзамен')),
        ('credit', _('Зачет')),
        ('credit_grade', _('Дифференцированный зачет')),
        ('coursework', _('Курсовая работа')),
        ('coursework_project', _('Курсовой проект')),
    )
    control_form = models.CharField(_('Форма контроля'), max_length=20, choices=CONTROL_FORM_CHOICES)
    
    # Дата проведения
    date = models.DateField(_('Дата проведения'), null=True, blank=True)
    
    # Статус ведомости
    STATUS_CHOICES = (
        ('draft', _('Черновик')),
        ('active', _('Активна')),
        ('closed', _('Закрыта')),
        ('archived', _('В архиве')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Номер ведомости
    number = models.CharField(_('Номер ведомости'), max_length=50, blank=True)
    
    # Данные ведомости
    data = models.JSONField(_('Данные ведомости'), default=dict)
    
    # Даты
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    closed_at = models.DateTimeField(_('Дата закрытия'), null=True, blank=True)
    
    # Подписи
    signed_by_teacher = models.BooleanField(_('Подписана преподавателем'), default=False)
    signed_by_head = models.BooleanField(_('Подписана зав. кафедрой'), default=False)
    
    class Meta:
        verbose_name = _('ведомость')
        verbose_name_plural = _('ведомости')
        unique_together = ('subject', 'group', 'semester', 'control_form')
    
    def __str__(self):
        return f"Ведомость {self.number}: {self.subject.name} - {self.group.name} ({self.get_control_form_display()})"


class GradeSheetEntry(models.Model):
    """
    Модель записи в ведомости (оценка студента)
    """
    grade_sheet = models.ForeignKey(GradeSheet, on_delete=models.CASCADE, related_name='entries')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='grade_sheet_entries')
    
    # Оценка
    GRADE_CHOICES = (
        ('excellent', _('Отлично')),
        ('good', _('Хорошо')),
        ('satisfactory', _('Удовлетворительно')),
        ('unsatisfactory', _('Неудовлетворительно')),
        ('passed', _('Зачтено')),
        ('not_passed', _('Не зачтено')),
        ('not_appeared', _('Не явился')),
        ('not_allowed', _('Не допущен')),
    )
    grade = models.CharField(_('Оценка'), max_length=20, choices=GRADE_CHOICES, null=True, blank=True)
    
    # Числовая оценка (если применимо)
    numeric_grade = models.PositiveSmallIntegerField(_('Числовая оценка'), null=True, blank=True)
    
    # Дата выставления оценки
    graded_at = models.DateTimeField(_('Дата выставления'), auto_now=True)
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='graded_entries', 
                                 null=True, blank=True)
    
    # Комментарий
    comment = models.TextField(_('Комментарий'), blank=True)
    
    class Meta:
        verbose_name = _('запись в ведомости')
        verbose_name_plural = _('записи в ведомостях')
        unique_together = ('grade_sheet', 'student')
    
    def __str__(self):
        grade_display = self.get_grade_display() if self.grade else 'Не выставлена'
        return f"{self.student.user.get_full_name()} - {grade_display}"


class Transcript(models.Model):
    """
    Модель зачетной книжки студента
    """
    base_report = models.OneToOneField(Report, on_delete=models.CASCADE, 
                                      related_name='transcript_details')
    
    # Информация о студенте
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='transcripts')
    
    # Информация о периоде
    academic_year = models.ForeignKey('university_structure.AcademicYear', on_delete=models.SET_NULL, 
                                     related_name='transcripts', 
                                     null=True, blank=True)
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.SET_NULL, 
                                related_name='transcripts', 
                                null=True, blank=True)
    
    # Номер зачетной книжки
    transcript_number = models.CharField(_('Номер зачетной книжки'), max_length=50, blank=True)
    
    # Данные зачетной книжки
    data = models.JSONField(_('Данные зачетной книжки'), default=dict)
    
    # Показатели
    gpa = models.DecimalField(_('Средний балл'), max_digits=5, decimal_places=2, null=True, blank=True)
    ects = models.DecimalField(_('ECTS кредиты'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Даты
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('зачетная книжка')
        verbose_name_plural = _('зачетные книжки')
    
    def __str__(self):
        return f"Зачетная книжка: {self.student.user.get_full_name()}"


class TeacherWorkloadReport(models.Model):
    """
    Модель отчета о нагрузке преподавателя
    """
    base_report = models.OneToOneField(Report, on_delete=models.CASCADE, 
                                      related_name='workload_details')
    
    # Информация о преподавателе или кафедре
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                               related_name='workload_reports', 
                               null=True, blank=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.SET_NULL, 
                                  related_name='workload_reports', 
                                  null=True, blank=True)
    
    # Информация о периоде
    academic_year = models.ForeignKey('university_structure.AcademicYear', on_delete=models.SET_NULL, 
                                     related_name='workload_reports', 
                                     null=True, blank=True)
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.SET_NULL, 
                                related_name='workload_reports', 
                                null=True, blank=True)
    
    # Данные отчета
    data = models.JSONField(_('Данные отчета'), default=dict)
    
    # Показатели нагрузки (в часах)
    total_hours = models.DecimalField(_('Всего часов'), max_digits=8, decimal_places=2, null=True, blank=True)
    lectures_hours = models.DecimalField(_('Лекции'), max_digits=8, decimal_places=2, null=True, blank=True)
    seminars_hours = models.DecimalField(_('Семинары'), max_digits=8, decimal_places=2, null=True, blank=True)
    labs_hours = models.DecimalField(_('Лабораторные'), max_digits=8, decimal_places=2, null=True, blank=True)
    practices_hours = models.DecimalField(_('Практики'), max_digits=8, decimal_places=2, null=True, blank=True)
    consultations_hours = models.DecimalField(_('Консультации'), max_digits=8, decimal_places=2, null=True, blank=True)
    exams_hours = models.DecimalField(_('Экзамены'), max_digits=8, decimal_places=2, null=True, blank=True)
    course_works_hours = models.DecimalField(_('Курсовые работы'), max_digits=8, decimal_places=2, null=True, blank=True)
    thesis_hours = models.DecimalField(_('Дипломные работы'), max_digits=8, decimal_places=2, null=True, blank=True)
    other_hours = models.DecimalField(_('Прочие'), max_digits=8, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = _('отчет о нагрузке')
        verbose_name_plural = _('отчеты о нагрузке')
    
    def __str__(self):
        if self.teacher:
            return f"Нагрузка: {self.teacher.user.get_full_name()}"
        else:
            return f"Нагрузка кафедры: {self.department.name}"


class ContingentReport(models.Model):
    """
    Модель отчета о контингенте студентов
    """
    base_report = models.OneToOneField(Report, on_delete=models.CASCADE, 
                                      related_name='contingent_details')
    
    # Информация о периоде
    academic_year = models.ForeignKey('university_structure.AcademicYear', on_delete=models.SET_NULL, 
                                     related_name='contingent_reports', 
                                     null=True, blank=True)
    date = models.DateField(_('Дата отчета'), default=timezone.now)
    
    # Фильтры для отчета
    DETAIL_LEVEL_CHOICES = (
        ('university', _('Университет')),
        ('faculty', _('Факультет')),
        ('department', _('Кафедра')),
        ('specialization', _('Специальность')),
        ('group', _('Группа')),
    )
    detail_level = models.CharField(_('Уровень детализации'), max_length=20, choices=DETAIL_LEVEL_CHOICES)
    
    # Ссылки на объекты отчета
    faculty = models.ForeignKey('university_structure.Faculty', on_delete=models.SET_NULL, 
                               related_name='contingent_reports', 
                               null=True, blank=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.SET_NULL, 
                                  related_name='contingent_reports', 
                                  null=True, blank=True)
    specialization = models.ForeignKey('university_structure.Specialization', on_delete=models.SET_NULL, 
                                      related_name='contingent_reports', 
                                      null=True, blank=True)
    group = models.ForeignKey('university_structure.Group', on_delete=models.SET_NULL, 
                             related_name='contingent_reports', 
                             null=True, blank=True)
    
    # Данные отчета
    data = models.JSONField(_('Данные отчета'), default=dict)
    
    # Показатели
    total_students = models.PositiveIntegerField(_('Всего студентов'), null=True, blank=True)
    budget_students = models.PositiveIntegerField(_('На бюджете'), null=True, blank=True)
    contract_students = models.PositiveIntegerField(_('На контракте'), null=True, blank=True)
    full_time_students = models.PositiveIntegerField(_('Очная форма'), null=True, blank=True)
    part_time_students = models.PositiveIntegerField(_('Заочная форма'), null=True, blank=True)
    evening_students = models.PositiveIntegerField(_('Вечерняя форма'), null=True, blank=True)
    distance_students = models.PositiveIntegerField(_('Дистанционная форма'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('отчет о контингенте')
        verbose_name_plural = _('отчеты о контингенте')
    
    def __str__(self):
        return f"Контингент: {self.base_report.title}"


class ReportScheduledTask(models.Model):
    """
    Модель для регулярного автоматического создания отчетов
    """
    name = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    
    # Связь с шаблоном
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, 
                                related_name='scheduled_tasks')
    
    # Параметры для отчета
    parameters = models.JSONField(_('Параметры'), default=dict)
    
    # Расписание запуска
    RECURRENCE_CHOICES = (
        ('daily', _('Ежедневно')),
        ('weekly', _('Еженедельно')),
        ('monthly', _('Ежемесячно')),
        ('quarterly', _('Ежеквартально')),
        ('semester', _('По семестрам')),
        ('yearly', _('Ежегодно')),
    )
    recurrence = models.CharField(_('Периодичность'), max_length=20, choices=RECURRENCE_CHOICES)
    
    # Настройки конкретного времени
    weekday = models.PositiveSmallIntegerField(_('День недели (0-6)'), null=True, blank=True)
    day_of_month = models.PositiveSmallIntegerField(_('День месяца'), null=True, blank=True)
    hour = models.PositiveSmallIntegerField(_('Час (0-23)'), default=0)
    minute = models.PositiveSmallIntegerField(_('Минута (0-59)'), default=0)
    
    # Активность задачи
    is_active = models.BooleanField(_('Активна'), default=True)
    
    # Получатели отчета
    recipients = models.ManyToManyField('accounts.User', related_name='scheduled_reports', blank=True)
    
    # Настройки рассылки
    send_email = models.BooleanField(_('Отправлять по email'), default=True)
    email_subject = models.CharField(_('Тема письма'), max_length=255, blank=True)
    email_body = models.TextField(_('Текст письма'), blank=True)
    
    # Метаданные
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='created_report_tasks', 
                                  null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    last_run = models.DateTimeField(_('Последний запуск'), null=True, blank=True)
    next_run = models.DateTimeField(_('Следующий запуск'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('запланированная задача отчета')
        verbose_name_plural = _('запланированные задачи отчетов')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_recurrence_display()})"


class ReportScheduledRun(models.Model):
    """
    Модель для отслеживания выполнения запланированных отчетов
    """
    task = models.ForeignKey(ReportScheduledTask, on_delete=models.CASCADE, related_name='runs')
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, related_name='scheduled_run', null=True, blank=True)
    
    # Время запуска и статус
    scheduled_for = models.DateTimeField(_('Запланировано на'))
    started_at = models.DateTimeField(_('Начало выполнения'), null=True, blank=True)
    finished_at = models.DateTimeField(_('Окончание выполнения'), null=True, blank=True)
    
    STATUS_CHOICES = (
        ('pending', _('Ожидает')),
        ('running', _('Выполняется')),
        ('completed', _('Завершено')),
        ('failed', _('Ошибка')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Информация об ошибке
    error_message = models.TextField(_('Сообщение об ошибке'), blank=True)
    
    # Информация о рассылке
    is_sent = models.BooleanField(_('Отправлено'), default=False)
    sent_at = models.DateTimeField(_('Время отправки'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('запуск запланированного отчета')
        verbose_name_plural = _('запуски запланированных отчетов')
        ordering = ['-scheduled_for']
    
    def __str__(self):
        return f"Запуск {self.task.name} - {self.scheduled_for}"


class ReportCategory(models.Model):
    """
    Модель категории отчетов для организации в интерфейсе
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='subcategories', verbose_name=_('Родительская категория'))
    icon = models.CharField(_('Иконка'), max_length=50, blank=True)
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    class Meta:
        verbose_name = _('категория отчетов')
        verbose_name_plural = _('категории отчетов')
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class ReportDashboard(models.Model):
    """
    Модель панели отчетов/дашборда
    """
    name = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    
    # Настройки доступа
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='owned_dashboards')
    is_public = models.BooleanField(_('Публичный'), default=False)
    shared_with = models.ManyToManyField('accounts.User', related_name='shared_dashboards', blank=True)
    
    # Настройки внешнего вида
    layout = models.JSONField(_('Макет'), default=dict)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('панель отчетов')
        verbose_name_plural = _('панели отчетов')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.owner.get_full_name()})"


class DashboardWidget(models.Model):
    """
    Модель виджета для панели отчетов
    """
    dashboard = models.ForeignKey(ReportDashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(_('Заголовок'), max_length=255)
    
    # Связь с отчетом
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, 
                              related_name='dashboard_widgets', 
                              null=True, blank=True)
    
    # Тип виджета
    WIDGET_TYPES = (
        ('chart', _('График')),
        ('table', _('Таблица')),
        ('counter', _('Счетчик')),
        ('gauge', _('Индикатор')),
        ('text', _('Текст')),
        ('custom', _('Пользовательский')),
    )
    widget_type = models.CharField(_('Тип виджета'), max_length=20, choices=WIDGET_TYPES)
    
    # Настройки виджета
    settings = models.JSONField(_('Настройки'), default=dict)
    
    # Данные виджета (если нет отчета)
    data = models.JSONField(_('Данные'), null=True, blank=True)
    
    # Положение на дашборде
    position_x = models.PositiveSmallIntegerField(_('Позиция X'), default=0)
    position_y = models.PositiveSmallIntegerField(_('Позиция Y'), default=0)
    width = models.PositiveSmallIntegerField(_('Ширина'), default=4)
    height = models.PositiveSmallIntegerField(_('Высота'), default=4)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('виджет панели')
        verbose_name_plural = _('виджеты панели')
        ordering = ['dashboard', 'position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


class ReportSubscription(models.Model):
    """
    Модель подписки на отчеты
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='report_subscriptions')
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Настройки подписки
    is_active = models.BooleanField(_('Активна'), default=True)
    parameters = models.JSONField(_('Параметры'), default=dict)
    
    # Расписание
    RECURRENCE_CHOICES = (
        ('daily', _('Ежедневно')),
        ('weekly', _('Еженедельно')),
        ('monthly', _('Ежемесячно')),
        ('quarterly', _('Ежеквартально')),
        ('semester', _('По семестрам')),
        ('yearly', _('Ежегодно')),
    )
    recurrence = models.CharField(_('Периодичность'), max_length=20, choices=RECURRENCE_CHOICES)
    
    # Настройки рассылки
    send_email = models.BooleanField(_('Отправлять по email'), default=True)
    send_notification = models.BooleanField(_('Отправлять уведомление'), default=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    last_sent = models.DateTimeField(_('Последняя отправка'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('подписка на отчеты')
        verbose_name_plural = _('подписки на отчеты')
        unique_together = ('user', 'report_template')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.report_template.name}"


# Сигналы для автоматизации
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=GradeSheet)
def create_grade_sheet_entries(sender, instance, created, **kwargs):
    """
    Автоматически создает записи в ведомости для всех студентов группы
    """
    if created:
        # Получаем всех студентов группы
        from accounts.models import StudentProfile
        students = StudentProfile.objects.filter(group=instance.group)
        
        # Создаем записи для каждого студента
        for student in students:
            GradeSheetEntry.objects.create(
                grade_sheet=instance,
                student=student
            )

@receiver(post_save, sender=Report)
def update_report_status(sender, instance, **kwargs):
    """
    Обновляет статус отчета в связанных запланированных запусках
    """
    if instance.status in ['completed', 'failed']:
        # Ищем связанные запланированные запуски
        scheduled_runs = ReportScheduledRun.objects.filter(
            report=instance,
            status='running'
        )
        
        # Обновляем их статус
        for run in scheduled_runs:
            run.status = 'completed' if instance.status == 'completed' else 'failed'
            run.finished_at = timezone.now()
            if instance.status == 'failed' and instance.error_message:
                run.error_message = instance.error_message
            run.save()