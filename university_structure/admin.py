from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Faculty, Department, EducationLevel, Specialization, EducationalProfile,
    AcademicPlan, Subject, AcademicPlanSubject, AcademicYear, Semester,
    Group, Subgroup, SubgroupStudent, Holiday, Building, Room, Equipment
)


class DepartmentInline(admin.TabularInline):
    """
    Встраиваемая форма для кафедр факультета
    """
    model = Department
    extra = 1
    fields = ('name', 'short_name', 'code', 'foundation_date', 'is_active')
    show_change_link = True


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    """
    Административная модель для факультетов
    """
    list_display = ('name', 'short_name', 'code', 'foundation_date', 'is_active', 'departments_count')
    list_filter = ('is_active', 'foundation_date')
    search_fields = ('name', 'short_name', 'code', 'description')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'short_name', 'code', 'description')
        }),
        (_('Дополнительно'), {
            'fields': ('foundation_date', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    inlines = [DepartmentInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(departments_count=Count('departments'))
    
    def departments_count(self, obj):
        """Отображает количество кафедр на факультете"""
        return obj.departments_count
    departments_count.short_description = _('Кафедр')
    departments_count.admin_order_field = 'departments_count'
    
    actions = ['activate_faculties', 'deactivate_faculties']
    
    def activate_faculties(self, request, queryset):
        """Активирует выбранные факультеты"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные факультеты активированы'))
    activate_faculties.short_description = _('Активировать факультеты')
    
    def deactivate_faculties(self, request, queryset):
        """Деактивирует выбранные факультеты"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные факультеты деактивированы'))
    deactivate_faculties.short_description = _('Деактивировать факультеты')


class SubjectInline(admin.TabularInline):
    """
    Встраиваемая форма для предметов кафедры
    """
    model = Subject
    extra = 1
    fields = ('name', 'short_name', 'code', 'subject_type')
    show_change_link = True


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Административная модель для кафедр
    """
    list_display = (
        'name', 'short_name', 'code', 'faculty', 'foundation_date',
        'email', 'phone', 'is_active', 'subjects_count'
    )
    list_filter = ('faculty', 'is_active', 'foundation_date')
    search_fields = ('name', 'short_name', 'code', 'description', 'email', 'phone')
    list_select_related = ('faculty',)
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'short_name', 'code', 'faculty', 'description')
        }),
        (_('Контактная информация'), {
            'fields': ('website', 'email', 'phone', 'address', 'room_number')
        }),
        (_('Дополнительно'), {
            'fields': ('foundation_date', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    inlines = [SubjectInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(subjects_count=Count('subjects'))
    
    def subjects_count(self, obj):
        """Отображает количество предметов на кафедре"""
        return obj.subjects_count
    subjects_count.short_description = _('Предметов')
    subjects_count.admin_order_field = 'subjects_count'
    
    actions = ['activate_departments', 'deactivate_departments']
    
    def activate_departments(self, request, queryset):
        """Активирует выбранные кафедры"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные кафедры активированы'))
    activate_departments.short_description = _('Активировать кафедры')
    
    def deactivate_departments(self, request, queryset):
        """Деактивирует выбранные кафедры"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные кафедры деактивированы'))
    deactivate_departments.short_description = _('Деактивировать кафедры')


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    """
    Административная модель для уровней образования
    """
    list_display = ('name', 'code', 'study_duration', 'specializations_count')
    search_fields = ('name', 'code')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(specializations_count=Count('specializations'))
    
    def specializations_count(self, obj):
        """Отображает количество специальностей на данном уровне образования"""
        return obj.specializations_count
    specializations_count.short_description = _('Направлений')
    specializations_count.admin_order_field = 'specializations_count'


class EducationalProfileInline(admin.TabularInline):
    """
    Встраиваемая форма для профилей образовательных программ
    """
    model = EducationalProfile
    extra = 1
    fields = ('name', 'code', 'is_active', 'start_year', 'end_year')
    show_change_link = True


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    """
    Административная модель для направлений подготовки
    """
    list_display = (
        'code', 'name', 'department', 'education_level', 'qualification',
        'is_active', 'profiles_count', 'groups_count'
    )
    list_filter = ('department__faculty', 'department', 'education_level', 'is_active')
    search_fields = ('name', 'code', 'qualification', 'description')
    list_select_related = ('department', 'education_level')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'department', 'education_level')
        }),
        (_('Квалификация и описание'), {
            'fields': ('qualification', 'description')
        }),
        (_('Статус'), {
            'fields': ('is_active',)
        }),
    )
    inlines = [EducationalProfileInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            profiles_count=Count('profiles', distinct=True),
            groups_count=Count('groups', distinct=True)
        )
    
    def profiles_count(self, obj):
        """Отображает количество профилей у направления"""
        return obj.profiles_count
    profiles_count.short_description = _('Профилей')
    profiles_count.admin_order_field = 'profiles_count'
    
    def groups_count(self, obj):
        """Отображает количество групп на направлении"""
        return obj.groups_count
    groups_count.short_description = _('Групп')
    groups_count.admin_order_field = 'groups_count'
    
    actions = ['activate_specializations', 'deactivate_specializations']
    
    def activate_specializations(self, request, queryset):
        """Активирует выбранные направления подготовки"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные направления подготовки активированы'))
    activate_specializations.short_description = _('Активировать направления')
    
    def deactivate_specializations(self, request, queryset):
        """Деактивирует выбранные направления подготовки"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные направления подготовки деактивированы'))
    deactivate_specializations.short_description = _('Деактивировать направления')


@admin.register(EducationalProfile)
class EducationalProfileAdmin(admin.ModelAdmin):
    """
    Административная модель для профилей образовательных программ
    """
    list_display = (
        'name', 'code', 'specialization', 'start_year', 'end_year',
        'is_active', 'plans_count', 'groups_count'
    )
    list_filter = (
        'specialization__department__faculty', 'specialization__department',
        'specialization', 'is_active'
    )
    search_fields = ('name', 'code', 'description')
    list_select_related = ('specialization', 'specialization__department')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            plans_count=Count('academic_plans', distinct=True),
            groups_count=Count('groups', distinct=True)
        )
    
    def plans_count(self, obj):
        """Отображает количество учебных планов в профиле"""
        return obj.plans_count
    plans_count.short_description = _('Планов')
    plans_count.admin_order_field = 'plans_count'
    
    def groups_count(self, obj):
        """Отображает количество групп на профиле"""
        return obj.groups_count
    groups_count.short_description = _('Групп')
    groups_count.admin_order_field = 'groups_count'
    
    actions = ['activate_profiles', 'deactivate_profiles']
    
    def activate_profiles(self, request, queryset):
        """Активирует выбранные профили подготовки"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные профили подготовки активированы'))
    activate_profiles.short_description = _('Активировать профили')
    
    def deactivate_profiles(self, request, queryset):
        """Деактивирует выбранные профили подготовки"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные профили подготовки деактивированы'))
    deactivate_profiles.short_description = _('Деактивировать профили')


class AcademicPlanSubjectInline(admin.TabularInline):
    """
    Встраиваемая форма для предметов учебного плана
    """
    model = AcademicPlanSubject
    extra = 1
    fields = (
        'subject', 'semester', 'credits', 'control_form',
        'lectures_hours', 'seminars_hours', 'labs_hours'
    )
    raw_id_fields = ('subject',)
    autocomplete_fields = ('subject',)
    show_change_link = True


@admin.register(AcademicPlan)
class AcademicPlanAdmin(admin.ModelAdmin):
    """
    Административная модель для учебных планов
    """
    list_display = (
        'specialization', 'profile_display', 'year', 'version',
        'approval_date', 'is_active', 'subjects_count', 'groups_count'
    )
    list_filter = (
        'specialization__department__faculty', 'specialization__department',
        'specialization', 'year', 'is_active'
    )
    search_fields = ('specialization__name', 'profile__name', 'year', 'version', 'description')
    list_select_related = ('specialization', 'profile')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('specialization', 'profile', 'year', 'version')
        }),
        (_('Документы'), {
            'fields': ('approval_date', 'description', 'file')
        }),
        (_('Статус'), {
            'fields': ('is_active',)
        }),
    )
    inlines = [AcademicPlanSubjectInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            subjects_count=Count('subjects', distinct=True),
            groups_count=Count('groups', distinct=True)
        )
    
    def profile_display(self, obj):
        """Отображает профиль образовательной программы"""
        if obj.profile:
            return obj.profile.name
        return _('Без профиля')
    profile_display.short_description = _('Профиль')
    profile_display.admin_order_field = 'profile__name'
    
    def subjects_count(self, obj):
        """Отображает количество предметов в учебном плане"""
        return obj.subjects_count
    subjects_count.short_description = _('Предметов')
    subjects_count.admin_order_field = 'subjects_count'
    
    def groups_count(self, obj):
        """Отображает количество групп на учебном плане"""
        return obj.groups_count
    groups_count.short_description = _('Групп')
    groups_count.admin_order_field = 'groups_count'
    
    actions = ['activate_plans', 'deactivate_plans']
    
    def activate_plans(self, request, queryset):
        """Активирует выбранные учебные планы"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные учебные планы активированы'))
    activate_plans.short_description = _('Активировать планы')
    
    def deactivate_plans(self, request, queryset):
        """Деактивирует выбранные учебные планы"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные учебные планы деактивированы'))
    deactivate_plans.short_description = _('Деактивировать планы')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Административная модель для учебных дисциплин
    """
    list_display = ('name', 'short_name', 'code', 'department', 'subject_type', 'plans_count')
    list_filter = ('department__faculty', 'department', 'subject_type')
    search_fields = ('name', 'short_name', 'code', 'description')
    list_select_related = ('department',)
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'short_name', 'code', 'department')
        }),
        (_('Тип и описание'), {
            'fields': ('subject_type', 'description')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(plans_count=Count('academic_plans', distinct=True))
    
    def plans_count(self, obj):
        """Отображает количество учебных планов, в которых присутствует дисциплина"""
        return obj.plans_count
    plans_count.short_description = _('В учебных планах')
    plans_count.admin_order_field = 'plans_count'


@admin.register(AcademicPlanSubject)
class AcademicPlanSubjectAdmin(admin.ModelAdmin):
    """
    Административная модель для предметов учебного плана
    """
    list_display = (
        'subject', 'academic_plan', 'semester', 'control_form',
        'credits', 'total_hours', 'lectures_hours', 'seminars_hours',
        'labs_hours', 'is_optional'
    )
    list_filter = (
        'academic_plan__specialization__department__faculty',
        'academic_plan__specialization', 'semester', 'control_form', 'is_optional'
    )
    search_fields = ('subject__name', 'subject__code', 'academic_plan__year')
    list_select_related = ('subject', 'academic_plan', 'academic_plan__specialization')
    fieldsets = (
        (_('Связь с учебным планом'), {
            'fields': ('academic_plan', 'subject', 'semester')
        }),
        (_('Нагрузка'), {
            'fields': (
                'lectures_hours', 'seminars_hours', 'labs_hours',
                'practices_hours', 'self_study_hours'
            )
        }),
        (_('Контроль'), {
            'fields': ('credits', 'control_form', 'is_optional')
        }),
    )
    
    actions = ['copy_to_next_semester', 'set_as_optional', 'set_as_required']
    
    def copy_to_next_semester(self, request, queryset):
        """Копирует выбранные предметы в следующий семестр"""
        for item in queryset:
            AcademicPlanSubject.objects.create(
                academic_plan=item.academic_plan,
                subject=item.subject,
                semester=item.semester + 1,
                lectures_hours=item.lectures_hours,
                seminars_hours=item.seminars_hours,
                labs_hours=item.labs_hours,
                practices_hours=item.practices_hours,
                self_study_hours=item.self_study_hours,
                credits=item.credits,
                control_form=item.control_form,
                is_optional=item.is_optional
            )
        self.message_user(request, _(
            'Выбранные предметы скопированы в следующий семестр'
        ))
    copy_to_next_semester.short_description = _('Копировать в следующий семестр')
    
    def set_as_optional(self, request, queryset):
        """Отмечает выбранные предметы как дисциплины по выбору"""
        queryset.update(is_optional=True)
        self.message_user(request, _('Выбранные предметы отмечены как дисциплины по выбору'))
    set_as_optional.short_description = _('Отметить как дисциплины по выбору')
    
    def set_as_required(self, request, queryset):
        """Отмечает выбранные предметы как обязательные дисциплины"""
        queryset.update(is_optional=False)
        self.message_user(request, _('Выбранные предметы отмечены как обязательные дисциплины'))
    set_as_required.short_description = _('Отметить как обязательные дисциплины')


class SemesterInline(admin.TabularInline):
    """
    Встраиваемая форма для семестров учебного года
    """
    model = Semester
    extra = 2
    fields = (
        'number', 'semester_type', 'start_date', 'end_date',
        'class_start_date', 'class_end_date', 'is_current'
    )
    show_change_link = True


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """
    Административная модель для учебных годов
    """
    list_display = ('name', 'start_date', 'end_date', 'is_current', 'semesters_count')
    list_filter = ('is_current',)
    search_fields = ('name',)
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'start_date', 'end_date')
        }),
        (_('Статус'), {
            'fields': ('is_current',)
        }),
    )
    inlines = [SemesterInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(semesters_count=Count('semesters'))
    
    def semesters_count(self, obj):
        """Отображает количество семестров в учебном году"""
        return obj.semesters_count
    semesters_count.short_description = _('Семестров')
    semesters_count.admin_order_field = 'semesters_count'
    
    actions = ['set_as_current']
    
    def set_as_current(self, request, queryset):
        """Устанавливает выбранный учебный год как текущий"""
        # Сбрасываем флаг текущего года у всех годов
        AcademicYear.objects.all().update(is_current=False)
        # Устанавливаем флаг текущего года только для выбранного года
        if queryset.count() > 0:
            queryset[0].is_current = True
            queryset[0].save()
            self.message_user(request, _(
                f'Учебный год {queryset[0].name} установлен как текущий'
            ))
    set_as_current.short_description = _('Установить как текущий учебный год')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    """
    Административная модель для семестров
    """
    list_display = (
        'academic_year', 'number', 'semester_type', 'start_date',
        'end_date', 'class_start_date', 'class_end_date', 'is_current'
    )
    list_filter = ('academic_year', 'semester_type', 'is_current')
    search_fields = ('academic_year__name',)
    list_select_related = ('academic_year',)
    fieldsets = (
        (_('Связь с учебным годом'), {
            'fields': ('academic_year', 'number', 'semester_type')
        }),
        (_('Даты семестра'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Учебные даты'), {
            'fields': ('class_start_date', 'class_end_date')
        }),
        (_('Даты сессии'), {
            'fields': ('exam_start_date', 'exam_end_date')
        }),
        (_('Статус'), {
            'fields': ('is_current',)
        }),
    )
    
    actions = ['set_as_current']
    
    def set_as_current(self, request, queryset):
        """Устанавливает выбранный семестр как текущий"""
        # Сбрасываем флаг текущего семестра у всех семестров
        Semester.objects.all().update(is_current=False)
        # Устанавливаем флаг текущего семестра только для выбранного семестра
        if queryset.count() > 0:
            semester = queryset[0]
            semester.is_current = True
            semester.save()
            
            # Устанавливаем соответствующий учебный год как текущий
            academic_year = semester.academic_year
            AcademicYear.objects.all().update(is_current=False)
            academic_year.is_current = True
            academic_year.save()
            
            self.message_user(request, _(
                f'Семестр {semester.number} ({semester.academic_year.name}) установлен как текущий'
            ))
    set_as_current.short_description = _('Установить как текущий семестр')


class SubgroupInline(admin.TabularInline):
    """
    Встраиваемая форма для подгрупп учебной группы
    """
    model = Subgroup
    extra = 1
    fields = ('name', 'subgroup_type', 'max_students')
    show_change_link = True


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Административная модель для учебных групп
    """
    list_display = (
        'name', 'specialization', 'profile_display', 'year_of_admission',
        'current_semester', 'education_form', 'students_count', 'is_active'
    )
    list_filter = (
        'specialization__department__faculty', 'specialization__department',
        'specialization', 'year_of_admission', 'education_form', 'is_active'
    )
    search_fields = ('name', 'specialization__name', 'profile__name')
    list_select_related = ('specialization', 'profile', 'academic_plan')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'specialization', 'profile', 'academic_plan')
        }),
        (_('Характеристики'), {
            'fields': (
                'year_of_admission', 'current_semester',
                'education_form', 'max_students'
            )
        }),
        (_('Куратор и статус'), {
            'fields': ('curator', 'is_active')
        }),
    )
    inlines = [SubgroupInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Здесь предполагается, что у группы есть связь со студентами через поле 'students'
        # Если эта связь называется иначе, нужно изменить следующую строку
        return qs.annotate(students_count=Count('students', distinct=True))
    
    def profile_display(self, obj):
        """Отображает профиль образовательной программы"""
        if obj.profile:
            return obj.profile.name
        return _('Без профиля')
    profile_display.short_description = _('Профиль')
    profile_display.admin_order_field = 'profile__name'
    
    def students_count(self, obj):
        """Отображает количество студентов в группе"""
        return obj.students_count
    students_count.short_description = _('Студентов')
    students_count.admin_order_field = 'students_count'
    
    actions = ['activate_groups', 'deactivate_groups', 'increase_semester']
    
    def activate_groups(self, request, queryset):
        """Активирует выбранные группы"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные группы активированы'))
    activate_groups.short_description = _('Активировать группы')
    
    def deactivate_groups(self, request, queryset):
        """Деактивирует выбранные группы"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные группы деактивированы'))
    deactivate_groups.short_description = _('Деактивировать группы')
    
    def increase_semester(self, request, queryset):
        """Увеличивает номер текущего семестра на 1"""
        for group in queryset:
            group.current_semester += 1
            group.save(update_fields=['current_semester'])
        self.message_user(request, _('Семестр для выбранных групп увеличен на 1'))
    increase_semester.short_description = _('Увеличить семестр на 1')


class SubgroupStudentInline(admin.TabularInline):
    """
    Встраиваемая форма для студентов подгруппы
    """
    model = SubgroupStudent
    extra = 1
    raw_id_fields = ('student',)
    autocomplete_fields = ('student',)


@admin.register(Subgroup)
class SubgroupAdmin(admin.ModelAdmin):
    """
    Административная модель для подгрупп
    """
    list_display = (
        'name', 'group', 'subgroup_type', 'max_students', 'students_count'
    )
    list_filter = ('group__specialization', 'group', 'subgroup_type')
    search_fields = ('name', 'group__name')
    list_select_related = ('group',)
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'group', 'subgroup_type')
        }),
        (_('Параметры'), {
            'fields': ('max_students',)
        }),
    )
    inlines = [SubgroupStudentInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(students_count=Count('students'))
    
    def students_count(self, obj):
        """Отображает количество студентов в подгруппе"""
        return obj.students_count
    students_count.short_description = _('Студентов')
    students_count.admin_order_field = 'students_count'


@admin.register(SubgroupStudent)
class SubgroupStudentAdmin(admin.ModelAdmin):
    """
    Административная модель для студентов подгрупп
    """
    list_display = ('student', 'subgroup', 'group_link')
    list_filter = ('subgroup__group', 'subgroup')
    search_fields = (
        'student__user__last_name', 'student__user__first_name',
        'subgroup__name', 'subgroup__group__name'
    )
    list_select_related = ('student', 'student__user', 'subgroup', 'subgroup__group')
    
    def group_link(self, obj):
        """Отображает ссылку на группу студента"""
        url = reverse('admin:имя_приложения_group_change', args=[obj.subgroup.group.id])
        return format_html('<a href="{}">{}</a>', url, obj.subgroup.group.name)
    group_link.short_description = _('Группа')
    group_link.admin_order_field = 'subgroup__group__name'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """
    Административная модель для праздничных и выходных дней
    """
    list_display = ('name', 'holiday_type', 'academic_year', 'start_date', 'end_date', 'duration_days')
    list_filter = ('holiday_type', 'academic_year')
    search_fields = ('name',)
    list_select_related = ('academic_year',)
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'holiday_type', 'academic_year')
        }),
        (_('Даты'), {
            'fields': ('start_date', 'end_date')
        }),
    )
    
    def duration_days(self, obj):
        """Отображает продолжительность в днях"""
        delta = obj.end_date - obj.start_date
        return delta.days + 1  # Включаем конечную дату
    duration_days.short_description = _('Продолжительность (дней)')


class RoomInline(admin.TabularInline):
    """
    Встраиваемая форма для аудиторий здания
    """
    model = Room
    extra = 1
    fields = ('number', 'floor', 'room_type', 'capacity', 'is_active')
    show_change_link = True


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    """
    Административная модель для зданий университета
    """
    list_display = ('name', 'number', 'address', 'floors', 'rooms_count')
    list_filter = ('floors',)
    search_fields = ('name', 'number', 'address')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'number', 'address', 'description')
        }),
        (_('Характеристики'), {
            'fields': ('floors',)
        }),
        (_('Геолокация'), {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
    )
    inlines = [RoomInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(rooms_count=Count('rooms'))
    
    def rooms_count(self, obj):
        """Отображает количество аудиторий в здании"""
        return obj.rooms_count
    rooms_count.short_description = _('Аудиторий')
    rooms_count.admin_order_field = 'rooms_count'


class EquipmentInline(admin.TabularInline):
    """
    Встраиваемая форма для оборудования в аудитории
    """
    model = Equipment
    extra = 1
    fields = ('name', 'inventory_number', 'purchase_date', 'last_service_date')
    show_change_link = True


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """
    Административная модель для аудиторий/кабинетов
    """
    list_display = (
        'number', 'building', 'floor', 'room_type', 'capacity',
        'has_projector', 'has_computers', 'computers_count', 'is_active'
    )
    list_filter = ('building', 'floor', 'room_type', 'has_projector', 'has_computers', 'is_active')
    search_fields = ('number', 'building__name', 'description')
    list_select_related = ('building',)
    fieldsets = (
        (_('Расположение'), {
            'fields': ('number', 'building', 'floor')
        }),
        (_('Характеристики'), {
            'fields': ('room_type', 'capacity', 'description')
        }),
        (_('Оборудование'), {
            'fields': ('has_projector', 'has_computers', 'computers_count')
        }),
        (_('Статус'), {
            'fields': ('is_active',)
        }),
    )
    inlines = [EquipmentInline]
    actions = ['activate_rooms', 'deactivate_rooms']
    
    def activate_rooms(self, request, queryset):
        """Активирует выбранные аудитории"""
        queryset.update(is_active=True)
        self.message_user(request, _('Выбранные аудитории активированы'))
    activate_rooms.short_description = _('Активировать аудитории')
    
    def deactivate_rooms(self, request, queryset):
        """Деактивирует выбранные аудитории"""
        queryset.update(is_active=False)
        self.message_user(request, _('Выбранные аудитории деактивированы'))
    deactivate_rooms.short_description = _('Деактивировать аудитории')


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """
    Административная модель для оборудования
    """
    list_display = (
        'name', 'room', 'inventory_number', 'purchase_date', 'last_service_date'
    )
    list_filter = ('room__building', 'room', 'purchase_date', 'last_service_date')
    search_fields = ('name', 'inventory_number', 'room__number', 'description')
    list_select_related = ('room', 'room__building')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'room', 'inventory_number')
        }),
        (_('Описание'), {
            'fields': ('description',)
        }),
        (_('Даты'), {
            'fields': ('purchase_date', 'last_service_date')
        }),
    )