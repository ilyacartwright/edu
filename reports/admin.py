from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from django.contrib.admin.filters import SimpleListFilter

from .models import (
    ReportTemplate, 
    Report, 
    ReportAccess, 
    AcademicPerformanceReport, 
    AttendanceReport, 
    GradeSheet, 
    GradeSheetEntry, 
    Transcript, 
    TeacherWorkloadReport, 
    ContingentReport, 
    ReportScheduledTask, 
    ReportScheduledRun, 
    ReportCategory, 
    ReportDashboard, 
    DashboardWidget, 
    ReportSubscription
)


class ReportCategoryInline(admin.TabularInline):
    """
    Inline admin for report subcategories
    """
    model = ReportCategory
    extra = 1
    fields = ('name', 'icon', 'order', 'is_active')
    fk_name = 'parent'
    verbose_name = _('Subcategory')
    verbose_name_plural = _('Subcategories')


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for report categories
    """
    list_display = ('name', 'parent', 'icon', 'order', 'get_subcategories_count')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    inlines = [ReportCategoryInline]
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.count()
    get_subcategories_count.short_description = _('Subcategories')
    
    def get_queryset(self, request):
        """Only show top-level categories by default"""
        qs = super().get_queryset(request)
        if not request.GET.get('parent__id__exact'):
            return qs.filter(parent__isnull=True)
        return qs


class AvailableForRolesFilter(SimpleListFilter):
    """
    Filter for report templates based on available roles
    """
    title = _('Available For')
    parameter_name = 'available_for'
    
    def lookups(self, request, model_admin):
        return ReportTemplate.ROLE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(available_for__contains=self.value())
        return queryset


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for report templates
    """
    list_display = ('name', 'report_type', 'get_available_for', 'is_active', 'created_at')
    list_filter = ('report_type', AvailableForRolesFilter, 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'report_type')
        }),
        (_('Template Settings'), {
            'fields': ('template_file', 'parameters_schema', 'available_for')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_available_for(self, obj):
        roles = [dict(ReportTemplate.ROLE_CHOICES).get(role) for role in obj.available_for]
        return ', '.join(roles) if roles else _('None')
    get_available_for.short_description = _('Available For')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReportAccessInline(admin.TabularInline):
    """
    Inline admin for report access logs
    """
    model = ReportAccess
    extra = 0
    readonly_fields = ('user', 'accessed_at', 'ip_address', 'user_agent')
    can_delete = False
    max_num = 0
    verbose_name = _('Access Log')
    verbose_name_plural = _('Access Logs')


class ReportStatusFilter(SimpleListFilter):
    """
    Filter for report status
    """
    title = _('Status')
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return Report.STATUS_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin interface for reports
    """
    list_display = ('title', 'report_type', 'created_by', 'created_at', 'status', 'is_public',
                   'get_file_link')
    list_filter = ('report_type', ReportStatusFilter, 'is_public', 'created_at')
    search_fields = ('title', 'created_by__username', 'created_by__first_name', 'created_by__last_name')
    readonly_fields = ('created_at', 'access_code', 'created_by')
    inlines = [ReportAccessInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'template', 'report_type')
        }),
        (_('Report Data'), {
            'fields': ('parameters', 'file', 'content', 'period_start', 'period_end', 'semester')
        }),
        (_('Access Settings'), {
            'fields': ('is_public', 'access_code')
        }),
        (_('Status'), {
            'fields': ('status', 'error_message')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', 
                              obj.file.url, _('View File'))
        return _('No File')
    get_file_link.short_description = _('Report File')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_related_report_details(self, obj):
        """Get the specific report details model instance if exists"""
        related_objects = [
            'academic_performance_details', 
            'attendance_details', 
            'grade_sheet_details', 
            'transcript_details', 
            'workload_details', 
            'contingent_details'
        ]
        
        for related_name in related_objects:
            if hasattr(obj, related_name):
                return getattr(obj, related_name)
        return None
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add related report details to context"""
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['report_details'] = self.get_related_report_details(obj)
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(ReportAccess)
class ReportAccessAdmin(admin.ModelAdmin):
    """
    Admin interface for report access logs
    """
    list_display = ('report', 'user', 'accessed_at', 'ip_address')
    list_filter = ('accessed_at', 'report__report_type')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'report__title')
    readonly_fields = ('report', 'user', 'accessed_at', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class DetailLevelFilter(SimpleListFilter):
    """
    Filter for detail level in reports
    """
    title = _('Detail Level')
    parameter_name = 'detail_level'
    
    def lookups(self, request, model_admin):
        return model_admin.model.DETAIL_LEVEL_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(detail_level=self.value())
        return queryset


@admin.register(AcademicPerformanceReport)
class AcademicPerformanceReportAdmin(admin.ModelAdmin):
    """
    Admin interface for academic performance reports
    """
    list_display = ('base_report', 'detail_level', 'academic_year', 'semester', 'average_grade',
                   'passing_rate')
    list_filter = ('academic_year', 'semester', DetailLevelFilter)
    search_fields = ('base_report__title', 'faculty__name', 'department__name', 'group__name',
                    'student__user__username', 'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('base_report',)
    
    fieldsets = (
        (None, {
            'fields': ('base_report', 'detail_level')
        }),
        (_('Period'), {
            'fields': ('academic_year', 'semester')
        }),
        (_('Report Objects'), {
            'fields': ('faculty', 'department', 'group', 'student', 'subject')
        }),
        (_('Report Data'), {
            'fields': ('data',)
        }),
        (_('Metrics'), {
            'fields': ('average_grade', 'passing_rate', 'excellence_rate', 'failure_rate')
        }),
    )


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    """
    Admin interface for attendance reports
    """
    list_display = ('base_report', 'detail_level', 'academic_year', 'semester', 'attendance_rate')
    list_filter = ('academic_year', 'semester', DetailLevelFilter)
    search_fields = ('base_report__title', 'faculty__name', 'department__name', 'group__name',
                    'student__user__username', 'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('base_report',)
    
    fieldsets = (
        (None, {
            'fields': ('base_report', 'detail_level')
        }),
        (_('Period'), {
            'fields': ('academic_year', 'semester')
        }),
        (_('Report Objects'), {
            'fields': ('faculty', 'department', 'group', 'student', 'subject')
        }),
        (_('Report Data'), {
            'fields': ('data',)
        }),
        (_('Metrics'), {
            'fields': ('attendance_rate', 'absence_rate', 'excused_absence_rate')
        }),
    )


class GradeSheetEntryInline(admin.TabularInline):
    """
    Inline admin for grade sheet entries
    """
    model = GradeSheetEntry
    extra = 0
    fields = ('student', 'grade', 'numeric_grade', 'graded_at', 'graded_by', 'comment')
    readonly_fields = ('graded_at', 'graded_by')
    autocomplete_fields = ('student',)


@admin.register(GradeSheet)
class GradeSheetAdmin(admin.ModelAdmin):
    """
    Admin interface for grade sheets
    """
    list_display = ('number', 'subject', 'group', 'control_form', 'semester', 'date', 'status')
    list_filter = ('status', 'control_form', 'semester', 'date')
    search_fields = ('number', 'subject__name', 'group__name', 'teacher__user__username',
                    'teacher__user__first_name', 'teacher__user__last_name')
    readonly_fields = ('base_report', 'created_at', 'closed_at')
    inlines = [GradeSheetEntryInline]
    
    fieldsets = (
        (None, {
            'fields': ('base_report', 'number')
        }),
        (_('Course Info'), {
            'fields': ('subject', 'group', 'teacher', 'semester', 'control_form')
        }),
        (_('Status'), {
            'fields': ('status', 'date', 'created_at', 'closed_at')
        }),
        (_('Signatures'), {
            'fields': ('signed_by_teacher', 'signed_by_head')
        }),
        (_('Data'), {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """Set graded_by user when saving entries"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, GradeSheetEntry) and instance.grade and not instance.graded_by:
                instance.graded_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(GradeSheetEntry)
class GradeSheetEntryAdmin(admin.ModelAdmin):
    """
    Admin interface for grade sheet entries
    """
    list_display = ('student', 'grade_sheet', 'grade', 'numeric_grade', 'graded_at')
    list_filter = ('grade', 'graded_at', 'grade_sheet__control_form')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name',
                    'grade_sheet__number', 'grade_sheet__subject__name')
    readonly_fields = ('graded_at', 'graded_by')
    autocomplete_fields = ('grade_sheet', 'student')
    
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('grade') and not obj.graded_by:
            obj.graded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    """
    Admin interface for transcripts
    """
    list_display = ('base_report', 'student', 'transcript_number', 'academic_year', 'semester', 'gpa')
    list_filter = ('academic_year', 'semester')
    search_fields = ('base_report__title', 'transcript_number', 'student__user__username',
                    'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('base_report', 'created_at')
    
    fieldsets = (
        (None, {
            'fields': ('base_report', 'student', 'transcript_number')
        }),
        (_('Period'), {
            'fields': ('academic_year', 'semester')
        }),
        (_('Metrics'), {
            'fields': ('gpa', 'ects')
        }),
        (_('Data'), {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeacherWorkloadReport)
class TeacherWorkloadReportAdmin(admin.ModelAdmin):
    """
    Admin interface for teacher workload reports
    """
    list_display = ('base_report', 'get_report_for', 'academic_year', 'semester', 'total_hours')
    list_filter = ('academic_year', 'semester')
    search_fields = ('base_report__title', 'teacher__user__username', 'teacher__user__first_name',
                    'teacher__user__last_name', 'department__name')
    readonly_fields = ('base_report',)
    
    fieldsets = (
        (None, {
            'fields': ('base_report',)
        }),
        (_('Report For'), {
            'fields': ('teacher', 'department')
        }),
        (_('Period'), {
            'fields': ('academic_year', 'semester')
        }),
        (_('Workload Hours'), {
            'fields': ('total_hours', 'lectures_hours', 'seminars_hours', 'labs_hours',
                      'practices_hours', 'consultations_hours', 'exams_hours',
                      'course_works_hours', 'thesis_hours', 'other_hours')
        }),
        (_('Data'), {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
    )
    
    def get_report_for(self, obj):
        if obj.teacher:
            return f"{obj.teacher.user.get_full_name()} ({_('Teacher')})"
        elif obj.department:
            return f"{obj.department.name} ({_('Department')})"
        return _('Not specified')
    get_report_for.short_description = _('Report For')


@admin.register(ContingentReport)
class ContingentReportAdmin(admin.ModelAdmin):
    """
    Admin interface for contingent reports
    """
    list_display = ('base_report', 'detail_level', 'academic_year', 'date', 'total_students')
    list_filter = ('academic_year', 'date', DetailLevelFilter)
    search_fields = ('base_report__title', 'faculty__name', 'department__name',
                    'specialization__name', 'group__name')
    readonly_fields = ('base_report',)
    
    fieldsets = (
        (None, {
            'fields': ('base_report', 'detail_level')
        }),
        (_('Period'), {
            'fields': ('academic_year', 'date')
        }),
        (_('Report Objects'), {
            'fields': ('faculty', 'department', 'specialization', 'group')
        }),
        (_('Student Counts'), {
            'fields': ('total_students', 'budget_students', 'contract_students',
                      'full_time_students', 'part_time_students', 'evening_students',
                      'distance_students')
        }),
        (_('Data'), {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportScheduledTask)
class ReportScheduledTaskAdmin(admin.ModelAdmin):
    """
    Admin interface for scheduled report tasks
    """
    list_display = ('name', 'template', 'recurrence', 'is_active', 'next_run', 'last_run')
    list_filter = ('recurrence', 'is_active', 'template__report_type')
    search_fields = ('name', 'description', 'template__name')
    readonly_fields = ('created_by', 'created_at', 'last_run', 'next_run')
    filter_horizontal = ('recipients',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'template', 'is_active')
        }),
        (_('Parameters'), {
            'fields': ('parameters',)
        }),
        (_('Schedule'), {
            'fields': ('recurrence', 'weekday', 'day_of_month', 'hour', 'minute',
                      'last_run', 'next_run')
        }),
        (_('Recipients'), {
            'fields': ('recipients',)
        }),
        (_('Email Settings'), {
            'fields': ('send_email', 'email_subject', 'email_body')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReportScheduledRun)
class ReportScheduledRunAdmin(admin.ModelAdmin):
    """
    Admin interface for scheduled report runs
    """
    list_display = ('task', 'scheduled_for', 'status', 'started_at', 'finished_at', 'is_sent')
    list_filter = ('status', 'is_sent', 'scheduled_for')
    search_fields = ('task__name', 'error_message')
    readonly_fields = ('task', 'report', 'scheduled_for', 'started_at', 'finished_at',
                      'status', 'error_message', 'is_sent', 'sent_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class DashboardWidgetInline(admin.TabularInline):
    """
    Inline admin for dashboard widgets
    """
    model = DashboardWidget
    extra = 1
    fields = ('title', 'widget_type', 'report', 'position_x', 'position_y', 'width', 'height')
    autocomplete_fields = ('report',)


@admin.register(ReportDashboard)
class ReportDashboardAdmin(admin.ModelAdmin):
    """
    Admin interface for report dashboards
    """
    list_display = ('name', 'owner', 'is_public', 'get_widgets_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description', 'owner__username', 'owner__first_name', 'owner__last_name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('shared_with',)
    inlines = [DashboardWidgetInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        (_('Access Settings'), {
            'fields': ('owner', 'is_public', 'shared_with')
        }),
        (_('Layout Settings'), {
            'fields': ('layout',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_widgets_count(self, obj):
        return obj.widgets.count()
    get_widgets_count.short_description = _('Widgets')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """
    Admin interface for dashboard widgets
    """
    list_display = ('title', 'dashboard', 'widget_type', 'position_x', 'position_y', 'width', 'height')
    list_filter = ('widget_type', 'dashboard')
    search_fields = ('title', 'dashboard__name')
    autocomplete_fields = ('dashboard', 'report')
    
    fieldsets = (
        (None, {
            'fields': ('dashboard', 'title', 'widget_type')
        }),
        (_('Data Source'), {
            'fields': ('report', 'data')
        }),
        (_('Settings'), {
            'fields': ('settings',)
        }),
        (_('Position'), {
            'fields': (('position_x', 'position_y'), ('width', 'height'))
        }),
    )


@admin.register(ReportSubscription)
class ReportSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for report subscriptions
    """
    list_display = ('user', 'report_template', 'recurrence', 'is_active', 'last_sent')
    list_filter = ('recurrence', 'is_active', 'report_template__report_type')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'report_template__name')
    readonly_fields = ('created_at', 'last_sent')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'report_template', 'is_active')
        }),
        (_('Parameters'), {
            'fields': ('parameters',)
        }),
        (_('Schedule'), {
            'fields': ('recurrence',)
        }),
        (_('Delivery Settings'), {
            'fields': ('send_email', 'send_notification')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'last_sent'),
            'classes': ('collapse',)
        }),
    )

