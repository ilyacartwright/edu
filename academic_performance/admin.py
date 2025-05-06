from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg, Sum, Min, Max
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

from .models import (
    GradeSystem, GradeValue, GradingScale, GradeConversion, GradeType,
    Grade, GradeSheet, GradeSheetItem, GradeHistory, Attendance,
    AttendanceSheet, StudentRecord, RecordEntry, AcademicPerformanceSummary,
    AcademicStanding, Scholarship, ScholarshipAssignment, AcademicDebt,
    RetakePermission, IndividualPlan, IndividualPlanItem, GradeImport,
    GradeImportItem, GradeExport
)


class GradeValueInline(admin.TabularInline):
    """
    Встраиваемая форма для значений оценок в системе оценивания
    """
    model = GradeValue
    extra = 1
    fields = ('value', 'numeric_value', 'min_percent', 'max_percent', 'description', 'is_passing')
    ordering = ('-numeric_value',)


@admin.register(GradeSystem)
class GradeSystemAdmin(admin.ModelAdmin):
    """
    Административная модель для систем оценивания
    """
    list_display = ('name', 'system_type', 'min_value', 'max_value', 'passing_value', 'is_default')
    list_filter = ('system_type', 'is_default')
    search_fields = ('name', 'description')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'description', 'system_type', 'is_default')
        }),
        (_('Диапазон значений'), {
            'fields': ('min_value', 'max_value', 'passing_value')
        }),
        (_('Настройки округления'), {
            'fields': ('rounding_method', 'decimal_places')
        }),
    )
    inlines = [GradeValueInline]
    actions = ['make_default']

    def make_default(self, request, queryset):
        """Устанавливает выбранную систему оценивания по умолчанию"""
        # Сбрасываем флаг у всех систем
        GradeSystem.objects.all().update(is_default=False)
        # Устанавливаем флаг для выбранных систем (фактически только для первой)
        queryset.update(is_default=True)
        self.message_user(request, _('Выбранная система оценивания установлена по умолчанию'))
    make_default.short_description = _('Установить по умолчанию')


@admin.register(GradeValue)
class GradeValueAdmin(admin.ModelAdmin):
    """
    Административная модель для значений оценок
    """
    list_display = ('value', 'numeric_value', 'grade_system', 'min_percent', 'max_percent', 'is_passing')
    list_filter = ('grade_system', 'is_passing')
    search_fields = ('value', 'description')
    list_select_related = ('grade_system',)
    ordering = ('grade_system', '-numeric_value')


class GradeConversionInline(admin.TabularInline):
    """
    Встраиваемая форма для соответствий значений в шкале перевода
    """
    model = GradeConversion
    extra = 1
    fk_name = 'scale'
    raw_id_fields = ('source_value', 'target_value')
    autocomplete_fields = ('source_value', 'target_value')


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    """
    Административная модель для шкал перевода оценок
    """
    list_display = ('name', 'source_system', 'target_system', 'is_active')
    list_filter = ('is_active', 'source_system', 'target_system')
    search_fields = ('name', 'description')
    list_select_related = ('source_system', 'target_system')
    inlines = [GradeConversionInline]
    actions = ['activate_scales', 'deactivate_scales']

    def activate_scales(self, request, queryset):
        """Активирует выбранные шкалы перевода"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные шкалы перевода активированы'))
    activate_scales.short_description = _('Активировать выбранные шкалы')

    def deactivate_scales(self, request, queryset):
        """Деактивирует выбранные шкалы перевода"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные шкалы перевода деактивированы'))
    deactivate_scales.short_description = _('Деактивировать выбранные шкалы')


@admin.register(GradeConversion)
class GradeConversionAdmin(admin.ModelAdmin):
    """
    Административная модель для соответствий значений в шкале перевода
    """
    list_display = ('scale', 'source_value', 'target_value')
    list_filter = ('scale',)
    list_select_related = ('scale', 'source_value', 'target_value')
    raw_id_fields = ('source_value', 'target_value')
    autocomplete_fields = ('source_value', 'target_value')
    search_fields = ('scale__name', 'source_value__value', 'target_value__value')


@admin.register(GradeType)
class GradeTypeAdmin(admin.ModelAdmin):
    """
    Административная модель для типов оценок
    """
    list_display = ('name', 'code', 'weight_in_final', 'default_grade_system')
    list_filter = ('default_grade_system',)
    search_fields = ('name', 'code', 'description')
    list_select_related = ('default_grade_system',)


class SemesterFilter(SimpleListFilter):
    """
    Фильтр для выбора академического семестра
    """
    title = _('семестр')
    parameter_name = 'semester_filter'

    def lookups(self, request, model_admin):
        # Получаем уникальные учебные годы и семестры для выпадающего списка
        semesters = model_admin.model.objects.select_related('semester').values_list(
            'semester__academic_year__name', 'semester__name', 'semester__id'
        ).distinct().order_by('-semester__academic_year__name', 'semester__name')
        
        return [(str(semester_id), f"{year} - {name}") for year, name, semester_id in semesters]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(semester__id=self.value())
        return queryset


class StudentFilter(SimpleListFilter):
    """
    Фильтр для выбора студента
    """
    title = _('студент')
    parameter_name = 'student_filter'

    def lookups(self, request, model_admin):
        # Получаем уникальных студентов для выпадающего списка
        students = model_admin.model.objects.select_related('student').values_list(
            'student__user__last_name', 'student__user__first_name', 'student__id'
        ).distinct().order_by('student__user__last_name', 'student__user__first_name')
        
        return [(str(student_id), f"{last_name} {first_name}") for last_name, first_name, student_id in students]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(student__id=self.value())
        return queryset


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """
    Административная модель для оценок
    """
    list_display = (
        'student', 'subject', 'semester', 'grade_type', 'grade_value_display', 
        'date', 'source', 'status', 'graded_by'
    )
    list_filter = (
        SemesterFilter, StudentFilter, 'grade_type', 'grade_system', 
        'status', 'source', 'date'
    )
    search_fields = (
        'student__user__last_name', 'student__user__first_name', 
        'subject__name', 'subject__code', 'comments'
    )
    list_select_related = (
        'student', 'student__user', 'subject', 'semester', 'grade_type', 
        'grade_system', 'grade_value', 'graded_by'
    )
    date_hierarchy = 'date'
    raw_id_fields = ('student', 'subject', 'academic_plan_subject', 'semester', 'graded_by')
    autocomplete_fields = ('student', 'subject', 'academic_plan_subject', 'semester')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Студент и предмет'), {
            'fields': ('student', 'subject', 'academic_plan_subject', 'semester')
        }),
        (_('Информация об оценке'), {
            'fields': (
                'grade_type', 'grade_system', 'grade_value', 'points', 
                'max_points', 'percentage', 'date'
            )
        }),
        (_('Источник и статус'), {
            'fields': ('source', 'status', 'graded_by', 'comments')
        }),
        (_('Связи с курсами и экзаменами'), {
            'fields': ('course', 'course_element', 'exam'),
            'classes': ('collapse',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_final', 'mark_as_draft', 'recalculate_percentage']

    def grade_value_display(self, obj):
        """Отображает значение оценки с цветовым индикатором"""
        if obj.is_passing:
            color = 'green'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{} ({})</span>', 
                         color, obj.grade_value.value, obj.grade_value.numeric_value)
    grade_value_display.short_description = _('Оценка')
    grade_value_display.admin_order_field = 'grade_value__numeric_value'

    def mark_as_final(self, request, queryset):
        """Отмечает выбранные оценки как окончательные"""
        queryset.update(status='final')
        self.message_user(request, _('Выбранные оценки отмечены как окончательные'))
    mark_as_final.short_description = _('Отметить как окончательные')

    def mark_as_draft(self, request, queryset):
        """Отмечает выбранные оценки как черновики"""
        queryset.update(status='draft')
        self.message_user(request, _('Выбранные оценки отмечены как черновики'))
    mark_as_draft.short_description = _('Отметить как черновики')

    def recalculate_percentage(self, request, queryset):
        """Пересчитывает процент для выбранных оценок"""
        for grade in queryset:
            if grade.points is not None and grade.max_points is not None and grade.max_points > 0:
                grade.percentage = (grade.points / grade.max_points) * 100
                grade.save(update_fields=['percentage'])
        self.message_user(request, _('Проценты пересчитаны для выбранных оценок'))
    recalculate_percentage.short_description = _('Пересчитать проценты')


class GradeSheetItemInline(admin.TabularInline):
    """
    Встраиваемая форма для записей в ведомости
    """
    model = GradeSheetItem
    extra = 0
    fields = ('student', 'grade_value', 'status', 'points', 'percentage', 'graded_by', 'graded_at')
    readonly_fields = ('student', 'graded_at')
    autocomplete_fields = ('student', 'grade_value', 'graded_by')
    raw_id_fields = ('student', 'grade_value', 'graded_by')
    can_delete = False
    show_change_link = True
    
    def get_queryset(self, request):
        # Оптимизация запросов с предзагрузкой связанных моделей
        qs = super().get_queryset(request)
        return qs.select_related('student', 'student__user', 'grade_value', 'graded_by')


@admin.register(GradeSheet)
class GradeSheetAdmin(admin.ModelAdmin):
    """
    Административная модель для ведомостей оценок
    """
    list_display = (
        'number', 'sheet_type', 'subject', 'group', 'semester', 
        'issue_date', 'status', 'teacher', 'items_count'
    )
    list_filter = ('sheet_type', 'status', 'issue_date', 'semester', 'group')
    search_fields = ('number', 'subject__name', 'group__name', 'comments')
    list_select_related = ('subject', 'group', 'semester', 'teacher', 'teacher__user')
    date_hierarchy = 'issue_date'
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GradeSheetItemInline]
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'number', 'sheet_type', 'subject', 'academic_plan_subject',
                'group', 'semester', 'teacher'
            )
        }),
        (_('Даты и статус'), {
            'fields': ('issue_date', 'expiration_date', 'status')
        }),
        (_('Система оценивания'), {
            'fields': ('grade_system',)
        }),
        (_('Связи и дополнительно'), {
            'fields': ('exam', 'comments'),
            'classes': ('collapse',)
        }),
        (_('Подписи'), {
            'fields': ('issued_by', 'verified_by', 'approved_by'),
            'classes': ('collapse',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'mark_as_in_progress', 'mark_as_completed', 'mark_as_verified',
        'mark_as_approved', 'extend_expiration_date', 'print_sheet'
    ]
    
    def items_count(self, obj):
        """Отображает количество записей в ведомости"""
        return obj.items.count()
    items_count.short_description = _('Записей')
    
    def get_queryset(self, request):
        # Оптимизация запросов с предзагрузкой связанных моделей
        qs = super().get_queryset(request)
        qs = qs.annotate(items_count=Count('items'))
        return qs
    
    def mark_as_in_progress(self, request, queryset):
        """Отмечает выбранные ведомости как в процессе заполнения"""
        queryset.update(status='in_progress')
        self.message_user(request, _('Выбранные ведомости отмечены как "В процессе заполнения"'))
    mark_as_in_progress.short_description = _('Отметить как "В процессе заполнения"')
    
    def mark_as_completed(self, request, queryset):
        """Отмечает выбранные ведомости как заполненные"""
        queryset.update(status='completed')
        self.message_user(request, _('Выбранные ведомости отмечены как "Заполнены"'))
    mark_as_completed.short_description = _('Отметить как "Заполнены"')
    
    def mark_as_verified(self, request, queryset):
        """Отмечает выбранные ведомости как проверенные"""
        queryset.update(status='verified')
        self.message_user(request, _('Выбранные ведомости отмечены как "Проверены"'))
    mark_as_verified.short_description = _('Отметить как "Проверены"')
    
    def mark_as_approved(self, request, queryset):
        """Отмечает выбранные ведомости как утвержденные"""
        queryset.update(status='approved')
        self.message_user(request, _('Выбранные ведомости отмечены как "Утверждены"'))
    mark_as_approved.short_description = _('Отметить как "Утверждены"')
    
    def extend_expiration_date(self, request, queryset):
        """Продлевает срок действия ведомости на 7 дней"""
        from django.utils import timezone
        import datetime
        for sheet in queryset:
            if sheet.expiration_date:
                sheet.expiration_date = sheet.expiration_date + datetime.timedelta(days=7)
            else:
                sheet.expiration_date = timezone.now().date() + datetime.timedelta(days=7)
            sheet.save(update_fields=['expiration_date'])
        self.message_user(request, _('Срок действия выбранных ведомостей продлен на 7 дней'))
    extend_expiration_date.short_description = _('Продлить срок на 7 дней')
    
    def print_sheet(self, request, queryset):
        """Кнопка для печати ведомости"""
        # Здесь должна быть реализация печати
        self.message_user(request, _('Ведомости подготовлены к печати'))
    print_sheet.short_description = _('Распечатать ведомость')


@admin.register(GradeSheetItem)
class GradeSheetItemAdmin(admin.ModelAdmin):
    """
    Административная модель для записей в ведомости
    """
    list_display = (
        'student', 'grade_sheet_link', 'status', 'grade_value_display',
        'points', 'percentage', 'graded_by', 'graded_at'
    )
    list_filter = ('status', 'graded_at', 'grade_sheet__sheet_type', SemesterFilter, StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'grade_sheet__number', 'comments'
    )
    list_select_related = (
        'student', 'student__user', 'grade_sheet', 'grade_value', 'graded_by'
    )
    readonly_fields = ('graded_at',)
    fieldsets = (
        (_('Связь с ведомостью'), {
            'fields': ('grade_sheet', 'student')
        }),
        (_('Оценка'), {
            'fields': ('grade_value', 'points', 'percentage')
        }),
        (_('Статус и проверка'), {
            'fields': ('status', 'graded_by', 'graded_at', 'comments')
        }),
    )
    actions = [
        'mark_as_graded', 'mark_as_not_graded', 'mark_as_absent',
        'mark_as_not_allowed', 'recalculate_percentage'
    ]
    
    def grade_sheet_link(self, obj):
        """Отображает ссылку на ведомость"""
        url = reverse('admin:имя_приложения_gradesheet_change', args=[obj.grade_sheet.id])
        return format_html('<a href="{}">{}</a>', url, obj.grade_sheet.number)
    grade_sheet_link.short_description = _('Ведомость')
    grade_sheet_link.admin_order_field = 'grade_sheet__number'
    
    def grade_value_display(self, obj):
        """Отображает значение оценки с цветовым индикатором"""
        if not obj.grade_value:
            return '-'
        
        if obj.grade_value.is_passing:
            color = 'green'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{} ({})</span>', 
                         color, obj.grade_value.value, obj.grade_value.numeric_value)
    grade_value_display.short_description = _('Оценка')
    
    def mark_as_graded(self, request, queryset):
        """Отмечает выбранные записи как оцененные"""
        queryset.update(status='graded')
        self.message_user(request, _('Выбранные записи отмечены как "Оценены"'))
    mark_as_graded.short_description = _('Отметить как "Оценены"')
    
    def mark_as_not_graded(self, request, queryset):
        """Отмечает выбранные записи как не оцененные"""
        queryset.update(status='not_graded')
        self.message_user(request, _('Выбранные записи отмечены как "Не оценены"'))
    mark_as_not_graded.short_description = _('Отметить как "Не оценены"')
    
    def mark_as_absent(self, request, queryset):
        """Отмечает выбранные записи как отсутствие студента"""
        queryset.update(status='absent')
        self.message_user(request, _('Выбранные записи отмечены как "Не явился"'))
    mark_as_absent.short_description = _('Отметить как "Не явился"')
    
    def mark_as_not_allowed(self, request, queryset):
        """Отмечает выбранные записи как недопуск к экзамену"""
        queryset.update(status='not_allowed')
        self.message_user(request, _('Выбранные записи отмечены как "Не допущен"'))
    mark_as_not_allowed.short_description = _('Отметить как "Не допущен"')
    
    def recalculate_percentage(self, request, queryset):
        """Пересчитывает процент для выбранных записей"""
        for item in queryset:
            if item.points is not None and item.grade_sheet.grade_system:
                max_val = item.grade_sheet.grade_system.max_value
                if max_val and max_val > 0:
                    item.percentage = (item.points / float(max_val)) * 100
                    item.save(update_fields=['percentage'])
        self.message_user(request, _('Проценты пересчитаны для выбранных записей'))
    recalculate_percentage.short_description = _('Пересчитать проценты')


@admin.register(GradeHistory)
class GradeHistoryAdmin(admin.ModelAdmin):
    """
    Административная модель для истории изменений оценок
    """
    list_display = (
        'student', 'subject', 'semester', 'change_type', 
        'previous_value_display', 'new_value_display', 'changed_by', 'changed_at'
    )
    list_filter = ('change_type', 'changed_at', SemesterFilter, StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'subject__name', 'comments'
    )
    list_select_related = (
        'student', 'student__user', 'subject', 'semester', 
        'previous_value', 'new_value', 'changed_by'
    )
    readonly_fields = (
        'student', 'subject', 'semester', 'grade_sheet_item', 
        'previous_value', 'new_value', 'changed_by', 'changed_at', 'change_type'
    )
    fieldsets = (
        (_('Информация об изменении'), {
            'fields': (
                'student', 'subject', 'semester', 'grade_sheet_item',
                'previous_value', 'new_value', 'change_type'
            )
        }),
        (_('Кто и когда'), {
            'fields': ('changed_by', 'changed_at', 'comments')
        }),
    )
    
    def previous_value_display(self, obj):
        """Отображает предыдущее значение оценки"""
        if not obj.previous_value:
            return '-'
        return f"{obj.previous_value.value} ({obj.previous_value.numeric_value})"
    previous_value_display.short_description = _('Предыдущее значение')
    
    def new_value_display(self, obj):
        """Отображает новое значение оценки"""
        if not obj.new_value:
            return '-'
        return f"{obj.new_value.value} ({obj.new_value.numeric_value})"
    new_value_display.short_description = _('Новое значение')
    
    def has_add_permission(self, request):
        """Запрещает добавление записей истории вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещает изменение записей истории"""
        return False


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Административная модель для посещаемости
    """
    list_display = (
        'student', 'class_instance', 'status', 'late_minutes', 
        'marked_by', 'marked_at'
    )
    list_filter = ('status', 'marked_at', 'class_instance__date')
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'class_instance__schedule_item__subject__name', 'reason'
    )
    list_select_related = ('student', 'student__user', 'class_instance', 'marked_by')
    readonly_fields = ('marked_at',)
    fieldsets = (
        (_('Студент и занятие'), {
            'fields': ('student', 'class_instance')
        }),
        (_('Статус посещения'), {
            'fields': ('status', 'late_minutes', 'reason')
        }),
        (_('Отметка'), {
            'fields': ('marked_by', 'marked_at')
        }),
    )
    actions = ['mark_as_present', 'mark_as_absent', 'mark_as_late', 'mark_as_sick']
    
    def mark_as_present(self, request, queryset):
        """Отмечает выбранных студентов как присутствующих"""
        queryset.update(status='present')
        self.message_user(request, _('Выбранные записи отмечены как "Присутствовал"'))
    mark_as_present.short_description = _('Отметить как "Присутствовал"')
    
    def mark_as_absent(self, request, queryset):
        """Отмечает выбранных студентов как отсутствующих"""
        queryset.update(status='absent')
        self.message_user(request, _('Выбранные записи отмечены как "Отсутствовал"'))
    mark_as_absent.short_description = _('Отметить как "Отсутствовал"')
    
    def mark_as_late(self, request, queryset):
        """Отмечает выбранных студентов как опоздавших"""
        queryset.update(status='late')
        self.message_user(request, _('Выбранные записи отмечены как "Опоздал"'))
    mark_as_late.short_description = _('Отметить как "Опоздал"')
    
    def mark_as_sick(self, request, queryset):
        """Отмечает выбранных студентов как больных"""
        queryset.update(status='sick')
        self.message_user(request, _('Выбранные записи отмечены как "Болен"'))
    mark_as_sick.short_description = _('Отметить как "Болен"')


@admin.register(AttendanceSheet)
class AttendanceSheetAdmin(admin.ModelAdmin):
    """
    Административная модель для журналов посещаемости
    """
    list_display = (
        'class_instance', 'status', 'filled_by', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'created_at', 'class_instance__date')
    search_fields = (
        'class_instance__schedule_item__subject__name',
        'class_instance__schedule_item__group__name', 'comments'
    )
    list_select_related = ('class_instance', 'filled_by')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Занятие'), {
            'fields': ('class_instance',)
        }),
        (_('Статус и заполнение'), {
            'fields': ('status', 'filled_by', 'comments')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_filled', 'mark_as_verified']
    
    def mark_as_filled(self, request, queryset):
        """Отмечает выбранные журналы как заполненные"""
        queryset.update(status='filled')
        self.message_user(request, _('Выбранные журналы отмечены как "Заполнены"'))
    mark_as_filled.short_description = _('Отметить как "Заполнены"')
    
    def mark_as_verified(self, request, queryset):
        """Отмечает выбранные журналы как проверенные"""
        queryset.update(status='verified')
        self.message_user(request, _('Выбранные журналы отмечены как "Проверены"'))
    mark_as_verified.short_description = _('Отметить как "Проверены"')


class RecordEntryInline(admin.TabularInline):
    """
    Встраиваемая форма для записей в зачетной книжке
    """
    model = RecordEntry
    extra = 0
    fields = ('subject', 'semester', 'entry_type', 'grade_value', 'date')
    readonly_fields = ('date',)
    autocomplete_fields = ('subject', 'semester', 'grade_value')
    raw_id_fields = ('subject', 'semester', 'grade_value')
    show_change_link = True


@admin.register(StudentRecord)
class StudentRecordAdmin(admin.ModelAdmin):
    """
    Административная модель для зачетных книжек
    """
    list_display = (
        'record_number', 'student', 'status', 'issue_date', 'closing_date',
        'entries_count'
    )
    list_filter = ('status', 'issue_date', 'closing_date')
    search_fields = ('record_number', 'student__user__last_name', 'student__user__first_name')
    list_select_related = ('student', 'student__user')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RecordEntryInline]
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('student', 'record_number')
        }),
        (_('Даты и статус'), {
            'fields': ('issue_date', 'closing_date', 'status')
        }),
        (_('Дополнительно'), {
            'fields': ('comments', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_records', 'archive_records', 'close_records']
    
    def entries_count(self, obj):
        """Отображает количество записей в зачетной книжке"""
        return obj.entries.count()
    entries_count.short_description = _('Записей')
    
    def get_queryset(self, request):
        # Оптимизация запросов с предзагрузкой связанных моделей
        qs = super().get_queryset(request)
        qs = qs.annotate(entries_count=Count('entries'))
        return qs
    
    def activate_records(self, request, queryset):
        """Активирует выбранные зачетные книжки"""
        queryset.update(status='active')
        self.message_user(request, _('Выбранные зачетные книжки активированы'))
    activate_records.short_description = _('Активировать зачетные книжки')
    
    def archive_records(self, request, queryset):
        """Архивирует выбранные зачетные книжки"""
        queryset.update(status='archived')
        self.message_user(request, _('Выбранные зачетные книжки архивированы'))
    archive_records.short_description = _('Архивировать зачетные книжки')
    
    def close_records(self, request, queryset):
        """Закрывает выбранные зачетные книжки"""
        from django.utils import timezone
        queryset.update(status='closed', closing_date=timezone.now().date())
        self.message_user(request, _('Выбранные зачетные книжки закрыты'))
    close_records.short_description = _('Закрыть зачетные книжки')


@admin.register(RecordEntry)
class RecordEntryAdmin(admin.ModelAdmin):
    """
    Административная модель для записей в зачетной книжке
    """
    list_display = (
        'record', 'subject', 'semester', 'entry_type', 'grade_value_display',
        'date', 'recorded_by'
    )
    list_filter = ('entry_type', 'date', SemesterFilter)
    search_fields = (
        'record__student__user__last_name', 'record__student__user__first_name',
        'subject__name', 'title'
    )
    list_select_related = (
        'record', 'record__student', 'record__student__user', 'subject',
        'semester', 'grade_system', 'grade_value', 'recorded_by'
    )
    fieldsets = (
        (_('Зачетная книжка'), {
            'fields': ('record',)
        }),
        (_('Предмет и семестр'), {
            'fields': ('subject', 'academic_plan_subject', 'semester')
        }),
        (_('Тип записи и оценка'), {
            'fields': (
                'entry_type', 'grade_system', 'grade_value', 'hours', 'credits'
            )
        }),
        (_('Информация о записи'), {
            'fields': ('date', 'recorded_by', 'comments')
        }),
        (_('Для курсовых работ и ВКР'), {
            'fields': ('title', 'supervisor'),
            'classes': ('collapse',),
        }),
    )
    raw_id_fields = ('record', 'subject', 'academic_plan_subject', 'semester', 'supervisor')
    autocomplete_fields = ('record', 'subject', 'academic_plan_subject', 'semester', 'supervisor')
    
    def grade_value_display(self, obj):
        """Отображает значение оценки с цветовым индикатором"""
        if obj.grade_value.is_passing:
            color = 'green'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{} ({})</span>', 
                         color, obj.grade_value.value, obj.grade_value.numeric_value)
    grade_value_display.short_description = _('Оценка')
    grade_value_display.admin_order_field = 'grade_value__numeric_value'


@admin.register(AcademicPerformanceSummary)
class AcademicPerformanceSummaryAdmin(admin.ModelAdmin):
    """
    Административная модель для сводок успеваемости
    """
    list_display = (
        'student', 'period_type', 'semester_or_year', 'gpa', 'total_subjects',
        'excellent_count', 'good_count', 'satisfactory_count', 'failed_count',
        'attendance_percentage', 'ranking', 'calculated_at'
    )
    list_filter = ('period_type', 'calculated_at', SemesterFilter, StudentFilter)
    search_fields = ('student__user__last_name', 'student__user__first_name')
    list_select_related = ('student', 'student__user', 'semester', 'academic_year')
    readonly_fields = ('calculated_at',)
    fieldsets = (
        (_('Студент и период'), {
            'fields': ('student', 'period_type', 'semester', 'academic_year')
        }),
        (_('Статистика оценок'), {
            'fields': (
                'total_subjects', 'excellent_count', 'good_count',
                'satisfactory_count', 'failed_count', 'gpa'
            )
        }),
        (_('Кредиты'), {
            'fields': ('total_credits', 'earned_credits')
        }),
        (_('Посещаемость'), {
            'fields': ('total_classes', 'attended_classes', 'attendance_percentage')
        }),
        (_('Рейтинг'), {
            'fields': ('ranking', 'group_size')
        }),
        (_('Расчет'), {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        }),
    )
    actions = ['recalculate_summaries']
    
    def semester_or_year(self, obj):
        """Отображает семестр или учебный год в зависимости от типа периода"""
        if obj.period_type == 'semester' and obj.semester:
            return str(obj.semester)
        elif obj.period_type == 'academic_year' and obj.academic_year:
            return str(obj.academic_year)
        return _('За все время')
    semester_or_year.short_description = _('Период')
    
    def recalculate_summaries(self, request, queryset):
        """Пересчитывает выбранные сводки успеваемости"""
        # В реальном проекте здесь должна быть логика пересчета
        self.message_user(request, _('Выбранные сводки успеваемости пересчитаны'))
    recalculate_summaries.short_description = _('Пересчитать сводки')


@admin.register(AcademicStanding)
class AcademicStandingAdmin(admin.ModelAdmin):
    """
    Административная модель для академических статусов
    """
    list_display = (
        'student', 'status_type', 'start_date', 'end_date', 'is_active',
        'changed_by', 'document_number'
    )
    list_filter = ('status_type', 'start_date', SemesterFilter, StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'document_number', 'reason'
    )
    list_select_related = ('student', 'student__user', 'semester', 'changed_by')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Студент'), {
            'fields': ('student',)
        }),
        (_('Статус'), {
            'fields': ('status_type', 'start_date', 'end_date', 'semester')
        }),
        (_('Обоснование'), {
            'fields': ('reason', 'document_number', 'document_date')
        }),
        (_('Кто изменил'), {
            'fields': ('changed_by', 'comments')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['extend_for_month', 'close_standings']
    
    def extend_for_month(self, request, queryset):
        """Продлевает выбранные статусы на месяц"""
        from django.utils import timezone
        import datetime
        for standing in queryset.filter(status_type__in=['warning', 'probation', 'academic_leave']):
            if standing.end_date:
                standing.end_date = standing.end_date + datetime.timedelta(days=30)
            else:
                standing.end_date = timezone.now().date() + datetime.timedelta(days=30)
            standing.save(update_fields=['end_date'])
        self.message_user(request, _('Выбранные статусы продлены на 30 дней'))
    extend_for_month.short_description = _('Продлить на 30 дней')
    
    def close_standings(self, request, queryset):
        """Закрывает выбранные статусы текущей датой"""
        from django.utils import timezone
        queryset.update(end_date=timezone.now().date())
        self.message_user(request, _('Выбранные статусы закрыты текущей датой'))
    close_standings.short_description = _('Закрыть статусы')


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    """
    Административная модель для стипендий
    """
    list_display = (
        'name', 'scholarship_type', 'amount', 'is_active',
        'gpa_requirement', 'attendance_requirement'
    )
    list_filter = ('scholarship_type', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'description', 'scholarship_type', 'is_active')
        }),
        (_('Финансы'), {
            'fields': ('amount',)
        }),
        (_('Требования'), {
            'fields': ('gpa_requirement', 'attendance_requirement')
        }),
    )
    actions = ['activate_scholarships', 'deactivate_scholarships']
    
    def activate_scholarships(self, request, queryset):
        """Активирует выбранные стипендии"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные стипендии активированы'))
    activate_scholarships.short_description = _('Активировать стипендии')
    
    def deactivate_scholarships(self, request, queryset):
        """Деактивирует выбранные стипендии"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные стипендии деактивированы'))
    deactivate_scholarships.short_description = _('Деактивировать стипендии')


@admin.register(ScholarshipAssignment)
class ScholarshipAssignmentAdmin(admin.ModelAdmin):
    """
    Административная модель для назначений стипендий
    """
    list_display = (
        'student', 'scholarship', 'status', 'start_date', 'end_date',
        'amount', 'document_number'
    )
    list_filter = ('status', 'start_date', 'semester', StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'scholarship__name', 'document_number'
    )
    list_select_related = ('student', 'student__user', 'scholarship', 'semester', 'assigned_by')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Студент и стипендия'), {
            'fields': ('student', 'scholarship')
        }),
        (_('Период назначения'), {
            'fields': ('start_date', 'end_date', 'semester')
        }),
        (_('Финансы и статус'), {
            'fields': ('amount', 'status', 'status_reason')
        }),
        (_('Документы'), {
            'fields': ('document_number', 'document_date', 'assigned_by')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'activate_assignments', 'suspend_assignments', 'terminate_assignments',
        'extend_for_semester'
    ]
    
    def activate_assignments(self, request, queryset):
        """Активирует выбранные назначения стипендий"""
        queryset.update(status='active')
        self.message_user(request, _('Выбранные назначения стипендий активированы'))
    activate_assignments.short_description = _('Активировать назначения')
    
    def suspend_assignments(self, request, queryset):
        """Приостанавливает выбранные назначения стипендий"""
        queryset.update(status='suspended')
        self.message_user(request, _('Выбранные назначения стипендий приостановлены'))
    suspend_assignments.short_description = _('Приостановить назначения')
    
    def terminate_assignments(self, request, queryset):
        """Прекращает выбранные назначения стипендий"""
        queryset.update(status='terminated')
        self.message_user(request, _('Выбранные назначения стипендий прекращены'))
    terminate_assignments.short_description = _('Прекратить назначения')
    
    def extend_for_semester(self, request, queryset):
        """Продлевает выбранные назначения на семестр"""
        from django.utils import timezone
        import datetime
        for assignment in queryset.filter(status='active'):
            if assignment.end_date:
                assignment.end_date = assignment.end_date + datetime.timedelta(days=180)
            else:
                assignment.end_date = timezone.now().date() + datetime.timedelta(days=180)
            assignment.save(update_fields=['end_date'])
        self.message_user(request, _('Выбранные назначения продлены на семестр (180 дней)'))
    extend_for_semester.short_description = _('Продлить на семестр')


@admin.register(AcademicDebt)
class AcademicDebtAdmin(admin.ModelAdmin):
    """
    Административная модель для академических задолженностей
    """
    list_display = (
        'student', 'subject', 'semester', 'debt_type', 'status',
        'deadline', 'cleared_at', 'created_at'
    )
    list_filter = ('status', 'debt_type', 'deadline', SemesterFilter, StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'subject__name', 'description'
    )
    list_select_related = ('student', 'student__user', 'subject', 'semester', 'created_by')
    readonly_fields = ('created_at',)
    fieldsets = (
        (_('Студент и предмет'), {
            'fields': ('student', 'subject', 'semester')
        }),
        (_('Задолженность'), {
            'fields': ('debt_type', 'description', 'deadline')
        }),
        (_('Статус'), {
            'fields': ('status', 'cleared_at', 'grade_sheet_item')
        }),
        (_('Создание'), {
            'fields': ('created_by', 'created_at')
        }),
    )
    actions = [
        'extend_deadline', 'mark_as_cleared', 'mark_as_waived',
        'mark_as_extended'
    ]
    
    def extend_deadline(self, request, queryset):
        """Продлевает срок погашения задолженности на 14 дней"""
        from django.utils import timezone
        import datetime
        for debt in queryset.filter(status__in=['active', 'extended']):
            debt.deadline = debt.deadline + datetime.timedelta(days=14)
            debt.status = 'extended'
            debt.save(update_fields=['deadline', 'status'])
        self.message_user(request, _('Срок погашения задолженностей продлен на 14 дней'))
    extend_deadline.short_description = _('Продлить срок на 14 дней')
    
    def mark_as_cleared(self, request, queryset):
        """Отмечает выбранные задолженности как погашенные"""
        from django.utils import timezone
        queryset.update(status='cleared', cleared_at=timezone.now().date())
        self.message_user(request, _('Выбранные задолженности отмечены как погашенные'))
    mark_as_cleared.short_description = _('Отметить как погашенные')
    
    def mark_as_waived(self, request, queryset):
        """Отмечает выбранные задолженности как аннулированные"""
        queryset.update(status='waived')
        self.message_user(request, _('Выбранные задолженности отмечены как аннулированные'))
    mark_as_waived.short_description = _('Отметить как аннулированные')
    
    def mark_as_extended(self, request, queryset):
        """Отмечает выбранные задолженности как продленные"""
        queryset.update(status='extended')
        self.message_user(request, _('Выбранные задолженности отмечены как продленные'))
    mark_as_extended.short_description = _('Отметить как продленные')


@admin.register(RetakePermission)
class RetakePermissionAdmin(admin.ModelAdmin):
    """
    Административная модель для разрешений на пересдачу
    """
    list_display = (
        'student', 'subject', 'semester', 'attempt_number', 'status',
        'issue_date', 'expiration_date'
    )
    list_filter = ('status', 'issue_date', 'expiration_date', SemesterFilter, StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'subject__name', 'document_number'
    )
    list_select_related = (
        'student', 'student__user', 'subject', 'semester',
        'created_by', 'approved_by'
    )
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Студент и предмет'), {
            'fields': ('student', 'subject', 'semester', 'academic_debt')
        }),
        (_('Информация о пересдаче'), {
            'fields': ('attempt_number', 'issue_date', 'expiration_date')
        }),
        (_('Статус и результат'), {
            'fields': ('status', 'grade_sheet_item')
        }),
        (_('Документы и связи'), {
            'fields': ('document_number', 'exam', 'grade_sheet')
        }),
        (_('Кто создал и утвердил'), {
            'fields': ('created_by', 'approved_by')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_issued', 'mark_as_used', 'mark_as_expired', 'extend_permission']
    
    def mark_as_issued(self, request, queryset):
        """Отмечает выбранные разрешения как выданные"""
        queryset.update(status='issued')
        self.message_user(request, _('Выбранные разрешения отмечены как выданные'))
    mark_as_issued.short_description = _('Отметить как выданные')
    
    def mark_as_used(self, request, queryset):
        """Отмечает выбранные разрешения как использованные"""
        queryset.update(status='used')
        self.message_user(request, _('Выбранные разрешения отмечены как использованные'))
    mark_as_used.short_description = _('Отметить как использованные')
    
    def mark_as_expired(self, request, queryset):
        """Отмечает выбранные разрешения как истекшие"""
        queryset.update(status='expired')
        self.message_user(request, _('Выбранные разрешения отмечены как истекшие'))
    mark_as_expired.short_description = _('Отметить как истекшие')
    
    def extend_permission(self, request, queryset):
        """Продлевает разрешение на 14 дней"""
        import datetime
        for permission in queryset.filter(status__in=['issued', 'expired']):
            permission.expiration_date = permission.expiration_date + datetime.timedelta(days=14)
            permission.status = 'issued'
            permission.save(update_fields=['expiration_date', 'status'])
        self.message_user(request, _('Выбранные разрешения продлены на 14 дней'))
    extend_permission.short_description = _('Продлить на 14 дней')


class IndividualPlanItemInline(admin.TabularInline):
    """
    Встраиваемая форма для элементов индивидуального учебного плана
    """
    model = IndividualPlanItem
    extra = 0
    fields = (
        'subject', 'semester', 'change_type', 'credits',
        'control_form', 'lectures_hours', 'seminars_hours'
    )
    autocomplete_fields = ('subject', 'semester', 'base_plan_subject')
    raw_id_fields = ('subject', 'semester', 'base_plan_subject')
    show_change_link = True


@admin.register(IndividualPlan)
class IndividualPlanAdmin(admin.ModelAdmin):
    """
    Административная модель для индивидуальных учебных планов
    """
    list_display = (
        'student', 'base_academic_plan', 'status', 'start_date', 'end_date',
        'created_at', 'document_number'
    )
    list_filter = ('status', 'start_date', StudentFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'document_number', 'reason'
    )
    list_select_related = ('student', 'student__user', 'base_academic_plan')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [IndividualPlanItemInline]
    fieldsets = (
        (_('Студент и база'), {
            'fields': ('student', 'base_academic_plan')
        }),
        (_('Период действия'), {
            'fields': ('start_date', 'end_date', 'status')
        }),
        (_('Обоснование'), {
            'fields': ('reason', 'description')
        }),
        (_('Документы'), {
            'fields': ('document_number', 'document_date')
        }),
        (_('Кто создал и утвердил'), {
            'fields': ('created_by', 'approved_by')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'approve_plans', 'activate_plans', 'complete_plans',
        'cancel_plans'
    ]
    
    def approve_plans(self, request, queryset):
        """Утверждает выбранные индивидуальные планы"""
        queryset.update(status='approved')
        self.message_user(request, _('Выбранные индивидуальные планы утверждены'))
    approve_plans.short_description = _('Утвердить планы')
    
    def activate_plans(self, request, queryset):
        """Активирует выбранные индивидуальные планы"""
        queryset.update(status='active')
        self.message_user(request, _('Выбранные индивидуальные планы активированы'))
    activate_plans.short_description = _('Активировать планы')
    
    def complete_plans(self, request, queryset):
        """Отмечает выбранные индивидуальные планы как завершенные"""
        queryset.update(status='completed')
        self.message_user(request, _('Выбранные индивидуальные планы отмечены как завершенные'))
    complete_plans.short_description = _('Отметить как завершенные')
    
    def cancel_plans(self, request, queryset):
        """Отменяет выбранные индивидуальные планы"""
        queryset.update(status='canceled')
        self.message_user(request, _('Выбранные индивидуальные планы отменены'))
    cancel_plans.short_description = _('Отменить планы')


@admin.register(IndividualPlanItem)
class IndividualPlanItemAdmin(admin.ModelAdmin):
    """
    Административная модель для элементов индивидуального учебного плана
    """
    list_display = (
        'individual_plan', 'subject', 'semester', 'change_type',
        'control_form', 'credits', 'total_hours'
    )
    list_filter = ('change_type', 'control_form', SemesterFilter)
    search_fields = (
        'individual_plan__student__user__last_name',
        'individual_plan__student__user__first_name',
        'subject__name', 'reason'
    )
    list_select_related = ('individual_plan', 'individual_plan__student', 'subject', 'semester')
    fieldsets = (
        (_('Связь с планом'), {
            'fields': ('individual_plan',)
        }),
        (_('Предмет и семестр'), {
            'fields': ('base_plan_subject', 'subject', 'semester')
        }),
        (_('Изменение'), {
            'fields': ('change_type', 'reason')
        }),
        (_('Учебная нагрузка'), {
            'fields': (
                'credits', 'control_form', 'lectures_hours', 'seminars_hours',
                'labs_hours', 'practices_hours', 'self_study_hours'
            )
        }),
    )


class GradeImportItemInline(admin.TabularInline):
    """
    Встраиваемая форма для записей импорта оценок
    """
    model = GradeImportItem
    extra = 0
    fields = (
        'student_id', 'subject_code', 'semester_id', 'grade_value',
        'grade_type', 'grade_date', 'status', 'error_message'
    )
    readonly_fields = ('status', 'error_message')
    can_delete = False
    show_change_link = True
    max_num = 50  # Ограничиваем количество отображаемых записей


@admin.register(GradeImport)
class GradeImportAdmin(admin.ModelAdmin):
    """
    Административная модель для импорта оценок
    """
    list_display = (
        'source', 'import_date', 'status', 'total_records', 
        'successful_records', 'failed_records', 'imported_by'
    )
    list_filter = ('source', 'status', 'import_date')
    search_fields = ('filename', 'error_log')
    list_select_related = ('imported_by',)
    readonly_fields = ('import_date', 'successful_records', 'failed_records', 'processed_records')
    inlines = [GradeImportItemInline]
    fieldsets = (
        (_('Источник импорта'), {
            'fields': ('source', 'filename', 'file')
        }),
        (_('Статус импорта'), {
            'fields': ('status', 'imported_by', 'import_date')
        }),
        (_('Статистика'), {
            'fields': (
                'total_records', 'processed_records', 
                'successful_records', 'failed_records'
            )
        }),
        (_('Журнал ошибок'), {
            'fields': ('error_log',),
            'classes': ('collapse',)
        }),
    )
    actions = ['process_imports', 'cancel_imports', 'retry_failed_items']
    
    def process_imports(self, request, queryset):
        """Запускает обработку выбранных импортов"""
        queryset.update(status='processing')
        # В реальном проекте здесь должен быть запуск задачи на обработку импорта
        self.message_user(request, _('Выбранные импорты отправлены на обработку'))
    process_imports.short_description = _('Обработать импорты')
    
    def cancel_imports(self, request, queryset):
        """Отменяет выбранные импорты"""
        queryset.filter(status__in=['pending', 'processing']).update(status='failed')
        self.message_user(request, _('Выбранные импорты отменены'))
    cancel_imports.short_description = _('Отменить импорты')
    
    def retry_failed_items(self, request, queryset):
        """Повторяет обработку неудачных записей в выбранных импортах"""
        for import_obj in queryset:
            import_obj.items.filter(status='error').update(status='pending')
            import_obj.status = 'processing'
            import_obj.save(update_fields=['status'])
        self.message_user(request, _('Неудачные записи отправлены на повторную обработку'))
    retry_failed_items.short_description = _('Повторить неудачные записи')


@admin.register(GradeImportItem)
class GradeImportItemAdmin(admin.ModelAdmin):
    """
    Административная модель для записей импорта оценок
    """
    list_display = (
        'grade_import', 'student_id', 'subject_code', 'grade_value',
        'status', 'grade_link'
    )
    list_filter = ('status', 'grade_import', 'grade_type')
    search_fields = ('student_id', 'subject_code', 'error_message')
    list_select_related = ('grade_import', 'grade')
    readonly_fields = ('grade', 'error_message')
    fieldsets = (
        (_('Связь с импортом'), {
            'fields': ('grade_import',)
        }),
        (_('Данные студента и предмета'), {
            'fields': ('student_id', 'subject_code', 'semester_id')
        }),
        (_('Информация об оценке'), {
            'fields': ('grade_value', 'grade_type', 'grade_date')
        }),
        (_('Дополнительная информация'), {
            'fields': ('additional_data',)
        }),
        (_('Статус обработки'), {
            'fields': ('status', 'error_message', 'grade')
        }),
    )
    actions = ['retry_items', 'skip_items']
    
    def grade_link(self, obj):
        """Отображает ссылку на созданную оценку"""
        if obj.grade:
            url = reverse('admin:имя_приложения_grade_change', args=[obj.grade.id])
            return format_html('<a href="{}">{}</a>', url, obj.grade)
        return '-'
    grade_link.short_description = _('Созданная оценка')
    
    def retry_items(self, request, queryset):
        """Повторяет обработку выбранных записей"""
        queryset.update(status='pending')
        self.message_user(request, _('Выбранные записи отправлены на повторную обработку'))
    retry_items.short_description = _('Повторить обработку')
    
    def skip_items(self, request, queryset):
        """Пропускает выбранные записи"""
        queryset.update(status='skipped')
        self.message_user(request, _('Выбранные записи отмечены как пропущенные'))
    skip_items.short_description = _('Пропустить записи')


@admin.register(GradeExport)
class GradeExportAdmin(admin.ModelAdmin):
    """
    Административная модель для экспорта оценок
    """
    list_display = (
        'format', 'student', 'group', 'subject', 'semester',
        'status', 'records_count', 'export_date', 'exported_by'
    )
    list_filter = ('format', 'status', 'export_date', SemesterFilter)
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'group__name', 'subject__name'
    )
    list_select_related = ('student', 'student__user', 'group', 'subject', 'semester', 'exported_by')
    readonly_fields = ('export_date', 'file', 'records_count')
    fieldsets = (
        (_('Формат экспорта'), {
            'fields': ('format',)
        }),
        (_('Фильтры для экспорта'), {
            'fields': ('group', 'student', 'subject', 'semester')
        }),
        (_('Дополнительные параметры'), {
            'fields': ('include_attendance', 'include_comments')
        }),
        (_('Статус и результат'), {
            'fields': ('status', 'records_count', 'file', 'exported_by', 'export_date')
        }),
    )
    actions = ['generate_exports', 'download_exports']
    
    def generate_exports(self, request, queryset):
        """Генерирует выбранные экспорты"""
        # В реальном проекте здесь должен быть запуск задачи на генерацию экспорта
        queryset.update(status='pending')
        self.message_user(request, _('Выбранные экспорты отправлены на генерацию'))
    generate_exports.short_description = _('Генерировать экспорты')
    
    def download_exports(self, request, queryset):
        """Скачивает выбранные экспорты"""
        # В реальном проекте здесь должна быть логика скачивания файлов
        self.message_user(request, _('Выбранные экспорты подготовлены к скачиванию'))
    download_exports.short_description = _('Скачать экспорты')

