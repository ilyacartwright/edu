# Регистрация моделей в админке
# Модели уже зарегистрированы через декораторы @admin.register
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

from .models import (
    TimeSlot, ClassType, ScheduleTemplate, ScheduleItem, Class,
    ScheduleChange, DailyScheduleGeneration, ConsultationSchedule,
    ExamSchedule, ScheduleAdditionalInfo, ScheduleNotification,
    ScheduleExport, ClassAttendanceTracking
)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """
    Административная модель для временных слотов
    """
    list_display = ('number', 'start_time', 'end_time', 'break_after', 'duration_display')
    list_filter = ('break_after',)
    search_fields = ('number',)
    ordering = ('number',)
    
    def duration_display(self, obj):
        """Отображает продолжительность слота в минутах"""
        if obj.start_time and obj.end_time:
            # Конвертируем время в минуты
            start_minutes = obj.start_time.hour * 60 + obj.start_time.minute
            end_minutes = obj.end_time.hour * 60 + obj.end_time.minute
            duration = end_minutes - start_minutes
            return f"{duration} мин."
        return "-"
    duration_display.short_description = _("Продолжительность")


@admin.register(ClassType)
class ClassTypeAdmin(admin.ModelAdmin):
    """
    Административная модель для типов занятий
    """
    list_display = ('name', 'short_name', 'color_display')
    search_fields = ('name', 'short_name')
    
    def color_display(self, obj):
        """Отображает цвет типа занятия с образцом"""
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = _("Цвет")


class ScheduleItemInline(admin.TabularInline):
    """
    Встраиваемая форма для элементов шаблона расписания
    """
    model = ScheduleItem
    extra = 1
    fields = ('subject', 'teacher', 'class_type', 'room', 'time_slot', 'weekday', 'week_type')
    raw_id_fields = ('subject', 'teacher', 'room')
    autocomplete_fields = ('subject', 'teacher', 'room')
    filter_horizontal = ('groups', 'subgroups')
    show_change_link = True


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(admin.ModelAdmin):
    """
    Административная модель для шаблонов расписания
    """
    list_display = ('name', 'semester', 'is_active', 'items_count', 'created_at', 'updated_at')
    list_filter = ('is_active', 'semester__academic_year', 'semester')
    search_fields = ('name',)
    list_select_related = ('semester', 'semester__academic_year')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'semester', 'is_active')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ScheduleItemInline]
    actions = ['activate_templates', 'deactivate_templates', 'generate_classes']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(items_count=Count('items'))
    
    def items_count(self, obj):
        """Отображает количество элементов в шаблоне"""
        return obj.items_count
    items_count.short_description = _("Элементов")
    items_count.admin_order_field = 'items_count'
    
    def activate_templates(self, request, queryset):
        """Активирует выбранные шаблоны"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные шаблоны активированы'))
    activate_templates.short_description = _('Активировать шаблоны')
    
    def deactivate_templates(self, request, queryset):
        """Деактивирует выбранные шаблоны"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные шаблоны деактивированы'))
    deactivate_templates.short_description = _('Деактивировать шаблоны')
    
    def generate_classes(self, request, queryset):
        """Генерирует занятия на основе выбранных шаблонов"""
        from django.utils import timezone
        import datetime
        
        count = 0
        for template in queryset:
            # Получаем все элементы шаблона
            items = template.items.all()
            
            # Получаем семестр из шаблона
            semester = template.semester
            
            # Определяем начальную и конечную даты для генерации занятий
            start_date = max(semester.class_start_date, timezone.now().date())
            end_date = semester.class_end_date
            
            for item in items:
                # Генерируем занятия для каждого элемента шаблона
                current_date = start_date
                while current_date <= end_date:
                    # Если день недели совпадает
                    if current_date.weekday() == item.weekday:
                        # Определяем номер недели от начала семестра
                        week_number = ((current_date - semester.class_start_date).days // 7) + 1
                        
                        # Проверяем соответствие типу недели (четная/нечетная)
                        if (item.week_type == 'every' or
                            (item.week_type == 'odd' and week_number % 2 == 1) or
                            (item.week_type == 'even' and week_number % 2 == 0)):
                            
                            # Проверяем, не попадает ли дата на праздник
                            is_holiday = False
                            for holiday in semester.academic_year.holidays.all():
                                if holiday.start_date <= current_date <= holiday.end_date:
                                    is_holiday = True
                                    break
                            
                            # Проверяем, не существует ли уже занятие с такими параметрами
                            if not is_holiday and not Class.objects.filter(
                                schedule_item=item,
                                date=current_date,
                                time_slot=item.time_slot,
                                room=item.room
                            ).exists():
                                # Создаем экземпляр занятия
                                class_obj = Class.objects.create(
                                    schedule_item=item,
                                    subject=item.subject,
                                    teacher=item.teacher,
                                    class_type=item.class_type,
                                    date=current_date,
                                    time_slot=item.time_slot,
                                    room=item.room,
                                    status='scheduled'
                                )
                                
                                # Добавляем группы и подгруппы
                                class_obj.groups.set(item.groups.all())
                                class_obj.subgroups.set(item.subgroups.all())
                                
                                count += 1
                            
                    # Переходим к следующей дате
                    current_date += datetime.timedelta(days=1)
                    
            # Создаем запись об успешной генерации
            DailyScheduleGeneration.objects.create(
                date=timezone.now().date(),
                schedule_template=template,
                is_generated=True,
                generated_at=timezone.now(),
                generated_by=request.user if request.user.is_authenticated else None
            )
        
        self.message_user(request, _('Сгенерировано {} занятий на основе выбранных шаблонов').format(count))
    generate_classes.short_description = _('Сгенерировать занятия')


class WeekdayFilter(SimpleListFilter):
    """
    Фильтр по дням недели
    """
    title = _('день недели')
    parameter_name = 'weekday'

    def lookups(self, request, model_admin):
        return ScheduleItem.WEEKDAYS

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(weekday=self.value())
        return queryset


class WeekTypeFilter(SimpleListFilter):
    """
    Фильтр по типу недели
    """
    title = _('тип недели')
    parameter_name = 'week_type'

    def lookups(self, request, model_admin):
        return ScheduleItem.WEEK_TYPES

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(week_type=self.value())
        return queryset


@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    """
    Административная модель для элементов расписания
    """
    list_display = (
        'subject', 'teacher', 'class_type', 'weekday_display', 'time_slot',
        'room', 'week_type_display', 'groups_display', 'classes_count'
    )
    list_filter = (
        'schedule_template', 'class_type', WeekdayFilter, WeekTypeFilter,
        'subject__department', 'groups', 'week_type'
    )
    search_fields = (
        'subject__name', 'teacher__user__last_name', 'teacher__user__first_name',
        'room__number', 'room__building__name'
    )
    list_select_related = ('subject', 'teacher', 'teacher__user', 'class_type', 'room', 'time_slot')
    filter_horizontal = ('groups', 'subgroups')
    fieldsets = (
        (_('Связь с шаблоном'), {
            'fields': ('schedule_template',)
        }),
        (_('Предмет и преподаватель'), {
            'fields': ('subject', 'teacher', 'class_type')
        }),
        (_('Группы и подгруппы'), {
            'fields': ('groups', 'subgroups')
        }),
        (_('Время и место'), {
            'fields': ('room', 'time_slot', 'weekday', 'week_type')
        }),
        (_('Дополнительно'), {
            'fields': ('comment',),
            'classes': ('collapse',)
        }),
    )
    actions = ['generate_classes', 'copy_to_next_week']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(classes_count=Count('classes'))
    
    def weekday_display(self, obj):
        """Отображает день недели"""
        return obj.get_weekday_display()
    weekday_display.short_description = _("День недели")
    weekday_display.admin_order_field = 'weekday'
    
    def week_type_display(self, obj):
        """Отображает тип недели"""
        return obj.get_week_type_display()
    week_type_display.short_description = _("Тип недели")
    week_type_display.admin_order_field = 'week_type'
    
    def groups_display(self, obj):
        """Отображает список групп"""
        return ", ".join([group.name for group in obj.groups.all()[:3]])
    groups_display.short_description = _("Группы")
    
    def classes_count(self, obj):
        """Отображает количество сгенерированных занятий"""
        return obj.classes_count
    classes_count.short_description = _("Занятий")
    classes_count.admin_order_field = 'classes_count'
    
    def generate_classes(self, request, queryset):
        """Генерирует занятия для выбранных элементов расписания"""
        from django.utils import timezone
        import datetime
        
        count = 0
        for item in queryset:
            # Получаем семестр из шаблона
            semester = item.schedule_template.semester
            
            # Определяем начальную и конечную даты для генерации занятий
            start_date = max(semester.class_start_date, timezone.now().date())
            end_date = semester.class_end_date
            
            # Генерируем все даты для этого дня недели в указанном периоде
            current_date = start_date
            while current_date <= end_date:
                # Если день недели совпадает
                if current_date.weekday() == item.weekday:
                    # Определяем номер недели от начала семестра
                    week_number = ((current_date - semester.class_start_date).days // 7) + 1
                    
                    # Проверяем соответствие типу недели (четная/нечетная)
                    if (item.week_type == 'every' or
                        (item.week_type == 'odd' and week_number % 2 == 1) or
                        (item.week_type == 'even' and week_number % 2 == 0)):
                        
                        # Проверяем, не попадает ли дата на праздник
                        is_holiday = False
                        for holiday in semester.academic_year.holidays.all():
                            if holiday.start_date <= current_date <= holiday.end_date:
                                is_holiday = True
                                break
                        
                        # Проверяем, не существует ли уже занятие с такими параметрами
                        if not is_holiday and not Class.objects.filter(
                            schedule_item=item,
                            date=current_date,
                            time_slot=item.time_slot,
                            room=item.room
                        ).exists():
                            # Создаем экземпляр занятия
                            class_obj = Class.objects.create(
                                schedule_item=item,
                                subject=item.subject,
                                teacher=item.teacher,
                                class_type=item.class_type,
                                date=current_date,
                                time_slot=item.time_slot,
                                room=item.room,
                                status='scheduled'
                            )
                            
                            # Добавляем группы и подгруппы
                            class_obj.groups.set(item.groups.all())
                            class_obj.subgroups.set(item.subgroups.all())
                            
                            count += 1
                        
                # Переходим к следующей дате
                current_date += datetime.timedelta(days=1)
                
        self.message_user(request, _('Сгенерировано {} занятий').format(count))
    generate_classes.short_description = _('Сгенерировать занятия')
    
    def copy_to_next_week(self, request, queryset):
        """Копирует выбранные элементы на следующую неделю"""
        for item in queryset:
            # Создаем копию элемента с измененным типом недели
            new_week_type = 'every'
            if item.week_type == 'odd':
                new_week_type = 'even'
            elif item.week_type == 'even':
                new_week_type = 'odd'
            
            # Создаем новый элемент
            new_item = ScheduleItem.objects.create(
                schedule_template=item.schedule_template,
                subject=item.subject,
                teacher=item.teacher,
                class_type=item.class_type,
                room=item.room,
                time_slot=item.time_slot,
                weekday=item.weekday,
                week_type=new_week_type,
                comment=item.comment
            )
            
            # Копируем связи с группами и подгруппами
            new_item.groups.set(item.groups.all())
            new_item.subgroups.set(item.subgroups.all())
            
        self.message_user(request, _('Выбранные элементы скопированы с инверсией типа недели'))
    copy_to_next_week.short_description = _('Копировать с инверсией типа недели')


class ClassDateFilter(SimpleListFilter):
    """
    Фильтр по дате занятия с относительными периодами
    """
    title = _('дата')
    parameter_name = 'date_filter'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Сегодня')),
            ('tomorrow', _('Завтра')),
            ('this_week', _('Текущая неделя')),
            ('next_week', _('Следующая неделя')),
            ('past', _('Прошедшие')),
            ('future', _('Будущие')),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'today':
            return queryset.filter(date=today)
        elif self.value() == 'tomorrow':
            return queryset.filter(date=today + timezone.timedelta(days=1))
        elif self.value() == 'this_week':
            # Понедельник этой недели
            start_of_week = today - timezone.timedelta(days=today.weekday())
            # Воскресенье этой недели
            end_of_week = start_of_week + timezone.timedelta(days=6)
            return queryset.filter(date__range=[start_of_week, end_of_week])
        elif self.value() == 'next_week':
            # Понедельник следующей недели
            start_of_next_week = today + timezone.timedelta(days=(7 - today.weekday()))
            # Воскресенье следующей недели
            end_of_next_week = start_of_next_week + timezone.timedelta(days=6)
            return queryset.filter(date__range=[start_of_next_week, end_of_next_week])
        elif self.value() == 'past':
            return queryset.filter(date__lt=today)
        elif self.value() == 'future':
            return queryset.filter(date__gte=today)
        return queryset


class ScheduleAdditionalInfoInline(admin.StackedInline):
    """
    Встраиваемая форма для дополнительной информации о занятии
    """
    model = ScheduleAdditionalInfo
    can_delete = False
    verbose_name_plural = _('Дополнительная информация')
    
    fieldsets = (
        (_('Материалы и курсы'), {
            'fields': ('materials', 'course_element'),
        }),
        (_('Онлайн-занятие'), {
            'fields': ('is_online', 'online_meeting_url'),
        }),
        (_('Подготовка'), {
            'fields': ('preparation_instructions',),
        }),
    )
    filter_horizontal = ('materials',)


class ClassAttendanceTrackingInline(admin.StackedInline):
    """
    Встраиваемая форма для отслеживания проведения занятия
    """
    model = ClassAttendanceTracking
    can_delete = False
    verbose_name_plural = _('Отметка о проведении')
    
    fieldsets = (
        (_('Проведение занятия'), {
            'fields': ('is_conducted', 'actual_start_time', 'actual_end_time', 'substitute_teacher'),
        }),
        (_('Посещаемость'), {
            'fields': ('students_count', 'students_present'),
        }),
        (_('Комментарий'), {
            'fields': ('teacher_comment',),
        }),
    )
    readonly_fields = ('marked_at',)


class ScheduleChangeInline(admin.TabularInline):
    """
    Встраиваемая форма для изменений в расписании
    """
    model = ScheduleChange
    fk_name = 'affected_class'
    extra = 1
    fields = ('change_type', 'description', 'new_date', 'new_time_slot', 'new_room', 'new_teacher')
    raw_id_fields = ('new_room', 'new_teacher', 'new_time_slot')
    autocomplete_fields = ('new_room', 'new_teacher', 'new_time_slot')
    readonly_fields = ('created_at',)
    can_delete = False


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """
    Административная модель для занятий
    """
    list_display = (
        'subject', 'teacher', 'class_type', 'date', 'time_slot',
        'room', 'groups_display', 'status', 'is_conducted'
    )
    list_filter = (
        ClassDateFilter, 'status', 'class_type', 'subject__department',
        'teacher', 'room__building', 'groups'
    )
    search_fields = (
        'subject__name', 'teacher__user__last_name', 'teacher__user__first_name',
        'room__number', 'room__building__name', 'topic', 'description'
    )
    list_select_related = ('subject', 'teacher', 'teacher__user', 'class_type', 'room', 'time_slot')
    filter_horizontal = ('groups', 'subgroups')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Предмет и преподаватель'), {
            'fields': ('subject', 'teacher', 'class_type', 'schedule_item')
        }),
        (_('Группы и подгруппы'), {
            'fields': ('groups', 'subgroups')
        }),
        (_('Время и место'), {
            'fields': ('date', 'time_slot', 'room')
        }),
        (_('Тема и описание'), {
            'fields': ('topic', 'description')
        }),
        (_('Статус'), {
            'fields': ('status', 'cancellation_reason', 'original_class')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ScheduleAdditionalInfoInline, ClassAttendanceTrackingInline, ScheduleChangeInline]
    actions = [
        'mark_as_conducted', 'mark_as_canceled', 'copy_to_next_week',
        'generate_attendance_tracking'
    ]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('attendance_tracking')
    
    def groups_display(self, obj):
        """Отображает список групп"""
        return ", ".join([group.name for group in obj.groups.all()[:3]])
    groups_display.short_description = _("Группы")
    
    def is_conducted(self, obj):
        """Отображает, проведено ли занятие"""
        if hasattr(obj, 'attendance_tracking'):
            return obj.attendance_tracking.is_conducted
        return False
    is_conducted.boolean = True
    is_conducted.short_description = _("Проведено")
    
    def mark_as_conducted(self, request, queryset):
        """Отмечает выбранные занятия как проведенные"""
        for class_obj in queryset:
            # Обновляем или создаем запись об отслеживании посещаемости
            attendance_tracking, created = ClassAttendanceTracking.objects.get_or_create(
                class_instance=class_obj,
                defaults={
                    'conducted_by': class_obj.teacher,
                    'is_conducted': True,
                    'actual_start_time': class_obj.time_slot.start_time,
                    'actual_end_time': class_obj.time_slot.end_time,
                    'students_count': sum([group.students.count() for group in class_obj.groups.all()])
                }
            )
            
            if not created:
                attendance_tracking.is_conducted = True
                attendance_tracking.save(update_fields=['is_conducted'])
                
            # Обновляем статус занятия
            if class_obj.status != 'completed':
                class_obj.status = 'completed'
                class_obj.save(update_fields=['status'])
                
        self.message_user(request, _('Выбранные занятия отмечены как проведенные'))
    mark_as_conducted.short_description = _('Отметить как проведенные')
    
    def mark_as_canceled(self, request, queryset):
        """Отмечает выбранные занятия как отмененные"""
        for class_obj in queryset:
            if class_obj.status != 'canceled':
                # Создаем запись об изменении в расписании
                ScheduleChange.objects.create(
                    affected_class=class_obj,
                    change_type='cancel',
                    description=_('Занятие отменено через административную панель'),
                    created_by=request.user if request.user.is_authenticated else None
                )
                
        self.message_user(request, _('Выбранные занятия отмечены как отмененные'))
    mark_as_canceled.short_description = _('Отметить как отмененные')
    
    def copy_to_next_week(self, request, queryset):
        """Копирует выбранные занятия на следующую неделю"""
        count = 0
        for class_obj in queryset:
            # Вычисляем дату через неделю
            next_week_date = class_obj.date + timezone.timedelta(days=7)
            
            # Проверяем, не существует ли уже занятие на эту дату
            if not Class.objects.filter(
                subject=class_obj.subject,
                date=next_week_date,
                time_slot=class_obj.time_slot,
                room=class_obj.room
            ).exists():
                # Создаем копию занятия
                new_class = Class.objects.create(
                    subject=class_obj.subject,
                    teacher=class_obj.teacher,
                    class_type=class_obj.class_type,
                    date=next_week_date,
                    time_slot=class_obj.time_slot,
                    room=class_obj.room,
                    status='scheduled',
                    topic=class_obj.topic,
                    description=class_obj.description
                )
                
                # Копируем связи с группами и подгруппами
                new_class.groups.set(class_obj.groups.all())
                new_class.subgroups.set(class_obj.subgroups.all())
                
                count += 1
                
        self.message_user(request, _('Скопировано {} занятий на следующую неделю').format(count))
    copy_to_next_week.short_description = _('Копировать на следующую неделю')
    
    def generate_attendance_tracking(self, request, queryset):
        """Генерирует записи об отслеживании посещаемости для выбранных занятий"""
        count = 0
        for class_obj in queryset:
            if not hasattr(class_obj, 'attendance_tracking'):
                # Создаем запись об отслеживании посещаемости
                ClassAttendanceTracking.objects.create(
                    class_instance=class_obj,
                    conducted_by=class_obj.teacher,
                    students_count=sum([group.students.count() for group in class_obj.groups.all()])
                )
                count += 1
                
        self.message_user(request, _('Созданы записи об отслеживании посещаемости для {} занятий').format(count))
    generate_attendance_tracking.short_description = _('Создать отслеживание посещаемости')


@admin.register(ScheduleChange)
class ScheduleChangeAdmin(admin.ModelAdmin):
    """
    Административная модель для изменений в расписании
    """
    list_display = (
        'affected_class', 'change_type', 'description_short',
        'created_by', 'created_at', 'is_notification_sent'
    )
    list_filter = ('change_type', 'created_at', 'is_notification_sent')
    search_fields = (
        'affected_class__subject__name', 'affected_class__teacher__user__last_name',
        'description', 'created_by__username'
    )
    list_select_related = ('affected_class', 'affected_class__subject', 'created_by', 'new_class')
    readonly_fields = ('created_at', 'notification_sent_at')
    
    fieldsets = (
        (_('Связь с занятием'), {
            'fields': ('affected_class',)
        }),
        (_('Тип изменения'), {
            'fields': ('change_type', 'description')
        }),
        (_('Новые параметры'), {
            'fields': ('new_date', 'new_time_slot', 'new_room', 'new_teacher')
        }),
        (_('Новое занятие'), {
            'fields': ('new_class',)
        }),
        (_('Уведомление'), {
            'fields': ('is_notification_sent', 'notification_sent_at')
        }),
        (_('Метаданные'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['send_notifications', 'create_new_classes']
    
    def description_short(self, obj):
        """Отображает сокращенное описание изменения"""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    description_short.short_description = _("Описание")
    
    def send_notifications(self, request, queryset):
        """Отправляет уведомления о выбранных изменениях"""
        count = 0
        for change in queryset.filter(is_notification_sent=False):
            # Формируем заголовок и сообщение
            title = f"{change.get_change_type_display()} занятия по {change.affected_class.subject.name}"
            message = f"Информируем об изменении в расписании: {change.get_change_type_display().lower()} "
            message += f"занятия по предмету '{change.affected_class.subject.name}', "
            message += f"которое было запланировано на {change.affected_class.date.strftime('%d.%m.%Y')} "
            message += f"в {change.affected_class.time_slot.start_time.strftime('%H:%M')}."
            
            if change.change_type == 'reschedule' and change.new_date and change.new_time_slot:
                message += f" Занятие перенесено на {change.new_date.strftime('%d.%m.%Y')} "
                message += f"в {change.new_time_slot.start_time.strftime('%H:%M')}."
            
            if change.description:
                message += f" Причина: {change.description}"
            
            # Создаем уведомление
            notification = ScheduleNotification.objects.create(
                notification_type='class_change',
                schedule_change=change,
                title=title,
                message=message,
                scheduled_for=timezone.now()
            )
            
            # Добавляем получателей - студентов групп и преподавателя
            users = [change.affected_class.teacher.user]
            for group in change.affected_class.groups.all():
                for student in group.students.all():
                    users.append(student.user)
            
            notification.recipients.set(users)
            
            # Отмечаем, что уведомление создано
            change.is_notification_sent = True
            change.notification_sent_at = timezone.now()
            change.save(update_fields=['is_notification_sent', 'notification_sent_at'])
            
            count += 1
            
        self.message_user(request, _('Отправлены уведомления для {} изменений').format(count))
    send_notifications.short_description = _('Отправить уведомления')
    
    def create_new_classes(self, request, queryset):
        """Создает новые занятия на основе изменений с типом 'reschedule'"""
        count = 0
        for change in queryset.filter(change_type='reschedule', new_class__isnull=True):
            if change.new_date and change.new_time_slot and change.new_room:
                # Создаем новое занятие
                affected_class = change.affected_class
                new_teacher = change.new_teacher or affected_class.teacher
                
                # Проверяем, не существует ли уже занятие с такими параметрами
                if not Class.objects.filter(
                    date=change.new_date,
                    time_slot=change.new_time_slot,
                    room=change.new_room
                ).exists():
                    # Создаем экземпляр занятия
                    new_class = Class.objects.create(
                        schedule_item=affected_class.schedule_item,
                        subject=affected_class.subject,
                        teacher=new_teacher,
                        class_type=affected_class.class_type,
                        date=change.new_date,
                        time_slot=change.new_time_slot,
                        room=change.new_room,
                        status='scheduled',
                        topic=affected_class.topic,
                        description=affected_class.description,
                        original_class=affected_class
                    )
                    
                    # Добавляем группы и подгруппы
                    new_class.groups.set(affected_class.groups.all())
                    new_class.subgroups.set(affected_class.subgroups.all())
                    
                    # Связываем с изменением
                    change.new_class = new_class
                    change.save(update_fields=['new_class'])
                    
                    count += 1
                    
        self.message_user(request, _('Создано {} новых занятий').format(count))
    create_new_classes.short_description = _('Создать новые занятия')


@admin.register(DailyScheduleGeneration)
class DailyScheduleGenerationAdmin(admin.ModelAdmin):
    """
    Административная модель для отслеживания генерации ежедневного расписания
    """
    list_display = ('date', 'schedule_template', 'is_generated', 'generated_at', 'generated_by')
    list_filter = ('is_generated', 'date', 'schedule_template')
    search_fields = ('date',)
    list_select_related = ('schedule_template', 'generated_by')
    readonly_fields = ('generated_at',)
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Информация о генерации'), {
            'fields': ('date', 'schedule_template', 'is_generated')
        }),
        (_('Метаданные'), {
            'fields': ('generated_at', 'generated_by'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_generated']
    
    def mark_as_generated(self, request, queryset):
        """Отмечает выбранные записи как сгенерированные"""
        queryset.update(is_generated=True, generated_at=timezone.now(), generated_by=request.user)
        self.message_user(request, _('Выбранные записи отмечены как сгенерированные'))
    mark_as_generated.short_description = _('Отметить как сгенерированные')


@admin.register(ConsultationSchedule)
class ConsultationScheduleAdmin(admin.ModelAdmin):
    """
    Административная модель для расписания консультаций
    """
    list_display = (
        'teacher', 'weekday_display', 'time_range', 'room',
        'groups_display', 'week_type_display', 'is_active'
    )
    list_filter = ('weekday', 'is_active', 'semester', 'teacher', 'week_type')
    search_fields = (
        'teacher__user__last_name', 'teacher__user__first_name',
        'room__number', 'room__building__name', 'comment'
    )
    list_select_related = ('teacher', 'teacher__user', 'room', 'semester')
    filter_horizontal = ('groups',)
    
    fieldsets = (
        (_('Преподаватель и семестр'), {
            'fields': ('teacher', 'semester')
        }),
        (_('Время и место'), {
            'fields': ('weekday', 'start_time', 'end_time', 'room', 'week_type')
        }),
        (_('Группы'), {
            'fields': ('groups',)
        }),
        (_('Дополнительно'), {
            'fields': ('is_active', 'comment')
        }),
    )
    actions = ['activate_consultations', 'deactivate_consultations']
    
    def weekday_display(self, obj):
        """Отображает день недели"""
        return obj.get_weekday_display()
    weekday_display.short_description = _("День недели")
    weekday_display.admin_order_field = 'weekday'
    
    def time_range(self, obj):
        """Отображает временной диапазон"""
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = _("Время")
    
    def week_type_display(self, obj):
        """Отображает тип недели"""
        return obj.get_week_type_display()
    week_type_display.short_description = _("Тип недели")
    week_type_display.admin_order_field = 'week_type'
    
    def groups_display(self, obj):
        """Отображает список групп"""
        groups = list(obj.groups.all())
        if not groups:
            return _("Все группы")
        return ", ".join([group.name for group in groups[:3]])
    groups_display.short_description = _("Группы")
    
    def activate_consultations(self, request, queryset):
        """Активирует выбранные консультации"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные консультации активированы'))
    activate_consultations.short_description = _('Активировать консультации')
    
    def deactivate_consultations(self, request, queryset):
        """Деактивирует выбранные консультации"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные консультации деактивированы'))
    deactivate_consultations.short_description = _('Деактивировать консультации')


class ExamDateFilter(SimpleListFilter):
    """
    Фильтр по дате экзамена с относительными периодами
    """
    title = _('дата')
    parameter_name = 'date_filter'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Сегодня')),
            ('tomorrow', _('Завтра')),
            ('this_week', _('Текущая неделя')),
            ('next_week', _('Следующая неделя')),
            ('upcoming', _('Ближайшие 30 дней')),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'today':
            return queryset.filter(date=today)
        elif self.value() == 'tomorrow':
            return queryset.filter(date=today + timezone.timedelta(days=1))
        elif self.value() == 'this_week':
            # Понедельник этой недели
            start_of_week = today - timezone.timedelta(days=today.weekday())
            # Воскресенье этой недели
            end_of_week = start_of_week + timezone.timedelta(days=6)
            return queryset.filter(date__range=[start_of_week, end_of_week])
        elif self.value() == 'next_week':
            # Понедельник следующей недели
            start_of_next_week = today + timezone.timedelta(days=(7 - today.weekday()))
            # Воскресенье следующей недели
            end_of_next_week = start_of_next_week + timezone.timedelta(days=6)
            return queryset.filter(date__range=[start_of_next_week, end_of_next_week])
        elif self.value() == 'upcoming':
            return queryset.filter(date__range=[today, today + timezone.timedelta(days=30)])
        return queryset


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    """
    Административная модель для расписания экзаменов
    """
    list_display = (
        'subject', 'exam_type_display', 'teacher', 'date', 'time_range',
        'room', 'groups_display', 'status', 'semester'
    )
    list_filter = (
        ExamDateFilter, 'exam_type', 'status', 'semester',
        'subject__department', 'teacher', 'groups'
    )
    search_fields = (
        'subject__name', 'teacher__user__last_name', 'teacher__user__first_name',
        'room__number', 'room__building__name', 'description'
    )
    list_select_related = ('subject', 'teacher', 'teacher__user', 'room', 'semester')
    filter_horizontal = ('groups',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Предмет и преподаватель'), {
            'fields': ('subject', 'teacher')
        }),
        (_('Тип экзамена и семестр'), {
            'fields': ('exam_type', 'semester')
        }),
        (_('Группы'), {
            'fields': ('groups',)
        }),
        (_('Время и место'), {
            'fields': ('date', 'start_time', 'end_time', 'room')
        }),
        (_('Статус и описание'), {
            'fields': ('status', 'description')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'mark_as_completed', 'mark_as_canceled', 'mark_as_scheduled',
        'create_consultation', 'send_reminders'
    ]
    
    def exam_type_display(self, obj):
        """Отображает тип экзамена"""
        return obj.get_exam_type_display()
    exam_type_display.short_description = _("Тип")
    exam_type_display.admin_order_field = 'exam_type'
    
    def time_range(self, obj):
        """Отображает временной диапазон"""
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = _("Время")
    
    def groups_display(self, obj):
        """Отображает список групп"""
        return ", ".join([group.name for group in obj.groups.all()[:3]])
    groups_display.short_description = _("Группы")
    
    def mark_as_completed(self, request, queryset):
        """Отмечает выбранные экзамены как проведенные"""
        queryset.update(status='completed')
        self.message_user(request, _('Выбранные экзамены отмечены как проведенные'))
    mark_as_completed.short_description = _('Отметить как проведенные')
    
    def mark_as_canceled(self, request, queryset):
        """Отмечает выбранные экзамены как отмененные"""
        queryset.update(status='canceled')
        self.message_user(request, _('Выбранные экзамены отмечены как отмененные'))
    mark_as_canceled.short_description = _('Отметить как отмененные')
    
    def mark_as_scheduled(self, request, queryset):
        """Отмечает выбранные экзамены как запланированные"""
        queryset.update(status='scheduled')
        self.message_user(request, _('Выбранные экзамены отмечены как запланированные'))
    mark_as_scheduled.short_description = _('Отметить как запланированные')
    
    def create_consultation(self, request, queryset):
        """Создает консультацию перед экзаменом"""
        count = 0
        for exam in queryset:
            # Вычисляем дату консультации за 2 дня до экзамена
            consultation_date = exam.date - timezone.timedelta(days=2)
            
            # Проверяем, не попадает ли дата на выходной
            if consultation_date.weekday() >= 5:  # Суббота или воскресенье
                consultation_date = exam.date - timezone.timedelta(days=3)  # Вычитаем еще один день
            
            # Создаем экзамен-консультацию
            if not ExamSchedule.objects.filter(
                subject=exam.subject,
                date=consultation_date,
                exam_type='consultation'
            ).exists():
                # Время консультации - обычно днем
                start_time = timezone.datetime.strptime('14:00', '%H:%M').time()
                end_time = timezone.datetime.strptime('15:30', '%H:%M').time()
                
                # Создаем запись
                consultation = ExamSchedule.objects.create(
                    subject=exam.subject,
                    teacher=exam.teacher,
                    groups=exam.groups,
                    date=consultation_date,
                    start_time=start_time,
                    end_time=end_time,
                    room=exam.room,
                    exam_type='consultation',
                    semester=exam.semester,
                    description=_('Консультация перед экзаменом')
                )
                
                # Добавляем группы
                consultation.groups.set(exam.groups.all())
                
                count += 1
                
        self.message_user(request, _('Создано {} консультаций перед экзаменами').format(count))
    create_consultation.short_description = _('Создать консультацию')
    
    def send_reminders(self, request, queryset):
        """Отправляет напоминания о выбранных экзаменах"""
        count = 0
        for exam in queryset:
            # Формируем заголовок и сообщение
            title = f"{exam.get_exam_type_display()} по {exam.subject.name}"
            message = f"Напоминаем, что {exam.get_exam_type_display().lower()} по предмету '{exam.subject.name}' "
            message += f"состоится {exam.date.strftime('%d.%m.%Y')} в {exam.start_time.strftime('%H:%M')} "
            message += f"в аудитории {exam.room}."
            
            # Создаем уведомление
            notification = ScheduleNotification.objects.create(
                notification_type='exam_reminder',
                exam=exam,
                title=title,
                message=message,
                scheduled_for=timezone.now()
            )
            
            # Добавляем получателей - студентов групп и преподавателя
            users = [exam.teacher.user]
            for group in exam.groups.all():
                for student in group.students.all():
                    users.append(student.user)
            
            notification.recipients.set(users)
            
            count += 1
            
        self.message_user(request, _('Отправлены напоминания для {} экзаменов').format(count))
    send_reminders.short_description = _('Отправить напоминания')


@admin.register(ScheduleAdditionalInfo)
class ScheduleAdditionalInfoAdmin(admin.ModelAdmin):
    """
    Административная модель для дополнительной информации к занятию
    """
    list_display = ('class_instance', 'is_online', 'has_materials', 'has_course_element')
    list_filter = ('is_online', 'class_instance__date')
    search_fields = (
        'class_instance__subject__name', 'class_instance__topic',
        'preparation_instructions', 'online_meeting_url'
    )
    list_select_related = ('class_instance', 'class_instance__subject')
    filter_horizontal = ('materials',)
    
    fieldsets = (
        (_('Связь с занятием'), {
            'fields': ('class_instance',)
        }),
        (_('Материалы и курсы'), {
            'fields': ('materials', 'course_element'),
        }),
        (_('Онлайн-занятие'), {
            'fields': ('is_online', 'online_meeting_url'),
        }),
        (_('Подготовка'), {
            'fields': ('preparation_instructions',),
        }),
    )
    
    def has_materials(self, obj):
        """Отображает, есть ли материалы"""
        return obj.materials.exists()
    has_materials.boolean = True
    has_materials.short_description = _("Есть материалы")
    
    def has_course_element(self, obj):
        """Отображает, есть ли связь с элементом курса"""
        return obj.course_element is not None
    has_course_element.boolean = True
    has_course_element.short_description = _("Есть элемент курса")


@admin.register(ScheduleNotification)
class ScheduleNotificationAdmin(admin.ModelAdmin):
    """
    Административная модель для уведомлений о расписании
    """
    list_display = (
        'title', 'notification_type', 'related_item',
        'is_sent', 'scheduled_for', 'sent_at'
    )
    list_filter = ('notification_type', 'is_sent', 'scheduled_for')
    search_fields = ('title', 'message')
    filter_horizontal = ('recipients',)
    readonly_fields = ('created_at', 'sent_at')
    
    fieldsets = (
        (_('Уведомление'), {
            'fields': ('notification_type', 'title', 'message')
        }),
        (_('Связь с элементами расписания'), {
            'fields': ('class_instance', 'exam', 'consultation', 'schedule_change'),
        }),
        (_('Получатели'), {
            'fields': ('recipients',),
        }),
        (_('Отправка'), {
            'fields': ('scheduled_for', 'is_sent', 'sent_at'),
        }),
        (_('Метаданные'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_sent', 'send_now']
    
    def related_item(self, obj):
        """Отображает связанный элемент расписания"""
        if obj.class_instance:
            return f"Занятие: {obj.class_instance}"
        elif obj.exam:
            return f"Экзамен: {obj.exam}"
        elif obj.consultation:
            return f"Консультация: {obj.consultation}"
        elif obj.schedule_change:
            return f"Изменение: {obj.schedule_change}"
        return "-"
    related_item.short_description = _("Связанный элемент")
    
    def mark_as_sent(self, request, queryset):
        """Отмечает выбранные уведомления как отправленные"""
        queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, _('Выбранные уведомления отмечены как отправленные'))
    mark_as_sent.short_description = _('Отметить как отправленные')
    
    def send_now(self, request, queryset):
        """Отправляет выбранные уведомления немедленно"""
        # В реальном приложении здесь был бы код для отправки уведомлений
        # через email, push-уведомления или другие каналы
        queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, _('Выбранные уведомления отправлены'))
    send_now.short_description = _('Отправить сейчас')


@admin.register(ScheduleExport)
class ScheduleExportAdmin(admin.ModelAdmin):
    """
    Административная модель для экспорта расписания
    """
    list_display = (
        'export_type', 'format_type', 'entity_name',
        'date_range', 'created_by', 'created_at'
    )
    list_filter = ('export_type', 'format_type', 'created_at')
    search_fields = (
        'student__user__last_name', 'group__name', 'teacher__user__last_name',
        'room__number', 'department__name', 'faculty__name'
    )
    list_select_related = (
        'student', 'student__user', 'group', 'teacher', 'teacher__user',
        'room', 'department', 'faculty', 'created_by'
    )
    readonly_fields = ('created_at', 'file')
    
    fieldsets = (
        (_('Тип и формат'), {
            'fields': ('export_type', 'format_type')
        }),
        (_('Период'), {
            'fields': ('start_date', 'end_date'),
        }),
        (_('Фильтры'), {
            'fields': ('student', 'group', 'teacher', 'room', 'department', 'faculty'),
        }),
        (_('Результат'), {
            'fields': ('file',),
        }),
        (_('Метаданные'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['regenerate_exports']
    
    def entity_name(self, obj):
        """Отображает название сущности, для которой экспортировано расписание"""
        if obj.student:
            return obj.student.user.get_full_name()
        elif obj.group:
            return obj.group.name
        elif obj.teacher:
            return obj.teacher.user.get_full_name()
        elif obj.room:
            return str(obj.room)
        elif obj.department:
            return obj.department.name
        elif obj.faculty:
            return obj.faculty.name
        return "-"
    entity_name.short_description = _("Объект")
    
    def date_range(self, obj):
        """Отображает диапазон дат"""
        return f"{obj.start_date.strftime('%d.%m.%Y')} - {obj.end_date.strftime('%d.%m.%Y')}"
    date_range.short_description = _("Период")
    
    def regenerate_exports(self, request, queryset):
        """Повторно генерирует выбранные экспорты"""
        # В реальном приложении здесь был бы код для генерации экспортов
        self.message_user(request, _('Выбранные экспорты сгенерированы повторно'))
    regenerate_exports.short_description = _('Сгенерировать повторно')


@admin.register(ClassAttendanceTracking)
class ClassAttendanceTrackingAdmin(admin.ModelAdmin):
    """
    Административная модель для отслеживания проведения занятий
    """
    list_display = (
        'class_instance', 'is_conducted', 'conducted_by', 'actual_time_range',
        'attendance_stats', 'substitute_teacher', 'marked_at'
    )
    list_filter = ('is_conducted', 'class_instance__date', 'conducted_by', 'substitute_teacher')
    search_fields = (
        'class_instance__subject__name', 'conducted_by__user__last_name',
        'substitute_teacher__user__last_name', 'teacher_comment'
    )
    list_select_related = ('class_instance', 'class_instance__subject', 'conducted_by', 'substitute_teacher')
    readonly_fields = ('marked_at',)
    
    fieldsets = (
        (_('Связь с занятием'), {
            'fields': ('class_instance',)
        }),
        (_('Проведение занятия'), {
            'fields': ('is_conducted', 'conducted_by', 'actual_start_time', 'actual_end_time'),
        }),
        (_('Замена преподавателя'), {
            'fields': ('substitute_teacher',),
        }),
        (_('Посещаемость'), {
            'fields': ('students_count', 'students_present'),
        }),
        (_('Комментарий'), {
            'fields': ('teacher_comment', 'marked_at'),
        }),
    )
    actions = ['mark_as_conducted', 'mark_as_not_conducted']
    
    def actual_time_range(self, obj):
        """Отображает фактический временной диапазон"""
        if obj.is_conducted and obj.actual_start_time and obj.actual_end_time:
            return f"{obj.actual_start_time.strftime('%H:%M')} - {obj.actual_end_time.strftime('%H:%M')}"
        return "-"
    actual_time_range.short_description = _("Фактическое время")
    
    def attendance_stats(self, obj):
        """Отображает статистику посещаемости"""
        if obj.is_conducted:
            if obj.students_count > 0:
                percentage = (obj.students_present / obj.students_count) * 100
                return f"{obj.students_present}/{obj.students_count} ({percentage:.1f}%)"
            return "0/0 (0%)"
        return "-"
    attendance_stats.short_description = _("Посещаемость")
    
    def mark_as_conducted(self, request, queryset):
        """Отмечает выбранные занятия как проведенные"""
        for tracking in queryset:
            if not tracking.is_conducted:
                tracking.is_conducted = True
                if not tracking.actual_start_time:
                    tracking.actual_start_time = tracking.class_instance.time_slot.start_time
                if not tracking.actual_end_time:
                    tracking.actual_end_time = tracking.class_instance.time_slot.end_time
                tracking.save()
                
                # Обновляем статус занятия
                class_instance = tracking.class_instance
                if class_instance.status != 'completed':
                    class_instance.status = 'completed'
                    class_instance.save(update_fields=['status'])
                
        self.message_user(request, _('Выбранные занятия отмечены как проведенные'))
    mark_as_conducted.short_description = _('Отметить как проведенные')
    
    def mark_as_not_conducted(self, request, queryset):
        """Отмечает выбранные занятия как не проведенные"""
        for tracking in queryset:
            if tracking.is_conducted:
                tracking.is_conducted = False
                tracking.save(update_fields=['is_conducted'])
                
                # Обновляем статус занятия, если оно было помечено как проведенное
                class_instance = tracking.class_instance
                if class_instance.status == 'completed':
                    class_instance.status = 'scheduled'
                    class_instance.save(update_fields=['status'])
                
        self.message_user(request, _('Выбранные занятия отмечены как не проведенные'))
    mark_as_not_conducted.short_description = _('Отметить как не проведенные')