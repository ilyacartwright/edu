from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.contrib.admin import SimpleListFilter

from .models import (
    MaterialCategory,
    Material,
    MaterialTag,
    MaterialAttachment,
    MaterialDownload,
    MaterialView,
    MaterialFavorite,
    MaterialComment,
    MaterialRating,
    Literature,
    ElectronicLibrarySystem,
)


class MaterialCategoryInline(admin.TabularInline):
    """
    Встроенная админка для подкатегорий
    """
    model = MaterialCategory
    extra = 1
    fields = ('name', 'description')
    fk_name = 'parent'


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    """
    Админка для категорий учебных материалов
    """
    list_display = ('name', 'parent', 'get_subcategories_count', 'get_materials_count')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    inlines = [MaterialCategoryInline]
    
    def get_subcategories_count(self, obj):
        """Получает количество подкатегорий"""
        return obj.subcategories.count()
    get_subcategories_count.short_description = _('Кол-во подкатегорий')
    
    def get_materials_count(self, obj):
        """Получает количество материалов в категории"""
        return obj.materials.count()
    get_materials_count.short_description = _('Кол-во материалов')
    
    def get_queryset(self, request):
        """Отображает только родительские категории по умолчанию"""
        qs = super().get_queryset(request)
        if not request.GET.get('parent__id__exact'):
            return qs.filter(parent__isnull=True)
        return qs


class MaterialTypeFilter(SimpleListFilter):
    """
    Фильтр по типу материала
    """
    title = _('Тип материала')
    parameter_name = 'material_type'
    
    def lookups(self, request, model_admin):
        return Material.MATERIAL_TYPES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(material_type=self.value())
        return queryset


class AccessLevelFilter(SimpleListFilter):
    """
    Фильтр по уровню доступа
    """
    title = _('Уровень доступа')
    parameter_name = 'access_level'
    
    def lookups(self, request, model_admin):
        return Material.ACCESS_LEVELS
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(access_level=self.value())
        return queryset


class MaterialAttachmentInline(admin.TabularInline):
    """
    Встроенная админка для вложений к материалу
    """
    model = MaterialAttachment
    extra = 1
    fields = ('title', 'description', 'file', 'file_size', 'file_type')
    readonly_fields = ('file_size', 'file_type')


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """
    Админка для учебных материалов
    """
    list_display = ('title', 'subject', 'get_material_type_display', 'author', 
                  'access_level', 'is_published', 'get_file_link', 'created_at')
    list_filter = (MaterialTypeFilter, AccessLevelFilter, 'is_published', 
                 'is_featured', 'subject', 'created_at')
    search_fields = ('title', 'description', 'content', 'author__username', 
                   'author__first_name', 'author__last_name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'file_size', 'file_type')
    filter_horizontal = ('tags', 'groups', 'courses')
    inlines = [MaterialAttachmentInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description')
        }),
        (_('Содержимое'), {
            'fields': ('content', 'file', 'file_size', 'file_type', 'external_url')
        }),
        (_('Привязка'), {
            'fields': ('subject', 'academic_plan_subject', 'category', 'material_type', 'tags')
        }),
        (_('Доступ'), {
            'fields': ('access_level', 'groups', 'courses')
        }),
        (_('Публикация'), {
            'fields': ('is_published', 'is_featured', 'author')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_material_type_display(self, obj):
        """Отображает тип материала"""
        return obj.get_material_type_display()
    get_material_type_display.short_description = _('Тип материала')
    
    def get_file_link(self, obj):
        """Формирует ссылку на файл если он есть"""
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>',
                             obj.file.url, self.get_file_size_display(obj))
        return '-'
    get_file_link.short_description = _('Файл')
    
    def get_file_size_display(self, obj):
        """Форматирует размер файла"""
        if not obj.file_size:
            return _('Файл')
        
        # Преобразуем байты в удобный формат
        size = obj.file_size
        if size < 1024:
            return f"{size} байт"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} КБ"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} МБ"
        else:
            return f"{size/(1024*1024*1024):.1f} ГБ"
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает автора при создании"""
        if not change and not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaterialTag)
class MaterialTagAdmin(admin.ModelAdmin):
    """
    Админка для тегов материалов
    """
    list_display = ('name', 'slug', 'get_materials_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def get_materials_count(self, obj):
        """Получает количество материалов с данным тегом"""
        return obj.materials.count()
    get_materials_count.short_description = _('Кол-во материалов')


@admin.register(MaterialAttachment)
class MaterialAttachmentAdmin(admin.ModelAdmin):
    """
    Админка для вложений к материалам
    """
    list_display = ('title', 'material', 'get_file_size_display', 'created_at')
    list_filter = ('created_at', 'file_type')
    search_fields = ('title', 'description', 'material__title')
    readonly_fields = ('file_size', 'file_type', 'created_at')
    
    def get_file_size_display(self, obj):
        """Форматирует размер файла"""
        if not obj.file_size:
            return '-'
        
        # Преобразуем байты в удобный формат
        size = obj.file_size
        if size < 1024:
            return f"{size} байт"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} КБ"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} МБ"
        else:
            return f"{size/(1024*1024*1024):.1f} ГБ"
    get_file_size_display.short_description = _('Размер файла')


@admin.register(MaterialDownload)
class MaterialDownloadAdmin(admin.ModelAdmin):
    """
    Админка для отслеживания скачиваний материалов
    """
    list_display = ('material', 'user', 'downloaded_at', 'ip_address')
    list_filter = ('downloaded_at',)
    search_fields = ('material__title', 'user__username', 'ip_address')
    readonly_fields = ('material', 'user', 'downloaded_at', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MaterialView)
class MaterialViewAdmin(admin.ModelAdmin):
    """
    Админка для отслеживания просмотров материалов
    """
    list_display = ('material', 'user', 'viewed_at', 'ip_address')
    list_filter = ('viewed_at',)
    search_fields = ('material__title', 'user__username', 'ip_address')
    readonly_fields = ('material', 'user', 'viewed_at', 'ip_address')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MaterialFavorite)
class MaterialFavoriteAdmin(admin.ModelAdmin):
    """
    Админка для избранных материалов
    """
    list_display = ('material', 'user', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('material__title', 'user__username')
    readonly_fields = ('added_at',)


class MaterialCommentInline(admin.TabularInline):
    """
    Встроенная админка для дочерних комментариев
    """
    model = MaterialComment
    extra = 0
    fields = ('author', 'text', 'created_at', 'is_approved')
    readonly_fields = ('created_at',)
    fk_name = 'parent'


@admin.register(MaterialComment)
class MaterialCommentAdmin(admin.ModelAdmin):
    """
    Админка для комментариев к материалам
    """
    list_display = ('get_comment_preview', 'material', 'author', 'created_at', 
                  'is_approved', 'parent')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('text', 'author__username', 'material__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MaterialCommentInline]
    
    fieldsets = (
        (None, {
            'fields': ('material', 'author', 'text')
        }),
        (_('Модерация'), {
            'fields': ('is_approved',)
        }),
        (_('Родительский комментарий'), {
            'fields': ('parent',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_comment_preview(self, obj):
        """Сокращенный текст комментария"""
        max_length = 50
        if len(obj.text) > max_length:
            return f"{obj.text[:max_length]}..."
        return obj.text
    get_comment_preview.short_description = _('Комментарий')
    
    def approve_comments(self, request, queryset):
        """Действие для одобрения комментариев"""
        queryset.update(is_approved=True)
        self.message_user(request, _("Выбранные комментарии одобрены"))
    approve_comments.short_description = _("Одобрить комментарии")
    
    def disapprove_comments(self, request, queryset):
        """Действие для отклонения комментариев"""
        queryset.update(is_approved=False)
        self.message_user(request, _("Выбранные комментарии отклонены"))
    disapprove_comments.short_description = _("Отклонить комментарии")
    
    actions = [approve_comments, disapprove_comments]


@admin.register(MaterialRating)
class MaterialRatingAdmin(admin.ModelAdmin):
    """
    Админка для оценок материалов
    """
    list_display = ('material', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('material__title', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')


class LiteratureTypeFilter(SimpleListFilter):
    """
    Фильтр по типу литературы
    """
    title = _('Тип литературы')
    parameter_name = 'literature_type'
    
    def lookups(self, request, model_admin):
        return Literature.LITERATURE_TYPES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(literature_type=self.value())
        return queryset


class AvailabilityFilter(SimpleListFilter):
    """
    Фильтр по доступности литературы
    """
    title = _('Доступность')
    parameter_name = 'availability'
    
    def lookups(self, request, model_admin):
        return Literature.AVAILABILITY_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(availability=self.value())
        return queryset


@admin.register(Literature)
class LiteratureAdmin(admin.ModelAdmin):
    """
    Админка для литературы
    """
    list_display = ('title', 'authors', 'publication_year', 'literature_type',
                  'availability', 'copies_available', 'get_file_link', 'get_subjects')
    list_filter = (LiteratureTypeFilter, AvailabilityFilter, 'publication_year')
    search_fields = ('title', 'authors', 'publisher', 'isbn', 'description')
    readonly_fields = ('file_size', 'created_at', 'updated_at')
    filter_horizontal = ('subjects',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'authors', 'literature_type')
        }),
        (_('Информация о публикации'), {
            'fields': ('publication_year', 'publisher', 'isbn', 'description')
        }),
        (_('Привязка к учебному процессу'), {
            'fields': ('subjects',)
        }),
        (_('Доступность'), {
            'fields': ('availability', 'copies_available', 'location')
        }),
        (_('Файл/ссылка'), {
            'fields': ('file', 'file_size', 'external_url')
        }),
        (_('Метаданные'), {
            'fields': ('added_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_subjects(self, obj):
        """Получает список дисциплин"""
        subjects = obj.subjects.all()
        if subjects:
            return ", ".join([subject.name for subject in subjects[:5]])
        return '-'
    get_subjects.short_description = _('Дисциплины')
    
    def get_file_link(self, obj):
        """Формирует ссылку на файл если он есть"""
        if obj.file:
            size_display = '-'
            if obj.file_size:
                # Преобразуем байты в удобный формат
                size = obj.file_size
                if size < 1024:
                    size_display = f"{size} байт"
                elif size < 1024 * 1024:
                    size_display = f"{size/1024:.1f} КБ"
                elif size < 1024 * 1024 * 1024:
                    size_display = f"{size/(1024*1024):.1f} МБ"
                else:
                    size_display = f"{size/(1024*1024*1024):.1f} ГБ"
            
            return format_html('<a href="{}" target="_blank">{}</a>',
                             obj.file.url, size_display)
        elif obj.external_url:
            return format_html('<a href="{}" target="_blank">{}</a>',
                             obj.external_url, _('Внешняя ссылка'))
        return '-'
    get_file_link.short_description = _('Файл/ссылка')
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает добавившего пользователя при создании"""
        if not change and not obj.added_by:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ElectronicLibrarySystem)
class ElectronicLibrarySystemAdmin(admin.ModelAdmin):
    """
    Админка для электронных библиотечных систем
    """
    list_display = ('name', 'url', 'is_active', 'subscription_start', 
                  'subscription_end', 'is_subscription_valid')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'access_instructions')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'description', 'logo')
        }),
        (_('Подписка'), {
            'fields': ('is_active', 'subscription_start', 'subscription_end')
        }),
        (_('Инструкции'), {
            'fields': ('access_instructions',)
        }),
    )

