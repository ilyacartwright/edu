from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
import datetime


class TimeSlot(models.Model):
    """
    Модель временного слота для занятий
    """
    number = models.PositiveSmallIntegerField(_('Номер пары'))
    start_time = models.TimeField(_('Время начала'))
    end_time = models.TimeField(_('Время окончания'))
    break_after = models.PositiveSmallIntegerField(_('Перерыв после (мин)'), default=10)
    
    class Meta:
        verbose_name = _('временной слот')
        verbose_name_plural = _('временные слоты')
        ordering = ['number']
    
    def __str__(self):
        return f"{self.number} пара ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
    
    def clean(self):
        """Проверка корректности времени начала и окончания"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class TimeSlot(models.Model):
    """
    Модель временного слота для занятий
    """
    number = models.PositiveSmallIntegerField(_('Номер пары'))
    start_time = models.TimeField(_('Время начала'))
    end_time = models.TimeField(_('Время окончания'))
    break_after = models.PositiveSmallIntegerField(_('Перерыв после (мин)'), default=10)
    
    class Meta:
        verbose_name = _('временной слот')
        verbose_name_plural = _('временные слоты')
        ordering = ['number']
    
    def __str__(self):
        return f"{self.number} пара ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
    
    def clean(self):
        """Проверка корректности времени начала и окончания"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_('Время начала должно быть меньше времени окончания'))

class ClassType(models.Model):
    """
    Модель типа занятия (лекция, семинар, лабораторная и т.д.)
    """
    name = models.CharField(_('Название'), max_length=100)
    short_name = models.CharField(_('Сокращение'), max_length=10)
    color = models.CharField(_('Цвет'), max_length=7, help_text="HEX-код цвета", default="#FFFFFF")
    
    class Meta:
        verbose_name = _('тип занятия')
        verbose_name_plural = _('типы занятий')
    
    def __str__(self):
        return self.name

class ScheduleTemplate(models.Model):
    """
    Модель шаблона расписания (для регулярных занятий)
    """
    name = models.CharField(_('Название'), max_length=100)
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='schedule_templates')
    is_active = models.BooleanField(_('Активен'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('шаблон расписания')
        verbose_name_plural = _('шаблоны расписания')
    
    def __str__(self):
        return f"{self.name} - {self.semester}"

class ScheduleItem(models.Model):
    """
    Модель элемента расписания (шаблон для регулярных занятий)
    """
    schedule_template = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, related_name='items')
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='schedule_items')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, 
                               related_name='schedule_items')
    class_type = models.ForeignKey(ClassType, on_delete=models.CASCADE, related_name='schedule_items')
    
    # Для каких групп/подгрупп занятие
    groups = models.ManyToManyField('university_structure.Group', related_name='schedule_items')
    subgroups = models.ManyToManyField('university_structure.Subgroup', related_name='schedule_items', blank=True)
    
    # Время и место
    room = models.ForeignKey('university_structure.Room', on_delete=models.CASCADE, 
                            related_name='schedule_items')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='schedule_items')
    
    WEEKDAYS = (
        (0, _('Понедельник')),
        (1, _('Вторник')),
        (2, _('Среда')),
        (3, _('Четверг')),
        (4, _('Пятница')),
        (5, _('Суббота')),
        (6, _('Воскресенье')),
    )
    weekday = models.PositiveSmallIntegerField(_('День недели'), choices=WEEKDAYS)
    
    # Периодичность
    WEEK_TYPES = (
        ('every', _('Каждую неделю')),
        ('odd', _('По нечетным')),
        ('even', _('По четным')),
    )
    week_type = models.CharField(_('Тип недели'), max_length=10, choices=WEEK_TYPES, default='every')
    
    # Комментарий
    comment = models.TextField(_('Комментарий'), blank=True)
    
    class Meta:
        verbose_name = _('элемент расписания')
        verbose_name_plural = _('элементы расписания')
        constraints = [
            models.UniqueConstraint(
                fields=['schedule_template', 'room', 'time_slot', 'weekday'],
                condition=models.Q(week_type='every'),
                name='unique_room_timeslot_weekday_every'
            ),
            models.UniqueConstraint(
                fields=['schedule_template', 'room', 'time_slot', 'weekday', 'week_type'],
                condition=~models.Q(week_type='every'),
                name='unique_room_timeslot_weekday_week_type'
            ),
        ]
    
    def __str__(self):
        group_names = ", ".join([group.name for group in self.groups.all()])
        return f"{self.subject.name} - {self.get_weekday_display()} {self.time_slot} - {group_names}"
    
    def clean(self):
        """Проверка на конфликты расписания"""
        if not self.id and self.room and self.time_slot and self.weekday is not None and self.schedule_template:
            # Проверяем конфликты в расписании для этой же аудитории в это же время
            conflicts = ScheduleItem.objects.filter(
                schedule_template=self.schedule_template,
                room=self.room,
                time_slot=self.time_slot,
                weekday=self.weekday
            )
            
            if self.week_type == 'every':
                # "Каждую неделю" конфликтует с любым другим типом
                if conflicts.exists():
                    raise ValidationError(
                        _('В это время в данной аудитории уже назначено занятие')
                    )
            else:
                # "По четным" и "По нечетным" не должны пересекаться между собой
                if conflicts.filter(week_type='every').exists():
                    raise ValidationError(
                        _('В это время в данной аудитории уже назначено еженедельное занятие')
                    )
                if conflicts.filter(week_type=self.week_type).exists():
                    raise ValidationError(
                        _('В это время в данной аудитории уже назначено занятие с таким же типом недели')
                    )
            
            # Проверяем конфликты по преподавателю
            teacher_conflicts = ScheduleItem.objects.filter(
                schedule_template=self.schedule_template,
                teacher=self.teacher,
                time_slot=self.time_slot,
                weekday=self.weekday
            )
            
            if self.week_type == 'every':
                if teacher_conflicts.exists():
                    raise ValidationError(
                        _('Преподаватель уже ведет занятие в это время')
                    )
            else:
                if teacher_conflicts.filter(week_type='every').exists():
                    raise ValidationError(
                        _('Преподаватель уже ведет еженедельное занятие в это время')
                    )
                if teacher_conflicts.filter(week_type=self.week_type).exists():
                    raise ValidationError(
                        _('Преподаватель уже ведет занятие в это время с таким же типом недели')
                    )
            
            # Проверяем конфликты по группам
            if self.pk is not None:  # Если это новая запись, у нас еще нет связанных групп
                for group in self.groups.all():
                    group_conflicts = ScheduleItem.objects.filter(
                        schedule_template=self.schedule_template,
                        groups=group,
                        time_slot=self.time_slot,
                        weekday=self.weekday
                    ).exclude(pk=self.pk)
                    
                    if self.week_type == 'every':
                        if group_conflicts.exists():
                            raise ValidationError(
                                _(f'Группа {group.name} уже имеет занятие в это время')
                            )
                    else:
                        if group_conflicts.filter(week_type='every').exists():
                            raise ValidationError(
                                _(f'Группа {group.name} уже имеет еженедельное занятие в это время')
                            )
                        if group_conflicts.filter(week_type=self.week_type).exists():
                            raise ValidationError(
                                _(f'Группа {group.name} уже имеет занятие в это время с таким же типом недели')
                            )

class Class(models.Model):
    """
    Модель конкретного занятия (экземпляр на определенную дату)
    """
    schedule_item = models.ForeignKey(ScheduleItem, on_delete=models.CASCADE, 
                                     related_name='classes', null=True, blank=True)
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, related_name='classes')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, related_name='classes')
    class_type = models.ForeignKey(ClassType, on_delete=models.CASCADE, related_name='classes')
    
    # Для каких групп/подгрупп занятие
    groups = models.ManyToManyField('university_structure.Group', related_name='classes')
    subgroups = models.ManyToManyField('university_structure.Subgroup', related_name='classes', blank=True)
    
    # Время и место
    date = models.DateField(_('Дата'))
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='classes')
    room = models.ForeignKey('university_structure.Room', on_delete=models.CASCADE, related_name='classes')
    
    # Статус занятия
    STATUS_CHOICES = (
        ('scheduled', _('Запланировано')),
        ('canceled', _('Отменено')),
        ('rescheduled', _('Перенесено')),
        ('completed', _('Проведено')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Дополнительная информация
    topic = models.CharField(_('Тема'), max_length=255, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    
    # Для отмененных/перенесенных занятий
    cancellation_reason = models.TextField(_('Причина отмены/переноса'), blank=True)
    
    # Если это перенесенное занятие, ссылка на оригинал
    original_class = models.ForeignKey('self', on_delete=models.SET_NULL, 
                                      null=True, blank=True, related_name='rescheduled_to')
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('занятие')
        verbose_name_plural = _('занятия')
        ordering = ['date', 'time_slot__start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'time_slot', 'room'],
                condition=~models.Q(status='canceled'),
                name='unique_date_timeslot_room'
            ),
        ]
    
    def __str__(self):
        group_names = ", ".join([group.name for group in self.groups.all()])
        return f"{self.subject.name} - {self.date} {self.time_slot} - {group_names} ({self.get_status_display()})"
    
    def clean(self):
        """Проверка на конфликты расписания"""
        if not self.id and self.room and self.time_slot and self.date:
            # Проверяем конфликты в расписании для этой же аудитории в это же время
            conflicts = Class.objects.filter(
                date=self.date,
                time_slot=self.time_slot,
                room=self.room
            ).exclude(status='canceled')
            
            if conflicts.exists():
                raise ValidationError(
                    _('В это время в данной аудитории уже назначено занятие')
                )
            
            # Проверяем конфликты по преподавателю
            teacher_conflicts = Class.objects.filter(
                date=self.date,
                time_slot=self.time_slot,
                teacher=self.teacher
            ).exclude(status='canceled')
            
            if teacher_conflicts.exists():
                raise ValidationError(
                    _('Преподаватель уже ведет занятие в это время')
                )
            
            # Проверка на конфликты по группам сделана только если объект уже сохранен
            if self.pk is not None:
                for group in self.groups.all():
                    group_conflicts = Class.objects.filter(
                        date=self.date,
                        time_slot=self.time_slot,
                        groups=group
                    ).exclude(status='canceled').exclude(pk=self.pk)
                    
                    if group_conflicts.exists():
                        raise ValidationError(
                            _(f'Группа {group.name} уже имеет занятие в это время')
                        )

class ScheduleChange(models.Model):
    """
    Модель изменения в расписании
    """
    affected_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='changes')
    
    CHANGE_TYPES = (
        ('cancel', _('Отмена')),
        ('reschedule', _('Перенос')),
        ('room_change', _('Смена аудитории')),
        ('teacher_change', _('Смена преподавателя')),
        ('other', _('Другое')),
    )
    change_type = models.CharField(_('Тип изменения'), max_length=20, choices=CHANGE_TYPES)
    
    description = models.TextField(_('Описание изменения'))
    
    # Для переноса или смены аудитории
    new_date = models.DateField(_('Новая дата'), null=True, blank=True)
    new_time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, 
                                     related_name='schedule_changes', null=True, blank=True)
    new_room = models.ForeignKey('university_structure.Room', on_delete=models.SET_NULL, 
                                related_name='schedule_changes', null=True, blank=True)
    
    # Для смены преподавателя
    new_teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                                   related_name='schedule_changes', null=True, blank=True)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='created_schedule_changes', null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    # Связанное новое занятие в случае переноса
    new_class = models.OneToOneField(Class, on_delete=models.SET_NULL, 
                                    related_name='original_change', 
                                    null=True, blank=True)
    
    # Статус уведомления об изменении
    is_notification_sent = models.BooleanField(_('Уведомление отправлено'), default=False)
    notification_sent_at = models.DateTimeField(_('Дата отправки уведомления'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('изменение в расписании')
        verbose_name_plural = _('изменения в расписании')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_change_type_display()} - {self.affected_class}"
    
    def save(self, *args, **kwargs):
        # Обновляем статус занятия в зависимости от типа изменения
        if self.change_type == 'cancel' and self.affected_class.status != 'canceled':
            self.affected_class.status = 'canceled'
            self.affected_class.cancellation_reason = self.description
            self.affected_class.save()
        elif self.change_type == 'reschedule' and self.affected_class.status != 'rescheduled':
            self.affected_class.status = 'rescheduled'
            self.affected_class.cancellation_reason = self.description
            self.affected_class.save()
        
        super().save(*args, **kwargs)

class DailyScheduleGeneration(models.Model):
    """
    Модель для отслеживания генерации ежедневного расписания
    """
    date = models.DateField(_('Дата'), unique=True)
    schedule_template = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, 
                                         related_name='daily_generations')
    is_generated = models.BooleanField(_('Сгенерировано'), default=False)
    generated_at = models.DateTimeField(_('Дата генерации'), null=True, blank=True)
    generated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                    related_name='generated_schedules', null=True, blank=True)
    
    class Meta:
        verbose_name = _('генерация ежедневного расписания')
        verbose_name_plural = _('генерации ежедневного расписания')
        ordering = ['-date']
    
    def __str__(self):
        return f"Генерация расписания на {self.date}"

class ConsultationSchedule(models.Model):
    """
    Модель расписания консультаций
    """
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, 
                               related_name='consultations')
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='consultations')
    
    WEEKDAYS = (
        (0, _('Понедельник')),
        (1, _('Вторник')),
        (2, _('Среда')),
        (3, _('Четверг')),
        (4, _('Пятница')),
        (5, _('Суббота')),
        (6, _('Воскресенье')),
    )
    weekday = models.PositiveSmallIntegerField(_('День недели'), choices=WEEKDAYS)
    
    start_time = models.TimeField(_('Время начала'))
    end_time = models.TimeField(_('Время окончания'))
    
    room = models.ForeignKey('university_structure.Room', on_delete=models.CASCADE, 
                            related_name='consultations')
    
    # Для каких групп консультация (опционально)
    groups = models.ManyToManyField('university_structure.Group', related_name='consultations', blank=True)
    
    # Периодичность
    WEEK_TYPES = (
        ('every', _('Каждую неделю')),
        ('odd', _('По нечетным')),
        ('even', _('По четным')),
    )
    week_type = models.CharField(_('Тип недели'), max_length=10, choices=WEEK_TYPES, default='every')
    
    is_active = models.BooleanField(_('Активна'), default=True)
    comment = models.TextField(_('Комментарий'), blank=True)
    
    class Meta:
        verbose_name = _('расписание консультаций')
        verbose_name_plural = _('расписания консультаций')
    
    def __str__(self):
        return f"Консультация {self.teacher} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        """Проверка корректности времени и конфликтов"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_('Время начала должно быть меньше времени окончания'))
        
        # Проверка на конфликты с другими консультациями в той же аудитории
        if not self.id and self.room and self.weekday is not None and self.start_time and self.end_time:
            conflicts = ConsultationSchedule.objects.filter(
                room=self.room,
                weekday=self.weekday,
                semester=self.semester
            ).filter(
                models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
            )
            
            if self.week_type == 'every':
                if conflicts.exists():
                    raise ValidationError(
                        _('В это время в данной аудитории уже назначена консультация')
                    )
            else:
                if conflicts.filter(week_type='every').exists():
                    raise ValidationError(
                        _('В это время в данной аудитории уже назначена еженедельная консультация')
                    )
                if conflicts.filter(week_type=self.week_type).exists():
                    raise ValidationError(
                        _('В это время в данной аудитории уже назначена консультация с таким же типом недели')
                    )
            
            # Проверка на конфликты с другими консультациями у того же преподавателя
            teacher_conflicts = ConsultationSchedule.objects.filter(
                teacher=self.teacher,
                weekday=self.weekday,
                semester=self.semester
            ).filter(
                models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
            )
            
            if self.week_type == 'every':
                if teacher_conflicts.exists():
                    raise ValidationError(
                        _('Преподаватель уже проводит консультацию в это время')
                    )
            else:
                if teacher_conflicts.filter(week_type='every').exists():
                    raise ValidationError(
                        _('Преподаватель уже проводит еженедельную консультацию в это время')
                    )
                if teacher_conflicts.filter(week_type=self.week_type).exists():
                    raise ValidationError(
                        _('Преподаватель уже проводит консультацию в это время с таким же типом недели')
                    )

class ExamSchedule(models.Model):
    """
    Модель расписания экзаменов
    """
    subject = models.ForeignKey('university_structure.Subject', on_delete=models.CASCADE, 
                               related_name='exams')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, 
                               related_name='exams')
    groups = models.ManyToManyField('university_structure.Group', related_name='exams')
    
    # Время и место
    date = models.DateField(_('Дата'))
    start_time = models.TimeField(_('Время начала'))
    end_time = models.TimeField(_('Время окончания'))
    room = models.ForeignKey('university_structure.Room', on_delete=models.CASCADE, 
                            related_name='exams')
    
    # Тип экзамена
    EXAM_TYPES = (
        ('exam', _('Экзамен')),
        ('credit', _('Зачет')),
        ('credit_grade', _('Дифференцированный зачет')),
        ('consultation', _('Консультация перед экзаменом')),
    )
    exam_type = models.CharField(_('Тип экзамена'), max_length=20, choices=EXAM_TYPES)
    
    # Статус
    STATUS_CHOICES = (
        ('scheduled', _('Запланирован')),
        ('canceled', _('Отменен')),
        ('rescheduled', _('Перенесен')),
        ('completed', _('Проведен')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    semester = models.ForeignKey('university_structure.Semester', on_delete=models.CASCADE, 
                                related_name='exams')
    
    # Дополнительная информация
    description = models.TextField(_('Описание'), blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('расписание экзамена')
        verbose_name_plural = _('расписание экзаменов')
        ordering = ['date', 'start_time']
    
    def __str__(self):
        group_names = ", ".join([group.name for group in self.groups.all()])
        return f"{self.get_exam_type_display()} {self.subject.name} - {self.date} - {group_names}"
    
    def clean(self):
        """Проверка корректности времени и конфликтов"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_('Время начала должно быть меньше времени окончания'))
        
        # Проверка, что дата входит в сессионный период семестра
        if self.date and self.semester:
            if not (self.semester.exam_start_date <= self.date <= self.semester.exam_end_date):
                # Консультации могут быть за несколько дней до начала сессии
                if self.exam_type != 'consultation' or self.date < (self.semester.exam_start_date - datetime.timedelta(days=7)):
                    raise ValidationError(_('Дата экзамена должна входить в период сессии'))
        
        # Проверка на конфликты с другими экзаменами в той же аудитории
        if not self.id and self.room and self.date and self.start_time and self.end_time:
            conflicts = ExamSchedule.objects.filter(
                room=self.room,
                date=self.date
            ).filter(
                models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
            ).exclude(status__in=['canceled', 'rescheduled'])
            
            if conflicts.exists():
                raise ValidationError(
                    _('В это время в данной аудитории уже назначен экзамен')
                )
            
            # Проверка на конфликты с другими экзаменами у того же преподавателя
            teacher_conflicts = ExamSchedule.objects.filter(
                teacher=self.teacher,
                date=self.date
            ).filter(
                models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
            ).exclude(status__in=['canceled', 'rescheduled'])
            
            if teacher_conflicts.exists():
                raise ValidationError(
                    _('Преподаватель уже проводит экзамен в это время')
                )
            
            # Проверка на конфликты для групп
            if self.pk is not None:  # Проверяем только для существующих записей
                for group in self.groups.all():
                    group_conflicts = ExamSchedule.objects.filter(
                        groups=group,
                        date=self.date
                    ).filter(
                        models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
                    ).exclude(status__in=['canceled', 'rescheduled']).exclude(pk=self.pk)
                    
                    if group_conflicts.exists():
                        raise ValidationError(
                            _(f'Группа {group.name} уже имеет экзамен в это время')
                        )

class ScheduleAdditionalInfo(models.Model):
    """
    Модель для хранения дополнительной информации к расписанию
    """
    class_instance = models.OneToOneField(Class, on_delete=models.CASCADE, related_name='additional_info')
    
    # Дополнительные материалы к занятию
    materials = models.ManyToManyField('study_materials.Material', blank=True, 
                                     related_name='scheduled_classes')
    
    # Домашнее задание, относящееся к этому занятию
    # homework = models.ForeignKey('homework.Homework', on_delete=models.SET_NULL, 
                            #    related_name='scheduled_classes', null=True, blank=True)
    
    # Онлайн-курс, связанный с занятием
    course_element = models.ForeignKey('courses.CourseElement', on_delete=models.SET_NULL, 
                                     related_name='scheduled_classes', null=True, blank=True)
    
    # Флаг для обозначения онлайн-занятия
    is_online = models.BooleanField(_('Онлайн-занятие'), default=False)
    
    # Ссылка на онлайн-конференцию
    online_meeting_url = models.URLField(_('Ссылка на онлайн-занятие'), blank=True)
    
    # Требуемое предварительное чтение/подготовка к занятию
    preparation_instructions = models.TextField(_('Инструкции по подготовке'), blank=True)
    
    class Meta:
        verbose_name = _('дополнительная информация к занятию')
        verbose_name_plural = _('дополнительная информация к занятиям')
    
    def __str__(self):
        return f"Доп. информация: {self.class_instance}"

class ScheduleNotification(models.Model):
    """
    Модель уведомлений о расписании
    """
    NOTIFICATION_TYPES = (
        ('class_reminder', _('Напоминание о занятии')),
        ('class_change', _('Изменение в расписании')),
        ('exam_reminder', _('Напоминание об экзамене')),
        ('consultation_reminder', _('Напоминание о консультации')),
    )
    notification_type = models.CharField(_('Тип уведомления'), max_length=21, choices=NOTIFICATION_TYPES)
    
    # Связь с различными сущностями расписания
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, 
                                      related_name='notifications', null=True, blank=True)
    exam = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, 
                            related_name='notifications', null=True, blank=True)
    consultation = models.ForeignKey(ConsultationSchedule, on_delete=models.CASCADE, 
                                    related_name='notifications', null=True, blank=True)
    schedule_change = models.ForeignKey(ScheduleChange, on_delete=models.CASCADE, 
                                       related_name='notifications', null=True, blank=True)
    
    # Получатели уведомления
    recipients = models.ManyToManyField('accounts.User', related_name='schedule_notifications')
    
    # Содержание уведомления
    title = models.CharField(_('Заголовок'), max_length=200)
    message = models.TextField(_('Сообщение'))
    
    # Время отправки и статус
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    scheduled_for = models.DateTimeField(_('Запланировано на'))
    sent_at = models.DateTimeField(_('Отправлено'), null=True, blank=True)
    is_sent = models.BooleanField(_('Отправлено'), default=False)
    
    class Meta:
        verbose_name = _('уведомление о расписании')
        verbose_name_plural = _('уведомления о расписании')
        ordering = ['-scheduled_for']
    
    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"

class ScheduleExport(models.Model):
    """
    Модель для отслеживания экспорта расписания
    """
    EXPORT_TYPES = (
        ('student', _('Расписание студента')),
        ('group', _('Расписание группы')),
        ('teacher', _('Расписание преподавателя')),
        ('room', _('Расписание аудитории')),
        ('department', _('Расписание кафедры')),
        ('faculty', _('Расписание факультета')),
    )
    export_type = models.CharField(_('Тип экспорта'), max_length=20, choices=EXPORT_TYPES)
    
    FORMAT_TYPES = (
        ('pdf', _('PDF')),
        ('excel', _('Excel')),
        ('ical', _('iCalendar')),
        ('json', _('JSON')),
    )
    format_type = models.CharField(_('Формат'), max_length=10, choices=FORMAT_TYPES)
    
    # Фильтры для экспорта
    start_date = models.DateField(_('Дата начала'))
    end_date = models.DateField(_('Дата окончания'))
    
    # Связи с сущностями
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.SET_NULL, 
                               related_name='schedule_exports', null=True, blank=True)
    group = models.ForeignKey('university_structure.Group', on_delete=models.SET_NULL, 
                             related_name='schedule_exports', null=True, blank=True)
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                               related_name='schedule_exports', null=True, blank=True)
    room = models.ForeignKey('university_structure.Room', on_delete=models.SET_NULL, 
                            related_name='schedule_exports', null=True, blank=True)
    department = models.ForeignKey('university_structure.Department', on_delete=models.SET_NULL, 
                                  related_name='schedule_exports', null=True, blank=True)
    faculty = models.ForeignKey('university_structure.Faculty', on_delete=models.SET_NULL, 
                               related_name='schedule_exports', null=True, blank=True)
    
    # Результат экспорта
    file = models.FileField(_('Файл'), upload_to='schedule_exports/')
    
    # Метаданные
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  related_name='schedule_exports', null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('экспорт расписания')
        verbose_name_plural = _('экспорты расписания')
        ordering = ['-created_at']
    
    def __str__(self):
        entity_name = ""
        if self.student:
            entity_name = self.student.user.get_full_name()
        elif self.group:
            entity_name = self.group.name
        elif self.teacher:
            entity_name = self.teacher.user.get_full_name()
        elif self.room:
            entity_name = str(self.room)
        elif self.department:
            entity_name = self.department.name
        elif self.faculty:
            entity_name = self.faculty.name
        
        return f"{self.get_export_type_display()} - {entity_name} ({self.start_date} - {self.end_date})"

class ClassAttendanceTracking(models.Model):
    """
    Модель для отслеживания факта проведения занятия
    """
    class_instance = models.OneToOneField(Class, on_delete=models.CASCADE, related_name='attendance_tracking')
    conducted_by = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                                    related_name='conducted_classes', null=True, blank=True)
    
    # Факт проведения
    is_conducted = models.BooleanField(_('Проведено'), default=False)
    actual_start_time = models.TimeField(_('Фактическое время начала'), null=True, blank=True)
    actual_end_time = models.TimeField(_('Фактическое время окончания'), null=True, blank=True)
    
    # Статистика посещаемости
    students_count = models.PositiveSmallIntegerField(_('Количество студентов'), default=0)
    students_present = models.PositiveSmallIntegerField(_('Присутствующих студентов'), default=0)
    
    # Замена преподавателя
    substitute_teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.SET_NULL, 
                                          related_name='substituted_classes', null=True, blank=True)
    
    # Комментарий преподавателя
    teacher_comment = models.TextField(_('Комментарий преподавателя'), blank=True)
    
    # Метаданные
    marked_at = models.DateTimeField(_('Отмечено'), auto_now=True)
    
    class Meta:
        verbose_name = _('отметка о проведении')
        verbose_name_plural = _('отметки о проведении')
    
    def __str__(self):
        status = _('Проведено') if self.is_conducted else _('Не проведено')
        return f"{self.class_instance} - {status}"
    
    @property
    def attendance_percentage(self):
        """Процент посещаемости"""
        if self.students_count > 0:
            return (self.students_present / self.students_count) * 100
        return 0

# Дополняем систему сигналов для генерации занятий из шаблона

@receiver(post_save, sender=ScheduleItem)
def create_classes_from_template(sender, instance, created, **kwargs):
    """
    Создает занятия на основе шаблона для будущих дат
    """
    if created:
        # Получаем семестр из шаблона
        semester = instance.schedule_template.semester
        
        # Определяем начальную и конечную даты для генерации занятий
        start_date = max(semester.class_start_date, timezone.now().date())
        end_date = semester.class_end_date
        
        # Генерируем все даты для этого дня недели в указанном периоде
        current_date = start_date
        while current_date <= end_date:
            # Если день недели совпадает
            if current_date.weekday() == instance.weekday:
                # Определяем номер недели от начала семестра
                week_number = ((current_date - semester.class_start_date).days // 7) + 1
                
                # Проверяем соответствие типу недели (четная/нечетная)
                if (instance.week_type == 'every' or
                    (instance.week_type == 'odd' and week_number % 2 == 1) or
                    (instance.week_type == 'even' and week_number % 2 == 0)):
                    
                    # Проверяем, не попадает ли дата на праздник
                    is_holiday = False
                    for holiday in semester.academic_year.holidays.all():
                        if holiday.start_date <= current_date <= holiday.end_date:
                            is_holiday = True
                            break
                    
                    if not is_holiday:
                        # Создаем экземпляр занятия
                        class_obj = Class.objects.create(
                            schedule_item=instance,
                            subject=instance.subject,
                            teacher=instance.teacher,
                            class_type=instance.class_type,
                            date=current_date,
                            time_slot=instance.time_slot,
                            room=instance.room,
                            status='scheduled'
                        )
                        
                        # Добавляем группы и подгруппы
                        class_obj.groups.set(instance.groups.all())
                        class_obj.subgroups.set(instance.subgroups.all())
            
            # Переходим к следующей дате
            current_date += datetime.timedelta(days=1)

@receiver(m2m_changed, sender=ScheduleItem.groups.through)
def update_groups_in_classes(sender, instance, action, **kwargs):
    """
    Обновляет группы в занятиях при изменении групп в элементе расписания
    """
    if action in ('post_add', 'post_remove', 'post_clear'):
        # Обновляем группы во всех будущих занятиях
        for class_obj in instance.classes.filter(date__gte=timezone.now().date()):
            if action == 'post_clear':
                class_obj.groups.clear()
            else:
                class_obj.groups.set(instance.groups.all())

@receiver(m2m_changed, sender=ScheduleItem.subgroups.through)
def update_subgroups_in_classes(sender, instance, action, **kwargs):
    """
    Обновляет подгруппы в занятиях при изменении подгрупп в элементе расписания
    """
    if action in ('post_add', 'post_remove', 'post_clear'):
        # Обновляем подгруппы во всех будущих занятиях
        for class_obj in instance.classes.filter(date__gte=timezone.now().date()):
            if action == 'post_clear':
                class_obj.subgroups.clear()
            else:
                class_obj.subgroups.set(instance.subgroups.all())

@receiver(post_save, sender=Class)
def create_class_attendance_tracking(sender, instance, created, **kwargs):
    """
    Создает запись для отслеживания проведения занятия
    """
    if created:
        ClassAttendanceTracking.objects.create(
            class_instance=instance,
            conducted_by=instance.teacher,
            students_count=sum([group.students.count() for group in instance.groups.all()])
        )

@receiver(post_save, sender=ExamSchedule)
def create_exam_notification(sender, instance, created, **kwargs):
    """
    Создает уведомление о предстоящем экзамене
    """
    if created:
        # Создаем уведомление за 3 дня до экзамена
        notification_date = instance.date - datetime.timedelta(days=3)
        
        # Формируем заголовок и сообщение
        title = f"{instance.get_exam_type_display()} по {instance.subject.name}"
        message = f"Напоминаем, что {instance.get_exam_type_display().lower()} по предмету '{instance.subject.name}' "
        message += f"состоится {instance.date.strftime('%d.%m.%Y')} в {instance.start_time.strftime('%H:%M')} "
        message += f"в аудитории {instance.room}."
        
        # Создаем уведомление
        notification = ScheduleNotification.objects.create(
            notification_type='exam_reminder',
            exam=instance,
            title=title,
            message=message,
            scheduled_for=notification_date
        )
        
        # Добавляем получателей - студентов групп и преподавателя
        users = [instance.teacher.user]
        for group in instance.groups.all():
            for student in group.students.all():
                users.append(student.user)
        
        notification.recipients.set(users)

@receiver(post_save, sender=ScheduleChange)
def create_schedule_change_notification(sender, instance, created, **kwargs):
    """
    Создает уведомление об изменении в расписании
    """
    if created and not instance.is_notification_sent:
        # Формируем заголовок и сообщение
        title = f"{instance.get_change_type_display()} занятия по {instance.affected_class.subject.name}"
        message = f"Информируем об изменении в расписании: {instance.get_change_type_display().lower()} "
        message += f"занятия по предмету '{instance.affected_class.subject.name}', "
        message += f"которое было запланировано на {instance.affected_class.date.strftime('%d.%m.%Y')} "
        message += f"в {instance.affected_class.time_slot.start_time.strftime('%H:%M')}."
        
        if instance.change_type == 'reschedule' and instance.new_date and instance.new_time_slot:
            message += f" Занятие перенесено на {instance.new_date.strftime('%d.%m.%Y')} "
            message += f"в {instance.new_time_slot.start_time.strftime('%H:%M')}."
        
        if instance.description:
            message += f" Причина: {instance.description}"
        
        # Создаем уведомление
        notification = ScheduleNotification.objects.create(
            notification_type='class_change',
            schedule_change=instance,
            title=title,
            message=message,
            scheduled_for=timezone.now()
        )
        
        # Добавляем получателей - студентов групп и преподавателя
        users = [instance.affected_class.teacher.user]
        for group in instance.affected_class.groups.all():
            for student in group.students.all():
                users.append(student.user)
        
        notification.recipients.set(users)
        
        # Отмечаем, что уведомление создано
        instance.is_notification_sent = True
        instance.notification_sent_at = timezone.now()
        instance.save(update_fields=['is_notification_sent', 'notification_sent_at'])