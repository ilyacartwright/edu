from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator
from decimal import Decimal
import uuid


class GradeSystem(models.Model):
    """
    Модель системы оценивания
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    
    # Диапазон значений
    min_value = models.DecimalField(_('Минимальное значение'), max_digits=5, decimal_places=2, 
                                   default=Decimal('0.00'))
    max_value = models.DecimalField(_('Максимальное значение'), max_digits=5, decimal_places=2, 
                                   default=Decimal('100.00'))
    passing_value = models.DecimalField(_('Проходной балл'), max_digits=5, decimal_places=2, 
                                      default=Decimal('60.00'))
    
    # Тип системы
    SYSTEM_TYPES = (
        ('numeric', _('Числовая (от min до max)')),
        ('letter', _('Буквенная (A, B, C...)')),
        ('pass_fail', _('Зачет/Незачет')),
        ('custom', _('Пользовательская')),
    )
    system_type = models.CharField(_('Тип системы'), max_length=20, choices=SYSTEM_TYPES)
    
    # Настройки округления
    ROUNDING_METHODS = (
        ('none', _('Не округлять')),
        ('ceil', _('К большему')),
        ('floor', _('К меньшему')),
        ('round', _('Математическое')),
    )
    rounding_method = models.CharField(_('Метод округления'), max_length=10, 
                                      choices=ROUNDING_METHODS, default='round')
    decimal_places = models.PositiveSmallIntegerField(_('Знаков после запятой'), default=2)
    
    # Метаданные
    is_default = models.BooleanField(_('По умолчанию'), default=False)
    
    class Meta:
        verbose_name = _('система оценивания')
        verbose_name_plural = _('системы оценивания')
    
    def __str__(self):
        return self.name


class GradeValue(models.Model):
    """
    Модель значения оценки в системе оценивания
    """
    grade_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, 
                                    related_name='values', verbose_name=_('Система оценивания'))
    
    # Значение оценки
    value = models.CharField(_('Значение'), max_length=10)
    numeric_value = models.DecimalField(_('Числовое значение'), max_digits=5, decimal_places=2)
    
    # Диапазон для автоматической конвертации
    min_percent = models.DecimalField(_('От (%)'), max_digits=5, decimal_places=2)
    max_percent = models.DecimalField(_('До (%)'), max_digits=5, decimal_places=2)
    
    # Дополнительная информация
    description = models.CharField(_('Описание'), max_length=100, blank=True)
    is_passing = models.BooleanField(_('Проходная оценка'), default=True)
    
    class Meta:
        verbose_name = _('значение оценки')
        verbose_name_plural = _('значения оценок')
        ordering = ['grade_system', '-numeric_value']
        unique_together = ['grade_system', 'value']
    
    def __str__(self):
        return f"{self.grade_system.name}: {self.value} ({self.numeric_value})"


class GradingScale(models.Model):
    """
    Модель шкалы перевода оценок между системами
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    
    # Исходная и целевая системы оценивания
    source_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, 
                                     related_name='source_scales', verbose_name=_('Исходная система'))
    target_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, 
                                     related_name='target_scales', verbose_name=_('Целевая система'))
    
    # Метаданные
    is_active = models.BooleanField(_('Активна'), default=True)
    
    class Meta:
        verbose_name = _('шкала перевода оценок')
        verbose_name_plural = _('шкалы перевода оценок')
        unique_together = ['source_system', 'target_system']
    
    def __str__(self):
        return f"{self.name} ({self.source_system.name} → {self.target_system.name})"


class GradeConversion(models.Model):
    """
    Модель соответствия значений в шкале перевода
    """
    scale = models.ForeignKey(GradingScale, on_delete=models.CASCADE, 
                             related_name='conversions', verbose_name=_('Шкала перевода'))
    
    # Соответствие значений
    source_value = models.ForeignKey(GradeValue, on_delete=models.CASCADE, 
                                    related_name='source_conversions', verbose_name=_('Исходное значение'))
    target_value = models.ForeignKey(GradeValue, on_delete=models.CASCADE, 
                                    related_name='target_conversions', verbose_name=_('Целевое значение'))
    
    class Meta:
        verbose_name = _('соответствие оценок')
        verbose_name_plural = _('соответствия оценок')
        unique_together = ['scale', 'source_value']
    
    def __str__(self):
        return f"{self.scale}: {self.source_value.value} → {self.target_value.value}"


class GradeType(models.Model):
    """
    Модель типа оценки (текущая, экзаменационная, итоговая)
    """
    name = models.CharField(_('Название'), max_length=100)
    code = models.CharField(_('Код'), max_length=20, unique=True)
    description = models.TextField(_('Описание'), blank=True)
    
    # Настройки веса
    weight_in_final = models.DecimalField(_('Вес в итоговой оценке'), max_digits=5, decimal_places=2, 
                                         default=Decimal('1.00'))
    
    # Система оценивания по умолчанию
    default_grade_system = models.ForeignKey(GradeSystem, on_delete=models.SET_NULL, 
                                           related_name='grade_types',
                                           null=True, blank=True, 
                                           verbose_name=_('Система оценивания по умолчанию'))
    
    class Meta:
        verbose_name = _('тип оценки')
        verbose_name_plural = _('типы оценок')
    
    def __str__(self):
        return self.name


class Grade(models.Model):
    """
    Модель оценки студента
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='grades', verbose_name=_('Студент'))
    
    # Связь с предметом учебного плана
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='grades', verbose_name=_('Предмет'))
    academic_plan_subject = models.ForeignKey('university_structure.AcademicPlanSubject', 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True,
                                            related_name='grades', 
                                            verbose_name=_('Предмет учебного плана'))
    
    # Связь с семестром
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='grades', verbose_name=_('Семестр'))
    
    # Тип оценки и значение
    grade_type = models.ForeignKey(GradeType, on_delete=models.CASCADE, 
                                  related_name='grades', verbose_name=_('Тип оценки'))
    grade_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, 
                                    related_name='grades', verbose_name=_('Система оценивания'))
    grade_value = models.ForeignKey(GradeValue, on_delete=models.CASCADE, 
                                   related_name='grades', verbose_name=_('Значение оценки'))
    
    # Связь с курсом (если это оценка из курса)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, 
                              null=True, blank=True,
                              related_name='grades', verbose_name=_('Курс'))
    course_element = models.ForeignKey('courses.CourseElement', on_delete=models.SET_NULL, 
                                      null=True, blank=True,
                                      related_name='grades', verbose_name=_('Элемент курса'))
    
    # Связь с экзаменом/зачетом
    exam = models.ForeignKey('schedule.ExamSchedule', on_delete=models.SET_NULL, 
                            null=True, blank=True,
                            related_name='grades', verbose_name=_('Экзамен/зачет'))
    
    # Дополнительная информация
    points = models.DecimalField(_('Баллы'), max_digits=10, decimal_places=2, null=True, blank=True)
    max_points = models.DecimalField(_('Максимум баллов'), max_digits=10, decimal_places=2, 
                                    null=True, blank=True)
    percentage = models.DecimalField(_('Процент'), max_digits=5, decimal_places=2, 
                                    null=True, blank=True)
    
    # Источник оценки
    SOURCE_CHOICES = (
        ('manual', _('Ручной ввод')),
        ('auto', _('Автоматически')),
        ('imported', _('Импортировано')),
        ('calculated', _('Вычислено')),
    )
    source = models.CharField(_('Источник'), max_length=20, choices=SOURCE_CHOICES, default='manual')
    
    # Примечания и комментарии
    comments = models.TextField(_('Комментарии'), blank=True)
    
    # Учёт даты
    date = models.DateField(_('Дата'), default=timezone.now)
    
    # Кто выставил оценку
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='given_grades', 
                                 null=True, blank=True,
                                 verbose_name=_('Выставил'))
    
    # Статус оценки
    STATUS_CHOICES = (
        ('draft', _('Черновик')),
        ('final', _('Окончательная')),
        ('corrected', _('Исправленная')),
        ('annulled', _('Аннулированная')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='final')
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('оценка')
        verbose_name_plural = _('оценки')
        ordering = ['-date', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.subject} ({self.grade_value.value})"
    
    @property
    def is_passing(self):
        """Проверяет, является ли оценка проходной"""
        return self.grade_value.is_passing


class GradeSheet(models.Model):
    """
    Модель ведомости оценок
    """
    # Связь с предметом учебного плана
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='academic_grade_sheets', verbose_name=_('Предмет'))
    academic_plan_subject = models.ForeignKey('university_structure.AcademicPlanSubject', 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True,
                                            related_name='grade_sheets', 
                                            verbose_name=_('Предмет учебного плана'))
    
    # Связь с группой и семестром
    group = models.ForeignKey('university_structure.Group', on_delete=models.CASCADE, 
                             related_name='academic_grade_sheets', verbose_name=_('Группа'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='academic_grade_sheets', verbose_name=_('Семестр'))
    
    # Тип ведомости
    SHEET_TYPES = (
        ('exam', _('Экзаменационная')),
        ('credit', _('Зачетная')),
        ('credit_grade', _('Дифференцированный зачет')),
        ('course_work', _('Курсовая работа')),
        ('practice', _('Практика')),
        ('final', _('Итоговая')),
    )
    sheet_type = models.CharField(_('Тип ведомости'), max_length=20, choices=SHEET_TYPES)
    
    # Связь с экзаменом/зачетом
    exam = models.OneToOneField('schedule.ExamSchedule', on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               related_name='grade_sheet', verbose_name=_('Экзамен/зачет'))
    
    # Преподаватель, ответственный за ведомость
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, 
                               related_name='academic_grade_sheets', verbose_name=_('Преподаватель'))
    
    # Номер ведомости
    number = models.CharField(_('Номер ведомости'), max_length=50, unique=True)
    
    # Даты
    issue_date = models.DateField(_('Дата выдачи'), default=timezone.now)
    expiration_date = models.DateField(_('Срок действия до'), null=True, blank=True)
    
    # Статус ведомости
    STATUS_CHOICES = (
        ('draft', _('Черновик')),
        ('issued', _('Выдана')),
        ('in_progress', _('В процессе заполнения')),
        ('completed', _('Заполнена')),
        ('verified', _('Проверена')),
        ('approved', _('Утверждена')),
        ('archived', _('В архиве')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Система оценивания
    grade_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, 
                                    related_name='grade_sheets', verbose_name=_('Система оценивания'))
    
    # Дополнительная информация
    comments = models.TextField(_('Комментарии'), blank=True)
    
    # Подписи
    issued_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='issued_grade_sheets', 
                                 null=True, blank=True,
                                 verbose_name=_('Выдал'))
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='verified_grade_sheets', 
                                   null=True, blank=True,
                                   verbose_name=_('Проверил'))
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='approved_grade_sheets', 
                                   null=True, blank=True,
                                   verbose_name=_('Утвердил'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('ведомость оценок')
        verbose_name_plural = _('ведомости оценок')
        ordering = ['-issue_date', 'group']
    
    def __str__(self):
        return f"Ведомость {self.number}: {self.group} - {self.subject} ({self.get_sheet_type_display()})"

class GradeSheetItem(models.Model):
    """
    Модель записи в ведомости оценок
    """
    grade_sheet = models.ForeignKey(GradeSheet, on_delete=models.CASCADE, 
                                   related_name='items', verbose_name=_('Ведомость'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='grade_sheet_items', verbose_name=_('Студент'))
    
    # Оценка
    grade_value = models.ForeignKey(GradeValue, on_delete=models.CASCADE, 
                                   related_name='grade_sheet_items', 
                                   null=True, blank=True,
                                   verbose_name=_('Значение оценки'))
    
    # Дополнительная информация
    points = models.DecimalField(_('Баллы'), max_digits=10, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(_('Процент'), max_digits=5, decimal_places=2, 
                                    null=True, blank=True)
    
    # Статус
    STATUS_CHOICES = (
        ('not_graded', _('Не оценено')),
        ('graded', _('Оценено')),
        ('absent', _('Не явился')),
        ('not_allowed', _('Не допущен')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='not_graded')
    
    # Дата выставления оценки
    graded_at = models.DateTimeField(_('Дата оценки'), null=True, blank=True)
    
    # Кто выставил оценку
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='grade_sheet_items', 
                                 null=True, blank=True,
                                 verbose_name=_('Выставил'))
    
    # Комментарии
    comments = models.TextField(_('Комментарии'), blank=True)
    
    class Meta:
        verbose_name = _('запись в ведомости')
        verbose_name_plural = _('записи в ведомости')
        ordering = ['grade_sheet', 'student']
        unique_together = ['grade_sheet', 'student']
    
    def __str__(self):
        grade_info = f" - {self.grade_value.value}" if self.grade_value else ""
        return f"{self.student}{grade_info} ({self.grade_sheet.number})"
    
    def save(self, *args, **kwargs):
        """Создает запись в истории оценок и обновляет связанную оценку при изменении"""
        is_new = self.pk is None
        old_instance = None
        
        if not is_new:
            try:
                old_instance = GradeSheetItem.objects.get(pk=self.pk)
            except GradeSheetItem.DoesNotExist:
                pass
        
        # Устанавливаем дату выставления оценки
        if self.status == 'graded' and not self.graded_at:
            self.graded_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Создаем соответствующую запись в истории
        if old_instance is None or old_instance.grade_value != self.grade_value:
            if self.status == 'graded' and self.grade_value:
                # Создаем или обновляем оценку в общей таблице оценок
                defaults = {
                    'subject': self.grade_sheet.subject,
                    'academic_plan_subject': self.grade_sheet.academic_plan_subject,
                    'semester': self.grade_sheet.semester,
                    'grade_system': self.grade_sheet.grade_system,
                    'grade_value': self.grade_value,
                    'points': self.points,
                    'percentage': self.percentage,
                    'source': 'manual',
                    'comments': self.comments,
                    'date': timezone.now().date(),
                    'graded_by': self.graded_by,
                    'status': 'final',
                }
                
                # Определяем тип оценки на основе типа ведомости
                sheet_type = self.grade_sheet.sheet_type
                grade_type_code = 'current'
                
                if sheet_type == 'exam':
                    grade_type_code = 'exam'
                elif sheet_type in ['credit', 'credit_grade']:
                    grade_type_code = 'credit'
                elif sheet_type == 'course_work':
                    grade_type_code = 'course_work'
                elif sheet_type == 'practice':
                    grade_type_code = 'practice'
                elif sheet_type == 'final':
                    grade_type_code = 'final'
                
                grade_type = GradeType.objects.get(code=grade_type_code)
                defaults['grade_type'] = grade_type
                
                # Если есть связанный экзамен, добавляем его
                if self.grade_sheet.exam:
                    defaults['exam'] = self.grade_sheet.exam
                
                # Создаем или обновляем запись оценки
                Grade.objects.update_or_create(
                    student=self.student,
                    subject=self.grade_sheet.subject,
                    semester=self.grade_sheet.semester,
                    grade_type=grade_type,
                    defaults=defaults
                )
                
                # Создаем запись в истории оценок
                GradeHistory.objects.create(
                    student=self.student,
                    subject=self.grade_sheet.subject,
                    semester=self.grade_sheet.semester,
                    grade_sheet_item=self,
                    previous_value=old_instance.grade_value if old_instance and old_instance.grade_value else None,
                    new_value=self.grade_value,
                    changed_by=self.graded_by,
                    change_type='update' if old_instance and old_instance.grade_value else 'create'
                )


class GradeHistory(models.Model):
    """
    Модель истории изменений оценок
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='grade_history', verbose_name=_('Студент'))
    
    # Связь с предметом и семестром
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='grade_history', verbose_name=_('Предмет'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='grade_history', verbose_name=_('Семестр'))
    
    # Связь с ведомостью (если оценка из ведомости)
    grade_sheet_item = models.ForeignKey(GradeSheetItem, on_delete=models.SET_NULL, 
                                        related_name='history', 
                                        null=True, blank=True,
                                        verbose_name=_('Запись в ведомости'))
    
    # Старое и новое значения
    previous_value = models.ForeignKey(GradeValue, on_delete=models.SET_NULL, 
                                      related_name='previous_history', 
                                      null=True, blank=True,
                                      verbose_name=_('Предыдущее значение'))
    new_value = models.ForeignKey(GradeValue, on_delete=models.SET_NULL, 
                                 related_name='new_history', 
                                 null=True, blank=True,
                                 verbose_name=_('Новое значение'))
    
    # Кто и когда изменил
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='grade_changes', 
                                  null=True, blank=True,
                                  verbose_name=_('Кто изменил'))
    changed_at = models.DateTimeField(_('Дата изменения'), auto_now_add=True)
    
    # Тип изменения
    CHANGE_TYPES = (
        ('create', _('Создание')),
        ('update', _('Изменение')),
        ('delete', _('Удаление')),
    )
    change_type = models.CharField(_('Тип изменения'), max_length=20, choices=CHANGE_TYPES)
    
    # Комментарии
    comments = models.TextField(_('Комментарии'), blank=True)
    
    class Meta:
        verbose_name = _('история оценок')
        verbose_name_plural = _('история оценок')
        ordering = ['-changed_at']
    
    def __str__(self):
        prev_val = self.previous_value.value if self.previous_value else '-'
        new_val = self.new_value.value if self.new_value else '-'
        return f"{self.student} - {self.subject}: {prev_val} → {new_val} ({self.changed_at})"


class Attendance(models.Model):
    """
    Модель посещаемости занятий
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='attendance', verbose_name=_('Студент'))
    class_instance = models.ForeignKey('schedule.Class', on_delete=models.CASCADE, 
                                      related_name='attendance', verbose_name=_('Занятие'))
    
    # Статус посещения
    STATUS_CHOICES = (
        ('present', _('Присутствовал')),
        ('absent', _('Отсутствовал')),
        ('late', _('Опоздал')),
        ('sick', _('Болен')),
        ('excused', _('Уважительная причина')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES)
    
    # Дополнительная информация
    late_minutes = models.PositiveSmallIntegerField(_('Опоздание (мин)'), null=True, blank=True)
    reason = models.TextField(_('Причина'), blank=True)
    
    # Кто отметил
    marked_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='marked_attendance', 
                                 null=True, blank=True,
                                 verbose_name=_('Отметил'))
    marked_at = models.DateTimeField(_('Дата отметки'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('посещаемость')
        verbose_name_plural = _('посещаемость')
        unique_together = ['student', 'class_instance']
    
    def __str__(self):
        return f"{self.student} - {self.class_instance}: {self.get_status_display()}"


class AttendanceSheet(models.Model):
    """
    Модель журнала посещаемости
    """
    class_instance = models.OneToOneField('schedule.Class', on_delete=models.CASCADE, 
                                         related_name='attendance_sheet', verbose_name=_('Занятие'))
    
    # Кто заполнил журнал
    filled_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                 related_name='filled_attendance_sheets', 
                                 null=True, blank=True,
                                 verbose_name=_('Заполнил'))
    
    # Статус заполнения
    STATUS_CHOICES = (
        ('not_filled', _('Не заполнен')),
        ('partially_filled', _('Частично заполнен')),
        ('filled', _('Заполнен')),
        ('verified', _('Проверен')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='not_filled')
    
    # Комментарии к занятию
    comments = models.TextField(_('Комментарии'), blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('журнал посещаемости')
        verbose_name_plural = _('журналы посещаемости')
    
    def __str__(self):
        return f"Журнал посещаемости: {self.class_instance}"

class StudentRecord(models.Model):
    """
    Модель зачетной книжки студента
    """
    student = models.OneToOneField('accounts.StudentProfile', on_delete=models.CASCADE, 
                                  related_name='record_book', verbose_name=_('Студент'))
    
    # Номер зачетной книжки
    record_number = models.CharField(_('Номер зачетной книжки'), max_length=50, unique=True)
    
    # Даты выдачи и закрытия
    issue_date = models.DateField(_('Дата выдачи'), default=timezone.now)
    closing_date = models.DateField(_('Дата закрытия'), null=True, blank=True)
    
    # Статус зачетной книжки
    STATUS_CHOICES = (
        ('active', _('Активна')),
        ('archived', _('В архиве')),
        ('lost', _('Утеряна')),
        ('closed', _('Закрыта')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Дополнительная информация
    comments = models.TextField(_('Комментарии'), blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('зачетная книжка')
        verbose_name_plural = _('зачетные книжки')
    
    def __str__(self):
        return f"Зачетная книжка {self.record_number}: {self.student}"


class RecordEntry(models.Model):
    """
    Модель записи в зачетной книжке
    """
    record = models.ForeignKey(StudentRecord, on_delete=models.CASCADE, 
                              related_name='entries', verbose_name=_('Зачетная книжка'))
    
    # Связь с предметом и семестром
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='record_entries', verbose_name=_('Предмет'))
    academic_plan_subject = models.ForeignKey('university_structure.AcademicPlanSubject', 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True,
                                            related_name='record_entries', 
                                            verbose_name=_('Предмет учебного плана'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='record_entries', verbose_name=_('Семестр'))
    
    # Тип записи
    ENTRY_TYPES = (
        ('exam', _('Экзамен')),
        ('credit', _('Зачет')),
        ('credit_grade', _('Дифференцированный зачет')),
        ('course_work', _('Курсовая работа')),
        ('course_project', _('Курсовой проект')),
        ('practice', _('Практика')),
        ('state_exam', _('Государственный экзамен')),
        ('vkr', _('Выпускная квалификационная работа')),
        ('other', _('Другое')),
    )
    entry_type = models.CharField(_('Тип записи'), max_length=20, choices=ENTRY_TYPES)
    
    # Общая информация
    hours = models.PositiveSmallIntegerField(_('Часы'), null=True, blank=True)
    credits = models.PositiveSmallIntegerField(_('Зачетные единицы'), null=True, blank=True)
    
    # Информация об оценке
    grade_system = models.ForeignKey(GradeSystem, on_delete=models.CASCADE, 
                                    related_name='record_entries', verbose_name=_('Система оценивания'))
    grade_value = models.ForeignKey(GradeValue, on_delete=models.CASCADE, 
                                   related_name='record_entries', verbose_name=_('Значение оценки'))
    
    # Связь с ведомостью
    grade_sheet_item = models.OneToOneField(GradeSheetItem, on_delete=models.SET_NULL, 
                                            null=True, blank=True,
                                            related_name='record_entry', verbose_name=_('Запись в ведомости'))
    
    # Дата внесения записи
    date = models.DateField(_('Дата записи'))
    
    # Кто внес запись
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='recorded_entries', 
                                   null=True, blank=True,
                                   verbose_name=_('Внес запись'))
    
    # Дополнительная информация
    comments = models.TextField(_('Комментарии'), blank=True)
    
    # Для курсовых работ и ВКР
    title = models.CharField(_('Название работы'), max_length=255, blank=True)
    supervisor = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                                  related_name='supervised_records', 
                                  null=True, blank=True,
                                  verbose_name=_('Руководитель'))
    
    class Meta:
        verbose_name = _('запись в зачетной книжке')
        verbose_name_plural = _('записи в зачетной книжке')
        ordering = ['semester', 'subject']
        unique_together = ['record', 'subject', 'semester', 'entry_type']
    
    def __str__(self):
        return f"{self.subject} - {self.get_entry_type_display()}: {self.grade_value.value}"


class AcademicPerformanceSummary(models.Model):
    """
    Модель сводной информации об успеваемости студента
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='performance_summaries', verbose_name=_('Студент'))
    
    # Период
    PERIOD_TYPES = (
        ('semester', _('Семестр')),
        ('academic_year', _('Учебный год')),
        ('all_time', _('За все время')),
    )
    period_type = models.CharField(_('Тип периода'), max_length=20, choices=PERIOD_TYPES)
    
    # Связь с семестром или учебным годом
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='performance_summaries', 
                                null=True, blank=True,
                                verbose_name=_('Семестр'))
    academic_year = models.ForeignKey('university_structure.AcademicYear', on_delete=models.CASCADE, 
                                     related_name='performance_summaries', 
                                     null=True, blank=True,
                                     verbose_name=_('Учебный год'))
    
    # Статистика успеваемости
    total_subjects = models.PositiveSmallIntegerField(_('Всего предметов'), default=0)
    excellent_count = models.PositiveSmallIntegerField(_('Отлично'), default=0)
    good_count = models.PositiveSmallIntegerField(_('Хорошо'), default=0)
    satisfactory_count = models.PositiveSmallIntegerField(_('Удовлетворительно'), default=0)
    failed_count = models.PositiveSmallIntegerField(_('Неудовлетворительно'), default=0)
    
    # Средний балл
    gpa = models.DecimalField(_('Средний балл'), max_digits=5, decimal_places=2, default=0)
    
    # Кредиты
    total_credits = models.PositiveSmallIntegerField(_('Всего зачетных единиц'), default=0)
    earned_credits = models.PositiveSmallIntegerField(_('Заработано зачетных единиц'), default=0)
    
    # Данные о посещаемости
    total_classes = models.PositiveSmallIntegerField(_('Всего занятий'), default=0)
    attended_classes = models.PositiveSmallIntegerField(_('Посещено занятий'), default=0)
    attendance_percentage = models.DecimalField(_('Процент посещаемости'), max_digits=5, decimal_places=2, 
                                              default=0)
    
    # Рейтинг
    ranking = models.PositiveSmallIntegerField(_('Рейтинг в группе'), null=True, blank=True)
    group_size = models.PositiveSmallIntegerField(_('Размер группы'), null=True, blank=True)
    
    # Метаданные
    calculated_at = models.DateTimeField(_('Дата расчета'), auto_now=True)
    
    class Meta:
        verbose_name = _('сводка успеваемости')
        verbose_name_plural = _('сводки успеваемости')
        ordering = ['student', '-semester']
        unique_together = [
            ['student', 'period_type', 'semester'],
            ['student', 'period_type', 'academic_year'],
        ]
    
    def __str__(self):
        period = ""
        if self.period_type == 'semester' and self.semester:
            period = f" - {self.semester}"
        elif self.period_type == 'academic_year' and self.academic_year:
            period = f" - {self.academic_year}"
        
        return f"Успеваемость {self.student}{period}"


class AcademicStanding(models.Model):
    """
    Модель академического статуса студента
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='academic_standings', verbose_name=_('Студент'))
    
    # Тип статуса
    STATUS_TYPES = (
        ('good', _('Хорошая успеваемость')),
        ('warning', _('Предупреждение')),
        ('probation', _('Испытательный срок')),
        ('academic_leave', _('Академический отпуск')),
        ('risk_expulsion', _('Риск отчисления')),
        ('expulsion', _('Отчисление')),
        ('reinstated', _('Восстановлен')),
        ('graduated', _('Выпускник')),
        ('transferred', _('Переведен')),
    )
    status_type = models.CharField(_('Тип статуса'), max_length=20, choices=STATUS_TYPES)
    
    # Период действия
    start_date = models.DateField(_('Дата начала'), default=timezone.now)
    end_date = models.DateField(_('Дата окончания'), null=True, blank=True)
    
    # Причина изменения статуса
    reason = models.TextField(_('Причина'), blank=True)
    
    # Связь с периодом обучения
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='academic_standings', 
                                null=True, blank=True,
                                verbose_name=_('Семестр'))
    
    # Связь с документом-основанием
    document_number = models.CharField(_('Номер документа'), max_length=100, blank=True)
    document_date = models.DateField(_('Дата документа'), null=True, blank=True)
    
    # Кто изменил статус
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='changed_academic_standings', 
                                  null=True, blank=True,
                                  verbose_name=_('Кто изменил'))
    
    # Дополнительная информация
    comments = models.TextField(_('Комментарии'), blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('академический статус')
        verbose_name_plural = _('академические статусы')
        ordering = ['student', '-start_date']
    
    def __str__(self):
        return f"{self.student} - {self.get_status_type_display()} ({self.start_date})"
    
    @property
    def is_active(self):
        """Проверяет, активен ли статус в текущую дату"""
        today = timezone.now().date()
        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today
    
    def is_active(self, obj):
        """Проверяет, активен ли статус в текущую дату"""
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = _("Активен")


class Scholarship(models.Model):
    """
    Модель стипендии
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    
    # Тип стипендии
    SCHOLARSHIP_TYPES = (
        ('academic', _('Академическая')),
        ('social', _('Социальная')),
        ('named', _('Именная')),
        ('president', _('Президентская')),
        ('government', _('Правительственная')),
        ('other', _('Другая')),
    )
    scholarship_type = models.CharField(_('Тип стипендии'), max_length=20, choices=SCHOLARSHIP_TYPES)
    
    # Сумма стипендии
    amount = models.DecimalField(_('Сумма'), max_digits=10, decimal_places=2)
    
    # Критерии получения
    gpa_requirement = models.DecimalField(_('Требуемый средний балл'), max_digits=5, decimal_places=2, 
                                         null=True, blank=True)
    attendance_requirement = models.DecimalField(_('Требуемый процент посещаемости'), 
                                               max_digits=5, decimal_places=2, 
                                               null=True, blank=True)
    
    # Метаданные
    is_active = models.BooleanField(_('Активна'), default=True)
    
    class Meta:
        verbose_name = _('стипендия')
        verbose_name_plural = _('стипендии')
    
    def __str__(self):
        return f"{self.name} ({self.get_scholarship_type_display()}): {self.amount}"


class ScholarshipAssignment(models.Model):
    """
    Модель назначения стипендии студенту
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='scholarships', verbose_name=_('Студент'))
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE, 
                                   related_name='assignments', verbose_name=_('Стипендия'))
    
    # Период назначения
    start_date = models.DateField(_('Дата начала'))
    end_date = models.DateField(_('Дата окончания'))
    
    # Семестр, за который назначена
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='scholarships', verbose_name=_('Семестр'))
    
    # Документ-основание
    document_number = models.CharField(_('Номер приказа'), max_length=100)
    document_date = models.DateField(_('Дата приказа'))
    
    # Статус назначения
    STATUS_CHOICES = (
        ('pending', _('Ожидает')),
        ('active', _('Активна')),
        ('suspended', _('Приостановлена')),
        ('terminated', _('Прекращена')),
        ('completed', _('Завершена')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Причина изменения статуса
    status_reason = models.TextField(_('Причина изменения статуса'), blank=True)
    
    # Фактическая сумма (может отличаться от стандартной)
    amount = models.DecimalField(_('Фактическая сумма'), max_digits=10, decimal_places=2, 
                                null=True, blank=True)
    
    # Кто создал запись
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='assigned_scholarships', 
                                   null=True, blank=True,
                                   verbose_name=_('Кто назначил'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('назначение стипендии')
        verbose_name_plural = _('назначения стипендий')
        ordering = ['student', '-start_date']
    
    def __str__(self):
        return f"{self.student} - {self.scholarship.name} ({self.start_date} - {self.end_date})"
    
    @property
    def is_active(self):
        """Проверяет, активно ли назначение в текущую дату"""
        today = timezone.now().date()
        return (self.status == 'active' and 
                self.start_date <= today <= self.end_date)
    
    def save(self, *args, **kwargs):
        # Если фактическая сумма не указана, используем стандартную
        if self.amount is None:
            self.amount = self.scholarship.amount
        
        super().save(*args, **kwargs)


class AcademicDebt(models.Model):
    """
    Модель академической задолженности
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='academic_debts', verbose_name=_('Студент'))
    
    # Связь с предметом и семестром
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='academic_debts', verbose_name=_('Предмет'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='academic_debts', verbose_name=_('Семестр'))
    
    # Тип задолженности
    DEBT_TYPES = (
        ('exam', _('Экзамен')),
        ('credit', _('Зачет')),
        ('course_work', _('Курсовая работа')),
        ('practice', _('Практика')),
        ('attendance', _('Посещаемость')),
        ('other', _('Другое')),
    )
    debt_type = models.CharField(_('Тип задолженности'), max_length=20, choices=DEBT_TYPES)
    
    # Описание задолженности
    description = models.TextField(_('Описание'), blank=True)
    
    # Даты
    deadline = models.DateField(_('Срок погашения'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    # Статус
    STATUS_CHOICES = (
        ('active', _('Активна')),
        ('extended', _('Продлена')),
        ('cleared', _('Погашена')),
        ('expired', _('Просрочена')),
        ('waived', _('Аннулирована')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Информация о погашении
    cleared_at = models.DateField(_('Дата погашения'), null=True, blank=True)
    grade_sheet_item = models.ForeignKey(GradeSheetItem, on_delete=models.SET_NULL, 
                                        related_name='debt_clearance', 
                                        null=True, blank=True,
                                        verbose_name=_('Запись в ведомости'))
    
    # Кто создал запись
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='created_debts', 
                                  null=True, blank=True,
                                  verbose_name=_('Кто создал'))
    
    class Meta:
        verbose_name = _('академическая задолженность')
        verbose_name_plural = _('академические задолженности')
        ordering = ['student', '-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.subject} ({self.get_debt_type_display()})"


class RetakePermission(models.Model):
    """
    Модель разрешения на пересдачу
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='retake_permissions', verbose_name=_('Студент'))
    academic_debt = models.ForeignKey(AcademicDebt, on_delete=models.SET_NULL, 
                                     related_name='retake_permissions', 
                                     null=True, blank=True,
                                     verbose_name=_('Академическая задолженность'))
    
    # Связь с предметом и семестром
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='retake_permissions', verbose_name=_('Предмет'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='retake_permissions', verbose_name=_('Семестр'))
    
    # Номер попытки
    attempt_number = models.PositiveSmallIntegerField(_('Номер попытки'), default=1)
    
    # Дата выдачи и срок действия
    issue_date = models.DateField(_('Дата выдачи'), default=timezone.now)
    expiration_date = models.DateField(_('Срок действия до'))
    
    # Документ-основание
    document_number = models.CharField(_('Номер документа'), max_length=100, blank=True)
    
    # Статус
    STATUS_CHOICES = (
        ('issued', _('Выдано')),
        ('used', _('Использовано')),
        ('expired', _('Истекло')),
        ('canceled', _('Аннулировано')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='issued')
    
    # Связь с экзаменом/зачетом или с ведомостью
    exam = models.ForeignKey('schedule.ExamSchedule', on_delete=models.SET_NULL, 
                            null=True, blank=True,
                            related_name='retake_permissions', verbose_name=_('Экзамен/зачет'))
    grade_sheet = models.ForeignKey(GradeSheet, on_delete=models.SET_NULL, 
                                   null=True, blank=True,
                                   related_name='retake_permissions', verbose_name=_('Ведомость'))
    
    # Результат пересдачи
    grade_sheet_item = models.OneToOneField(GradeSheetItem, on_delete=models.SET_NULL, 
                                           null=True, blank=True,
                                           related_name='retake_permission', 
                                           verbose_name=_('Запись в ведомости'))
    
    # Кто создал и одобрил
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='created_retake_permissions', 
                                  null=True, blank=True,
                                  verbose_name=_('Кто создал'))
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='approved_retake_permissions', 
                                   null=True, blank=True,
                                   verbose_name=_('Кто утвердил'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('разрешение на пересдачу')
        verbose_name_plural = _('разрешения на пересдачу')
        ordering = ['student', '-issue_date', 'subject']
    
    def __str__(self):
        return f"Разрешение на пересдачу: {self.student} - {self.subject} (Попытка {self.attempt_number})"


class IndividualPlan(models.Model):
    """
    Модель индивидуального учебного плана
    """
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, 
                               related_name='individual_plans', verbose_name=_('Студент'))
    
    # Основа для плана
    base_academic_plan = models.ForeignKey('university_structure.AcademicPlan', on_delete=models.CASCADE, 
                                          related_name='individual_plans', 
                                          verbose_name=_('Базовый учебный план'))
    
    # Период действия
    start_date = models.DateField(_('Дата начала'))
    end_date = models.DateField(_('Дата окончания'))
    
    # Документ-основание
    document_number = models.CharField(_('Номер приказа'), max_length=100)
    document_date = models.DateField(_('Дата приказа'))
    
    # Описание и обоснование
    reason = models.TextField(_('Причина создания'))
    description = models.TextField(_('Описание изменений'))
    
    # Статус
    STATUS_CHOICES = (
        ('draft', _('Черновик')),
        ('pending_approval', _('Ожидает утверждения')),
        ('approved', _('Утвержден')),
        ('active', _('Активен')),
        ('completed', _('Завершен')),
        ('canceled', _('Отменен')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Кто создал и утвердил
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='created_individual_plans', 
                                  null=True, blank=True,
                                  verbose_name=_('Кто создал'))
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='approved_individual_plans', 
                                   null=True, blank=True,
                                   verbose_name=_('Кто утвердил'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('индивидуальный учебный план')
        verbose_name_plural = _('индивидуальные учебные планы')
        ordering = ['student', '-start_date']
    
    def __str__(self):
        return f"ИУП: {self.student} ({self.start_date} - {self.end_date})"

class IndividualPlanItem(models.Model):
    """
    Модель элемента индивидуального учебного плана
    """
    individual_plan = models.ForeignKey(IndividualPlan, on_delete=models.CASCADE, 
                                       related_name='items', verbose_name=_('Индивидуальный план'))
    
    # Связь с предметом учебного плана
    base_plan_subject = models.ForeignKey('university_structure.AcademicPlanSubject', 
                                         on_delete=models.CASCADE, 
                                         related_name='individual_plan_items', 
                                         verbose_name=_('Предмет базового плана'),
                                         null=True, blank=True)
    
    # Или новый предмет
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='individual_plan_items', 
                               verbose_name=_('Предмет'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='individual_plan_items', 
                                verbose_name=_('Семестр'))
    
    # Изменения в нагрузке
    lectures_hours = models.PositiveSmallIntegerField(_('Лекции'), default=0)
    seminars_hours = models.PositiveSmallIntegerField(_('Семинары'), default=0)
    labs_hours = models.PositiveSmallIntegerField(_('Лабораторные'), default=0)
    practices_hours = models.PositiveSmallIntegerField(_('Практики'), default=0)
    self_study_hours = models.PositiveSmallIntegerField(_('Самостоятельная работа'), default=0)
    
    # Форма контроля и зачетные единицы
    credits = models.PositiveSmallIntegerField(_('Зачетные единицы'))
    CONTROL_FORMS = (
        ('exam', _('Экзамен')),
        ('credit', _('Зачет')),
        ('credit_grade', _('Зачет с оценкой')),
        ('coursework', _('Курсовая работа')),
        ('coursework_project', _('Курсовой проект')),
        ('practice', _('Практика')),
    )
    control_form = models.CharField(_('Форма контроля'), max_length=20, choices=CONTROL_FORMS)
    
    # Тип изменения
    CHANGE_TYPES = (
        ('replace', _('Замена предмета')),
        ('move', _('Перенос в другой семестр')),
        ('add', _('Добавление предмета')),
        ('remove', _('Удаление предмета')),
        ('modify', _('Изменение параметров')),
    )
    change_type = models.CharField(_('Тип изменения'), max_length=20, choices=CHANGE_TYPES)
    
    # Обоснование изменения
    reason = models.TextField(_('Обоснование изменения'), blank=True)
    
    class Meta:
        verbose_name = _('элемент индивидуального плана')
        verbose_name_plural = _('элементы индивидуального плана')
        ordering = ['individual_plan', 'semester', 'subject']
    
    def __str__(self):
        return f"{self.subject} ({self.get_change_type_display()})"
    
    @property
    def total_hours(self):
        """Общее количество часов по дисциплине в семестре"""
        return (self.lectures_hours + self.seminars_hours + self.labs_hours + 
                self.practices_hours + self.self_study_hours)


class GradeImport(models.Model):
    """
    Модель импорта оценок из внешних систем
    """
    # Источник импорта
    SOURCE_CHOICES = (
        ('csv', _('CSV файл')),
        ('excel', _('Excel файл')),
        ('api', _('Внешний API')),
        ('manual', _('Ручной ввод')),
        ('other', _('Другое')),
    )
    source = models.CharField(_('Источник'), max_length=20, choices=SOURCE_CHOICES)
    
    # Метаданные
    filename = models.CharField(_('Имя файла'), max_length=255, blank=True)
    file = models.FileField(_('Файл'), upload_to='grade_imports/', null=True, blank=True)
    
    # Информация об импорте
    imported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   related_name='grade_imports', 
                                   null=True, blank=True,
                                   verbose_name=_('Кто импортировал'))
    import_date = models.DateTimeField(_('Дата импорта'), auto_now_add=True)
    
    # Статус импорта
    STATUS_CHOICES = (
        ('pending', _('Ожидает обработки')),
        ('processing', _('Обрабатывается')),
        ('completed', _('Завершен')),
        ('failed', _('Ошибка')),
        ('partially_completed', _('Частично завершен')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Статистика
    total_records = models.PositiveIntegerField(_('Всего записей'), default=0)
    processed_records = models.PositiveIntegerField(_('Обработано записей'), default=0)
    successful_records = models.PositiveIntegerField(_('Успешно импортировано'), default=0)
    failed_records = models.PositiveIntegerField(_('Ошибки импорта'), default=0)
    
    # Журнал ошибок
    error_log = models.TextField(_('Журнал ошибок'), blank=True)
    
    class Meta:
        verbose_name = _('импорт оценок')
        verbose_name_plural = _('импорты оценок')
        ordering = ['-import_date']
    
    def __str__(self):
        return f"Импорт {self.id} от {self.import_date}"


class GradeImportItem(models.Model):
    """
    Модель записи импорта оценки
    """
    grade_import = models.ForeignKey(GradeImport, on_delete=models.CASCADE, 
                                    related_name='items', verbose_name=_('Импорт'))
    
    # Данные оценки
    student_id = models.CharField(_('ID студента'), max_length=50)
    subject_code = models.CharField(_('Код предмета'), max_length=50)
    semester_id = models.CharField(_('ID семестра'), max_length=50)
    grade_value = models.CharField(_('Значение оценки'), max_length=20)
    grade_type = models.CharField(_('Тип оценки'), max_length=50)
    grade_date = models.DateField(_('Дата оценки'), null=True, blank=True)
    
    # Дополнительные данные
    additional_data = models.JSONField(_('Дополнительные данные'), default=dict, blank=True)
    
    # Статус обработки
    STATUS_CHOICES = (
        ('pending', _('Ожидает обработки')),
        ('processed', _('Обработана')),
        ('error', _('Ошибка')),
        ('skipped', _('Пропущена')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Связь с созданной оценкой
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, 
                             null=True, blank=True,
                             related_name='import_item', verbose_name=_('Созданная оценка'))
    
    # Сообщение об ошибке
    error_message = models.TextField(_('Сообщение об ошибке'), blank=True)
    
    class Meta:
        verbose_name = _('запись импорта оценки')
        verbose_name_plural = _('записи импорта оценок')
    
    def __str__(self):
        return f"Запись {self.id}: {self.student_id} - {self.subject_code} - {self.grade_value}"


class GradeExport(models.Model):
    """
    Модель экспорта оценок
    """
    # Формат экспорта
    FORMAT_CHOICES = (
        ('csv', _('CSV')),
        ('excel', _('Excel')),
        ('pdf', _('PDF')),
        ('json', _('JSON')),
        ('xml', _('XML')),
    )
    format = models.CharField(_('Формат'), max_length=10, choices=FORMAT_CHOICES)
    
    # Фильтры для экспорта
    group = models.ForeignKey('university_structure.Group', on_delete=models.SET_NULL, 
                             null=True, blank=True,
                             related_name='grade_exports', verbose_name=_('Группа'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               related_name='grade_exports', verbose_name=_('Студент'))
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               related_name='grade_exports', verbose_name=_('Предмет'))
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.SET_NULL, 
                                null=True, blank=True,
                                related_name='grade_exports', verbose_name=_('Семестр'))
    
    # Дополнительные параметры
    include_attendance = models.BooleanField(_('Включить посещаемость'), default=False)
    include_comments = models.BooleanField(_('Включить комментарии'), default=False)
    
    # Метаданные
    exported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True,
                                   related_name='grade_exports', verbose_name=_('Кто экспортировал'))
    export_date = models.DateTimeField(_('Дата экспорта'), auto_now_add=True)
    
    # Файл экспорта
    file = models.FileField(_('Файл'), upload_to='grade_exports/', null=True, blank=True)
    
    # Статус экспорта
    STATUS_CHOICES = (
        ('pending', _('В процессе')),
        ('completed', _('Завершен')),
        ('failed', _('Ошибка')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Статистика
    records_count = models.PositiveIntegerField(_('Количество записей'), default=0)
    
    class Meta:
        verbose_name = _('экспорт оценок')
        verbose_name_plural = _('экспорты оценок')
        ordering = ['-export_date']
    
    def __str__(self):
        return f"Экспорт {self.id} от {self.export_date}"


# Сигналы для автоматизации
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Grade)
def update_academic_performance_summary(sender, instance, **kwargs):
    """
    Обновляет сводку успеваемости студента при изменении оценки
    """
    # Получаем или создаем сводку для семестра
    summary, created = AcademicPerformanceSummary.objects.get_or_create(
        student=instance.student,
        period_type='semester',
        semester=instance.semester,
        defaults={
            'total_subjects': 0,
            'excellent_count': 0,
            'good_count': 0,
            'satisfactory_count': 0,
            'failed_count': 0,
            'gpa': 0,
            'total_credits': 0,
            'earned_credits': 0,
        }
    )
    
    # Обновляем статистику
    # В реальном проекте здесь должна быть более сложная логика
    # для учета всех оценок в семестре
    
    # Пример простого обновления для демонстрации
    if instance.grade_value.numeric_value >= 90:
        summary.excellent_count += 1
    elif instance.grade_value.numeric_value >= 75:
        summary.good_count += 1
    elif instance.grade_value.numeric_value >= 60:
        summary.satisfactory_count += 1
    else:
        summary.failed_count += 1
    
    # Пересчитываем общее количество предметов
    total_subjects = (summary.excellent_count + summary.good_count + 
                      summary.satisfactory_count + summary.failed_count)
    summary.total_subjects = total_subjects
    
    # Обновляем средний балл (простой пример)
    all_grades = Grade.objects.filter(
        student=instance.student,
        semester=instance.semester
    )
    
    total_value = 0
    grade_count = 0
    
    for grade in all_grades:
        total_value += grade.grade_value.numeric_value
        grade_count += 1
    
    if grade_count > 0:
        summary.gpa = total_value / grade_count
    
    # Сохраняем обновленную сводку
    summary.save()

@receiver(post_save, sender=Attendance)
def update_attendance_stats(sender, instance, **kwargs):
    """
    Обновляет статистику посещаемости в сводке успеваемости
    """
    # Получаем семестр из связанного занятия
    semester = instance.class_instance.schedule_item.schedule_template.semester
    
    # Получаем или создаем сводку для семестра
    summary, created = AcademicPerformanceSummary.objects.get_or_create(
        student=instance.student,
        period_type='semester',
        semester=semester,
        defaults={
            'total_subjects': 0,
            'excellent_count': 0,
            'good_count': 0,
            'satisfactory_count': 0,
            'failed_count': 0,
            'gpa': 0,
            'total_credits': 0,
            'earned_credits': 0,
            'total_classes': 0,
            'attended_classes': 0,
            'attendance_percentage': 0,
        }
    )
    
    # Пересчитываем статистику посещаемости
    all_attendance = Attendance.objects.filter(
        student=instance.student,
        class_instance__schedule_item__schedule_template__semester=semester
    )
    
    total_classes = all_attendance.count()
    attended_classes = all_attendance.filter(status='present').count()
    
    summary.total_classes = total_classes
    summary.attended_classes = attended_classes
    
    if total_classes > 0:
        summary.attendance_percentage = (attended_classes / total_classes) * 100
    
    # Сохраняем обновленную сводку
    summary.save()

@receiver(post_save, sender=AcademicDebt)
def update_student_academic_standing(sender, instance, **kwargs):
    """
    Обновляет академический статус студента при изменении задолженности
    """
    # Проверяем количество активных задолженностей
    active_debts_count = AcademicDebt.objects.filter(
        student=instance.student,
        status__in=['active', 'extended', 'expired']
    ).count()
    
    # Определяем статус на основе количества задолженностей
    if active_debts_count == 0:
        # Если нет задолженностей, статус "хорошая успеваемость"
        status_type = 'good'
    elif active_debts_count <= 2:
        # Если 1-2 задолженности, статус "предупреждение"
        status_type = 'warning'
    elif active_debts_count <= 4:
        # Если 3-4 задолженности, статус "испытательный срок"
        status_type = 'probation'
    else:
        # Если более 4 задолженностей, статус "риск отчисления"
        status_type = 'risk_expulsion'
    
    # Получаем текущий активный статус
    current_standing = AcademicStanding.objects.filter(
        student=instance.student,
        end_date__isnull=True
    ).order_by('-start_date').first()
    
    # Если статус изменился, создаем новую запись
    if not current_standing or current_standing.status_type != status_type:
        # Закрываем текущий статус, если он есть
        if current_standing:
            current_standing.end_date = timezone.now().date()
            current_standing.save()
        
        # Создаем новый статус
        AcademicStanding.objects.create(
            student=instance.student,
            status_type=status_type,
            start_date=timezone.now().date(),
            reason=_('Автоматическое обновление на основе академических задолженностей'),
            semester=instance.semester
        )

@receiver(post_save, sender=GradeSheet)
def create_grade_sheet_items(sender, instance, created, **kwargs):
    """
    Создает записи в ведомости для всех студентов группы при создании ведомости
    """
    if created:
        # Получаем всех студентов группы
        students = instance.group.students.all()
        
        # Создаем записи для каждого студента
        for student in students:
            GradeSheetItem.objects.create(
                grade_sheet=instance,
                student=student,
                status='not_graded'
            )

@receiver(post_save, sender=Grade)
def check_academic_debt_clearance(sender, instance, **kwargs):
    """
    Проверяет, погашена ли задолженность при изменении оценки
    """
    # Проверяем, является ли оценка проходной
    if instance.is_passing:
        # Ищем активные задолженности по этому предмету
        debts = AcademicDebt.objects.filter(
            student=instance.student,
            subject=instance.subject,
            semester=instance.semester,
            status__in=['active', 'extended']
        )
        
        # Если найдены задолженности, отмечаем их как погашенные
        for debt in debts:
            debt.status = 'cleared'
            debt.cleared_at = instance.date
            debt.save()