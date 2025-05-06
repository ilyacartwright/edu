from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.utils import timezone

from .models import (
    # Лекции и видео
    LectureContent,
    VideoContent,
    
    # Тесты
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    QuizAnswer,
    
    # Задания
    Assignment,
    AssignmentSubmission,
    
    # Обсуждения
    Discussion,
    DiscussionTopic,
    DiscussionMessage,
    DiscussionAttachment,
    DiscussionParticipation,
    
    # Опросы
    Survey,
    SurveyQuestion,
    SurveyOption,
    SurveySubmission,
    SurveyAnswer,
    
    # Интерактивное содержимое
    InteractiveContent,
    InteractiveAttempt,
    
    # Вебинары
    Webinar,
    WebinarAttendance,
)


class LectureFormatFilter(admin.SimpleListFilter):
    """
    Фильтр по формату лекции
    """
    title = _('Формат лекции')
    parameter_name = 'format'
    
    def lookups(self, request, model_admin):
        return LectureContent.FORMAT_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(format=self.value())
        return queryset


@admin.register(LectureContent)
class LectureContentAdmin(admin.ModelAdmin):
    """
    Админка для содержимого лекций
    """
    list_display = ('element', 'format', 'word_count', 'estimated_read_time', 'show_toc')
    list_filter = (LectureFormatFilter, 'show_toc')
    search_fields = ('element__title', 'content')
    readonly_fields = ('word_count', 'estimated_read_time', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('element',)
        }),
        (_('Содержимое'), {
            'fields': ('content', 'format')
        }),
        (_('Настройки отображения'), {
            'fields': ('show_toc',)
        }),
        (_('Статистика'), {
            'fields': ('word_count', 'estimated_read_time')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class VideoSourceFilter(admin.SimpleListFilter):
    """
    Фильтр по источнику видео
    """
    title = _('Источник видео')
    parameter_name = 'source_type'
    
    def lookups(self, request, model_admin):
        return VideoContent.VIDEO_SOURCES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source_type=self.value())
        return queryset


@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    """
    Админка для видео-содержимого
    """
    list_display = ('element', 'source_type', 'get_video_link', 'duration_display', 'allow_download')
    list_filter = (VideoSourceFilter, 'allow_download', 'autoplay')
    search_fields = ('element__title', 'video_id', 'video_url')
    
    fieldsets = (
        (None, {
            'fields': ('element', 'source_type')
        }),
        (_('Источник видео'), {
            'fields': ('video_id', 'video_url', 'video_file')
        }),
        (_('Параметры видео'), {
            'fields': ('duration', 'start_time', 'end_time')
        }),
        (_('Настройки отображения'), {
            'fields': ('allow_download', 'autoplay', 'show_controls')
        }),
        (_('Расшифровка'), {
            'fields': ('transcript',)
        }),
    )
    
    def get_video_link(self, obj):
        """Формирует ссылку на видео в зависимости от типа источника"""
        if obj.source_type == 'youtube' and obj.video_id:
            return format_html('<a href="https://youtu.be/{}" target="_blank">YouTube</a>',
                             obj.video_id)
        elif obj.source_type == 'vimeo' and obj.video_id:
            return format_html('<a href="https://vimeo.com/{}" target="_blank">Vimeo</a>',
                             obj.video_id)
        elif obj.source_type == 'external' and obj.video_url:
            return format_html('<a href="{}" target="_blank">Внешняя ссылка</a>',
                             obj.video_url)
        elif obj.source_type == 'uploaded' and obj.video_file:
            return format_html('<a href="{}" target="_blank">Скачать файл</a>',
                             obj.video_file.url)
        return '-'
    get_video_link.short_description = _('Ссылка на видео')
    
    def duration_display(self, obj):
        """Форматирует длительность видео в формате ЧЧ:ММ:СС"""
        if not obj.duration:
            return '-'
        
        hours = obj.duration // 3600
        minutes = (obj.duration % 3600) // 60
        seconds = obj.duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    duration_display.short_description = _('Длительность')


class QuizQuestionInline(admin.TabularInline):
    """
    Встроенная админка для вопросов теста
    """
    model = QuizQuestion
    extra = 1
    fields = ('text', 'question_type', 'order', 'points')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """
    Админка для тестов
    """
    list_display = ('element', 'get_questions_count', 'attempts_allowed', 'time_limit',
                  'passing_score', 'get_attempts_count', 'get_average_score')
    list_filter = ('show_correct_answers', 'randomize_questions')
    search_fields = ('element__title', 'instructions')
    readonly_fields = ('created_at', 'updated_at', 'total_questions', 'total_points')
    inlines = [QuizQuestionInline]
    
    fieldsets = (
        (None, {
            'fields': ('element',)
        }),
        (_('Инструкции'), {
            'fields': ('instructions',)
        }),
        (_('Настройки прохождения'), {
            'fields': ('time_limit', 'attempts_allowed', 'passing_score')
        }),
        (_('Дополнительные настройки'), {
            'fields': ('randomize_questions', 'show_correct_answers')
        }),
        (_('Статистика'), {
            'fields': ('total_questions', 'total_points')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_questions_count(self, obj):
        """Получает количество вопросов в тесте"""
        return obj.questions.count()
    get_questions_count.short_description = _('Кол-во вопросов')
    
    def get_attempts_count(self, obj):
        """Получает количество попыток прохождения теста"""
        return obj.attempts.count()
    get_attempts_count.short_description = _('Кол-во попыток')
    
    def get_average_score(self, obj):
        """Получает среднюю оценку за тест"""
        avg_score = obj.attempts.filter(status='completed').aggregate(
            Avg('score_percentage')
        )['score_percentage__avg']
        
        if avg_score is not None:
            return f"{avg_score:.1f}%"
        return '-'
    get_average_score.short_description = _('Средний балл')


class QuizOptionInline(admin.TabularInline):
    """
    Встроенная админка для вариантов ответа
    """
    model = QuizOption
    extra = 2
    fields = ('text', 'is_correct', 'match_text', 'order')


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """
    Админка для вопросов теста
    """
    list_display = ('text_preview', 'quiz', 'question_type', 'order', 'points', 'get_options_count')
    list_filter = ('question_type', 'quiz')
    search_fields = ('text', 'quiz__element__title', 'explanation')
    inlines = [QuizOptionInline]
    
    fieldsets = (
        (None, {
            'fields': ('quiz', 'text', 'question_type')
        }),
        (_('Отображение'), {
            'fields': ('order', 'points', 'image')
        }),
        (_('Объяснение'), {
            'fields': ('explanation',)
        }),
    )
    
    def text_preview(self, obj):
        """Сокращенный текст вопроса"""
        max_length = 50
        if len(obj.text) > max_length:
            return f"{obj.text[:max_length]}..."
        return obj.text
    text_preview.short_description = _('Вопрос')
    
    def get_options_count(self, obj):
        """Получает количество вариантов ответа"""
        return obj.options.count()
    get_options_count.short_description = _('Кол-во вариантов')


class QuizAnswerInline(admin.TabularInline):
    """
    Встроенная админка для ответов на вопросы теста
    """
    model = QuizAnswer
    extra = 0
    readonly_fields = ('question', 'is_correct', 'partial_score', 'answered_at')
    fields = ('question', 'is_correct', 'partial_score', 'answered_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """
    Админка для попыток прохождения теста
    """
    list_display = ('student', 'quiz', 'status', 'score', 'score_percentage',
                  'passed', 'started_at', 'time_spent_display')
    list_filter = ('status', 'passed', 'quiz__element__course')
    search_fields = ('student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'quiz__element__title')
    readonly_fields = ('started_at', 'completed_at', 'time_spent', 'score',
                     'max_score', 'score_percentage', 'passed')
    inlines = [QuizAnswerInline]
    
    fieldsets = (
        (None, {
            'fields': ('quiz', 'student', 'status')
        }),
        (_('Результаты'), {
            'fields': ('score', 'max_score', 'score_percentage', 'passed')
        }),
        (_('Время'), {
            'fields': ('started_at', 'completed_at', 'time_spent')
        }),
    )
    
    def time_spent_display(self, obj):
        """Форматирует затраченное время"""
        if not obj.time_spent:
            return '-'
        
        hours = obj.time_spent // 3600
        minutes = (obj.time_spent % 3600) // 60
        seconds = obj.time_spent % 60
        
        if hours > 0:
            return f"{hours}ч {minutes}мин {seconds}с"
        elif minutes > 0:
            return f"{minutes}мин {seconds}с"
        else:
            return f"{seconds}с"
    time_spent_display.short_description = _('Затраченное время')
    
    def has_add_permission(self, request):
        return False
    
    def mark_as_complete(self, request, queryset):
        """Действие для завершения попыток"""
        for attempt in queryset.filter(status='in_progress'):
            attempt.complete()
        self.message_user(request, _("Выбранные попытки отмечены как завершенные"))
    mark_as_complete.short_description = _("Отметить как завершенные")
    
    actions = [mark_as_complete]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    """
    Админка для ответов на вопросы теста
    """
    list_display = ('question_preview', 'attempt', 'is_correct', 'partial_score', 'answered_at')
    list_filter = ('is_correct', 'question__question_type')
    search_fields = ('attempt__student__user__username', 'attempt__student__user__first_name',
                   'attempt__student__user__last_name', 'question__text')
    readonly_fields = ('attempt', 'question', 'answered_at')
    
    def question_preview(self, obj):
        """Сокращенный текст вопроса"""
        max_length = 50
        if len(obj.question.text) > max_length:
            return f"{obj.question.text[:max_length]}..."
        return obj.question.text
    question_preview.short_description = _('Вопрос')
    
    def has_add_permission(self, request):
        return False


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """
    Админка для заданий
    """
    list_display = ('element', 'max_score', 'passing_score', 'due_date',
                  'resubmissions_allowed', 'get_submissions_count')
    list_filter = ('resubmissions_allowed', 'late_submissions_allowed')
    search_fields = ('element__title', 'description', 'requirements')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('element',)
        }),
        (_('Содержимое задания'), {
            'fields': ('description', 'requirements', 'attachment')
        }),
        (_('Оценка'), {
            'fields': ('max_score', 'passing_score')
        }),
        (_('Сроки'), {
            'fields': ('due_date', 'late_submissions_allowed', 'late_submissions_deadline')
        }),
        (_('Файлы ответа'), {
            'fields': ('max_file_size_mb', 'allowed_file_types')
        }),
        (_('Переотправка'), {
            'fields': ('resubmissions_allowed', 'max_attempts')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_submissions_count(self, obj):
        """Получает количество решений задания"""
        return obj.submissions.count()
    get_submissions_count.short_description = _('Кол-во решений')


class SubmissionStatusFilter(admin.SimpleListFilter):
    """
    Фильтр по статусу решения
    """
    title = _('Статус решения')
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return AssignmentSubmission.STATUS_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    """
    Админка для решений заданий
    """
    list_display = ('student', 'assignment', 'status', 'submission_date',
                  'attempt_number', 'score', 'is_late', 'graded_by')
    list_filter = (SubmissionStatusFilter, 'is_late', 'assignment__element__course')
    search_fields = ('student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'assignment__element__title',
                   'text_answer', 'feedback')
    readonly_fields = ('submission_date', 'is_late', 'attempt_number', 'file_name',
                     'file_size', 'graded_at')
    
    fieldsets = (
        (None, {
            'fields': ('assignment', 'student', 'status')
        }),
        (_('Ответ'), {
            'fields': ('text_answer', 'file', 'file_name', 'file_size')
        }),
        (_('Оценка'), {
            'fields': ('score', 'feedback', 'graded_by', 'graded_at')
        }),
        (_('Информация о подаче'), {
            'fields': ('submission_date', 'attempt_number', 'is_late')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает проверяющего при изменении оценки"""
        if 'score' in form.changed_data or 'status' in form.changed_data:
            if obj.status == 'graded' and obj.score is not None:
                obj.graded_by = request.user
                obj.graded_at = timezone.now()
        
        super().save_model(request, obj, form, change)


class DiscussionTopicInline(admin.TabularInline):
    """
    Встроенная админка для тем обсуждения
    """
    model = DiscussionTopic
    extra = 0
    fields = ('title', 'author', 'created_at', 'is_pinned', 'is_closed', 'is_approved')
    readonly_fields = ('created_at',)


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    """
    Админка для обсуждений
    """
    list_display = ('element', 'is_graded', 'max_score', 'required_posts',
                  'required_replies', 'allow_anonymous', 'get_topics_count')
    list_filter = ('is_graded', 'allow_anonymous', 'require_approval')
    search_fields = ('element__title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DiscussionTopicInline]
    
    fieldsets = (
        (None, {
            'fields': ('element', 'description')
        }),
        (_('Оценивание'), {
            'fields': ('is_graded', 'max_score')
        }),
        (_('Требования к участию'), {
            'fields': ('required_posts', 'required_replies')
        }),
        (_('Дополнительные настройки'), {
            'fields': ('allow_anonymous', 'require_approval')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_topics_count(self, obj):
        """Получает количество тем в обсуждении"""
        return obj.topics.count()
    get_topics_count.short_description = _('Кол-во тем')


class DiscussionMessageInline(admin.TabularInline):
    """
    Встроенная админка для сообщений в теме
    """
    model = DiscussionMessage
    extra = 0
    fields = ('author', 'content_preview', 'is_solution', 'is_approved', 'created_at')
    readonly_fields = ('content_preview', 'created_at')
    
    def content_preview(self, obj):
        """Сокращенное содержимое сообщения"""
        max_length = 50
        if len(obj.content) > max_length:
            return f"{obj.content[:max_length]}..."
        return obj.content
    content_preview.short_description = _('Содержимое')


@admin.register(DiscussionTopic)
class DiscussionTopicAdmin(admin.ModelAdmin):
    """
    Админка для тем обсуждения
    """
    list_display = ('title', 'discussion', 'author', 'is_pinned', 'is_closed',
                  'is_anonymous', 'is_approved', 'views_count', 'get_messages_count')
    list_filter = ('is_pinned', 'is_closed', 'is_anonymous', 'is_approved')
    search_fields = ('title', 'content', 'author__username', 'discussion__element__title')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    inlines = [DiscussionMessageInline]
    
    fieldsets = (
        (None, {
            'fields': ('discussion', 'title', 'content')
        }),
        (_('Автор'), {
            'fields': ('author', 'is_anonymous')
        }),
        (_('Настройки'), {
            'fields': ('is_pinned', 'is_closed', 'is_approved', 'approved_by')
        }),
        (_('Статистика'), {
            'fields': ('views_count',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_messages_count(self, obj):
        """Получает количество сообщений в теме"""
        return obj.messages.count()
    get_messages_count.short_description = _('Кол-во сообщений')
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает модератора при одобрении"""
        if 'is_approved' in form.changed_data and obj.is_approved:
            obj.approved_by = request.user
        
        super().save_model(request, obj, form, change)


class DiscussionAttachmentInline(admin.TabularInline):
    """
    Встроенная админка для вложений к сообщениям
    """
    model = DiscussionAttachment
    extra = 1
    fields = ('file', 'filename', 'file_size')
    readonly_fields = ('file_size',)


@admin.register(DiscussionMessage)
class DiscussionMessageAdmin(admin.ModelAdmin):
    """
    Админка для сообщений в обсуждении
    """
    list_display = ('topic', 'author', 'content_preview', 'is_solution',
                  'is_anonymous', 'is_approved', 'created_at', 'get_rating')
    list_filter = ('is_solution', 'is_anonymous', 'is_approved')
    search_fields = ('content', 'author__username', 'topic__title')
    readonly_fields = ('created_at', 'updated_at', 'get_upvotes', 'get_downvotes')
    inlines = [DiscussionAttachmentInline]
    
    fieldsets = (
        (None, {
            'fields': ('topic', 'author', 'content')
        }),
        (_('Родительское сообщение'), {
            'fields': ('parent',)
        }),
        (_('Настройки'), {
            'fields': ('is_solution', 'is_anonymous', 'is_approved', 'approved_by')
        }),
        (_('Рейтинг'), {
            'fields': ('get_upvotes', 'get_downvotes')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Сокращенное содержимое сообщения"""
        max_length = 50
        if len(obj.content) > max_length:
            return f"{obj.content[:max_length]}..."
        return obj.content
    content_preview.short_description = _('Содержимое')
    
    def get_rating(self, obj):
        """Получает рейтинг сообщения"""
        return obj.rating
    get_rating.short_description = _('Рейтинг')
    
    def get_upvotes(self, obj):
        """Получает количество положительных голосов"""
        return obj.upvotes.count()
    get_upvotes.short_description = _('Положительные голоса')
    
    def get_downvotes(self, obj):
        """Получает количество отрицательных голосов"""
        return obj.downvotes.count()
    get_downvotes.short_description = _('Отрицательные голоса')
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает модератора при одобрении"""
        if 'is_approved' in form.changed_data and obj.is_approved:
            obj.approved_by = request.user
        
        super().save_model(request, obj, form, change)


@admin.register(DiscussionParticipation)
class DiscussionParticipationAdmin(admin.ModelAdmin):
    """
    Админка для участия в обсуждении
    """
    list_display = ('student', 'discussion', 'topics_created', 'messages_posted',
                  'replies_posted', 'grade', 'graded_by')
    list_filter = ('discussion__is_graded',)
    search_fields = ('student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'discussion__element__title')
    readonly_fields = ('topics_created', 'messages_posted', 'replies_posted', 'graded_at')
    
    fieldsets = (
        (None, {
            'fields': ('discussion', 'student')
        }),
        (_('Статистика'), {
            'fields': ('topics_created', 'messages_posted', 'replies_posted')
        }),
        (_('Оценка'), {
            'fields': ('grade', 'feedback', 'graded_by', 'graded_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает оценивающего при установке оценки"""
        if 'grade' in form.changed_data and obj.grade is not None:
            obj.graded_by = request.user
            obj.graded_at = timezone.now()
            
            # Обновляем прогресс после оценивания
            obj.update_progress()
        
        super().save_model(request, obj, form, change)
    
    def update_statistics(self, request, queryset):
        """Действие для обновления статистики участия"""
        for participation in queryset:
            participation.update_statistics()
        self.message_user(request, _("Статистика участия обновлена"))
    update_statistics.short_description = _("Обновить статистику участия")
    
    actions = [update_statistics]


class SurveyQuestionInline(admin.TabularInline):
    """
    Встроенная админка для вопросов опроса
    """
    model = SurveyQuestion
    extra = 1
    fields = ('text', 'question_type', 'is_required', 'order')


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    """
    Админка для опросов
    """
    list_display = ('element', 'is_anonymous', 'show_results',
                  'allow_multiple_submissions', 'get_questions_count', 'get_submissions_count')
    list_filter = ('is_anonymous', 'show_results', 'allow_multiple_submissions')
    search_fields = ('element__title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SurveyQuestionInline]
    
    fieldsets = (
        (None, {
            'fields': ('element', 'description')
        }),
        (_('Настройки опроса'), {
            'fields': ('is_anonymous', 'show_results', 'allow_multiple_submissions')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_questions_count(self, obj):
        """Получает количество вопросов в опросе"""
        return obj.questions.count()
    get_questions_count.short_description = _('Кол-во вопросов')
    
    def get_submissions_count(self, obj):
        """Получает количество ответов на опрос"""
        return obj.submissions.count()
    get_submissions_count.short_description = _('Кол-во ответов')


class SurveyOptionInline(admin.TabularInline):
    """
    Встроенная админка для вариантов ответа на вопрос опроса
    """
    model = SurveyOption
    extra = 2
    fields = ('text', 'order')


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    """
    Админка для вопросов опроса
    """
    list_display = ('text_preview', 'survey', 'question_type', 'is_required', 'order')
    list_filter = ('question_type', 'is_required')
    search_fields = ('text', 'survey__element__title')
    inlines = [SurveyOptionInline]
    
    fieldsets = (
        (None, {
            'fields': ('survey', 'text', 'question_type')
        }),
        (_('Настройки'), {
            'fields': ('is_required', 'order')
        }),
        (_('Параметры шкалы'), {
            'fields': ('scale_min', 'scale_max', 'scale_min_label', 'scale_max_label'),
            'classes': ('collapse',),
            'description': _('Используется только для вопросов типа рейтинговая шкала и шкала Ликерта'),
        }),
    )
    
    def text_preview(self, obj):
        """Сокращенный текст вопроса"""
        max_length = 50
        if len(obj.text) > max_length:
            return f"{obj.text[:max_length]}..."
        return obj.text
    text_preview.short_description = _('Вопрос')


class SurveyAnswerInline(admin.TabularInline):
    """
    Встроенная админка для ответов на вопросы опроса
    """
    model = SurveyAnswer
    extra = 0
    fields = ('question', 'text_answer', 'numeric_answer', 'get_selected_options')
    readonly_fields = ('question', 'get_selected_options')
    
    def get_selected_options(self, obj):
        """Получает выбранные варианты"""
        options = obj.selected_options.all()
        if options:
            return ", ".join([option.text for option in options])
        return '-'
    get_selected_options.short_description = _('Выбранные варианты')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SurveySubmission)
class SurveySubmissionAdmin(admin.ModelAdmin):
    """
    Админка для заполненных опросов
    """
    list_display = ('get_respondent', 'survey', 'submission_date', 'attempt_number')
    list_filter = ('survey__is_anonymous', 'submission_date')
    search_fields = ('student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'survey__element__title')
    readonly_fields = ('submission_date', 'attempt_number')
    inlines = [SurveyAnswerInline]
    
    fieldsets = (
        (None, {
            'fields': ('survey', 'student')
        }),
        (_('Информация о подаче'), {
            'fields': ('submission_date', 'attempt_number')
        }),
    )
    
    def get_respondent(self, obj):
        """Получает информацию о респонденте (с учетом анонимности)"""
        if obj.student:
            return obj.student
        return _('Анонимный респондент')
    get_respondent.short_description = _('Респондент')


@admin.register(InteractiveContent)
class InteractiveContentAdmin(admin.ModelAdmin):
    """
    Админка для интерактивного содержимого
    """
    list_display = ('element', 'content_type', 'is_gradable', 'max_score', 'passing_score')
    list_filter = ('content_type', 'is_gradable', 'allow_fullscreen')
    search_fields = ('element__title', 'content_url', 'content_embed_code')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('element', 'content_type')
        }),
        (_('Содержимое'), {
            'fields': ('content_url', 'content_embed_code', 'content_html', 'content_js', 'h5p_content_id')
        }),
        (_('Настройки отображения'), {
            'fields': ('width', 'height', 'allow_fullscreen')
        }),
        (_('Оценивание'), {
            'fields': ('is_gradable', 'max_score', 'passing_score')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InteractiveAttempt)
class InteractiveAttemptAdmin(admin.ModelAdmin):
    """
    Админка для попыток прохождения интерактивного содержимого
    """
    list_display = ('student', 'interactive_content', 'score_percentage', 'passed',
                  'started_at', 'time_spent_display')
    list_filter = ('passed', 'interactive_content__element__course')
    search_fields = ('student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'interactive_content__element__title')
    readonly_fields = ('started_at', 'completed_at', 'time_spent', 'score',
                     'max_score', 'score_percentage', 'passed', 'raw_result')
    
    fieldsets = (
        (None, {
            'fields': ('interactive_content', 'student')
        }),
        (_('Результаты'), {
            'fields': ('score', 'max_score', 'score_percentage', 'passed')
        }),
        (_('Время'), {
            'fields': ('started_at', 'completed_at', 'time_spent')
        }),
        (_('Данные'), {
            'fields': ('raw_result',),
            'classes': ('collapse',)
        }),
    )
    
    def time_spent_display(self, obj):
        """Форматирует затраченное время"""
        if not obj.time_spent:
            return '-'
        
        hours = obj.time_spent // 3600
        minutes = (obj.time_spent % 3600) // 60
        seconds = obj.time_spent % 60
        
        if hours > 0:
            return f"{hours}ч {minutes}мин {seconds}с"
        elif minutes > 0:
            return f"{minutes}мин {seconds}с"
        else:
            return f"{seconds}с"
    time_spent_display.short_description = _('Затраченное время')
    
    def has_add_permission(self, request):
        return False


class WebinarCoHostsInline(admin.TabularInline):
    """
    Встроенная админка для со-ведущих вебинара
    """
    model = Webinar.co_hosts.through
    extra = 1
    verbose_name = _('Со-ведущий')
    verbose_name_plural = _('Со-ведущие')


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    """
    Админка для вебинаров
    """
    list_display = ('element', 'webinar_type', 'platform', 'host',
                  'start_datetime', 'duration_minutes', 'is_past', 'is_live')
    list_filter = ('webinar_type', 'platform', 'track_attendance')
    search_fields = ('element__title', 'description', 'host__user__username',
                   'host__user__first_name', 'host__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('co_hosts',)
    
    fieldsets = (
        (None, {
            'fields': ('element', 'webinar_type', 'description')
        }),
        (_('Время проведения'), {
            'fields': ('start_datetime', 'end_datetime', 'duration_minutes', 'timezone_info')
        }),
        (_('Платформа'), {
            'fields': ('platform', 'platform_name', 'meeting_url', 'meeting_id', 'password')
        }),
        (_('Материалы'), {
            'fields': ('recording_url', 'presentation_file', 'prerequisites')
        }),
        (_('Ведущие'), {
            'fields': ('host', 'co_hosts')
        }),
        (_('Отслеживание присутствия'), {
            'fields': ('track_attendance', 'minimum_attendance_minutes')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WebinarAttendance)
class WebinarAttendanceAdmin(admin.ModelAdmin):
    """
    Админка для посещений вебинара
    """
    list_display = ('student', 'webinar', 'status', 'attendance_minutes',
                  'joined_at', 'has_participated')
    list_filter = ('status', 'has_participated', 'webinar__element__course')
    search_fields = ('student__user__username', 'student__user__first_name',
                   'student__user__last_name', 'webinar__element__title',
                   'teacher_notes')
    readonly_fields = ('joined_at', 'left_at')
    
    fieldsets = (
        (None, {
            'fields': ('webinar', 'student', 'status')
        }),
        (_('Информация о посещении'), {
            'fields': ('joined_at', 'left_at', 'attendance_minutes', 'has_participated')
        }),
        (_('Техническая информация'), {
            'fields': ('ip_address', 'user_agent')
        }),
        (_('Заметки'), {
            'fields': ('teacher_notes',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Обновляет прогресс при сохранении"""
        super().save_model(request, obj, form, change)
        
        if 'status' in form.changed_data:
            # Обновляем прогресс если статус изменен
            obj.update_progress()
    
    def mark_as_attended(self, request, queryset):
        """Действие для отметки посещения"""
        queryset.update(status='attended')
        for attendance in queryset:
            attendance.update_progress()
        self.message_user(request, _("Выбранные записи отмечены как посещенные"))
    mark_as_attended.short_description = _("Отметить как посещенные")
    
    def mark_as_watched_recording(self, request, queryset):
        """Действие для отметки просмотра записи"""
        queryset.update(status='watched_recording')
        for attendance in queryset:
            attendance.update_progress()
        self.message_user(request, _("Выбранные записи отмечены как просмотревшие запись"))
    mark_as_watched_recording.short_description = _("Отметить как просмотревшие запись")
    
    actions = [mark_as_attended, mark_as_watched_recording]


# Настройка административного сайта
admin.site.site_header = _('Управление контентом курсов')
admin.site.site_title = _('Администрирование курсов')
admin.site.index_title = _('Панель управления контентом')