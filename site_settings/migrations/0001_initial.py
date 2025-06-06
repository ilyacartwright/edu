# Generated by Django 4.2.10 on 2025-05-06 20:48

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "site_name",
                    models.CharField(
                        default="EduPortal",
                        max_length=100,
                        verbose_name="Название сайта",
                    ),
                ),
                (
                    "site_description",
                    models.TextField(blank=True, verbose_name="Описание сайта"),
                ),
                (
                    "site_keywords",
                    models.TextField(
                        blank=True,
                        help_text="Через запятую",
                        verbose_name="Ключевые слова",
                    ),
                ),
                (
                    "site_logo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="site_settings/",
                        verbose_name="Логотип сайта",
                    ),
                ),
                (
                    "site_favicon",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="site_settings/",
                        verbose_name="Favicon",
                    ),
                ),
                (
                    "footer_text",
                    models.TextField(blank=True, verbose_name="Текст футера"),
                ),
                (
                    "contact_email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="Контактный email"
                    ),
                ),
                (
                    "contact_phone",
                    models.CharField(
                        blank=True, max_length=20, verbose_name="Контактный телефон"
                    ),
                ),
                ("social_vk", models.URLField(blank=True, verbose_name="ВКонтакте")),
                (
                    "social_telegram",
                    models.URLField(blank=True, verbose_name="Telegram"),
                ),
                (
                    "social_instagram",
                    models.URLField(blank=True, verbose_name="Instagram"),
                ),
                ("social_youtube", models.URLField(blank=True, verbose_name="YouTube")),
                (
                    "primary_color",
                    models.CharField(
                        default="#3498db",
                        help_text="HEX или RGB код цвета",
                        max_length=20,
                        verbose_name="Основной цвет",
                    ),
                ),
                (
                    "secondary_color",
                    models.CharField(
                        default="#2ecc71",
                        help_text="HEX или RGB код цвета",
                        max_length=20,
                        verbose_name="Дополнительный цвет",
                    ),
                ),
                (
                    "enable_caching",
                    models.BooleanField(
                        default=True, verbose_name="Включить кэширование"
                    ),
                ),
                (
                    "maintenance_mode",
                    models.BooleanField(
                        default=False, verbose_name="Режим обслуживания"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Дата обновления"),
                ),
            ],
            options={
                "verbose_name": "настройки сайта",
                "verbose_name_plural": "настройки сайта",
            },
        ),
        migrations.CreateModel(
            name="StudentProfileSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "show_faculty",
                    models.BooleanField(
                        default=True, verbose_name="Показывать факультет"
                    ),
                ),
                (
                    "show_specialization",
                    models.BooleanField(
                        default=True, verbose_name="Показывать направление"
                    ),
                ),
                (
                    "show_group",
                    models.BooleanField(default=True, verbose_name="Показывать группу"),
                ),
                (
                    "show_student_id",
                    models.BooleanField(
                        default=True, verbose_name="Показывать номер студенческого"
                    ),
                ),
                (
                    "show_education_form",
                    models.BooleanField(
                        default=True, verbose_name="Показывать форму обучения"
                    ),
                ),
                (
                    "show_education_basis",
                    models.BooleanField(
                        default=True, verbose_name="Показывать основу обучения"
                    ),
                ),
                (
                    "show_enrollment_year",
                    models.BooleanField(
                        default=True, verbose_name="Показывать год поступления"
                    ),
                ),
                (
                    "show_current_semester",
                    models.BooleanField(
                        default=True, verbose_name="Показывать текущий семестр"
                    ),
                ),
                (
                    "show_academic_status",
                    models.BooleanField(default=True, verbose_name="Показывать статус"),
                ),
                (
                    "show_scholarship_status",
                    models.BooleanField(
                        default=True, verbose_name="Показывать стипендию"
                    ),
                ),
                (
                    "show_dormitory",
                    models.BooleanField(
                        default=True, verbose_name="Показывать проживание в общежитии"
                    ),
                ),
                (
                    "show_personal_info",
                    models.BooleanField(
                        default=True, verbose_name="Показывать личную информацию"
                    ),
                ),
                (
                    "show_skills",
                    models.BooleanField(default=True, verbose_name="Показывать навыки"),
                ),
                (
                    "show_achievements",
                    models.BooleanField(
                        default=True, verbose_name="Показывать достижения"
                    ),
                ),
                (
                    "show_courses",
                    models.BooleanField(default=True, verbose_name="Показывать курсы"),
                ),
                (
                    "show_activity",
                    models.BooleanField(
                        default=True, verbose_name="Показывать активность"
                    ),
                ),
                (
                    "show_statistics",
                    models.BooleanField(
                        default=True, verbose_name="Показывать статистику"
                    ),
                ),
            ],
            options={
                "verbose_name": "настройки профиля студента",
                "verbose_name_plural": "настройки профиля студента",
            },
        ),
        migrations.CreateModel(
            name="ProfileFieldSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "profile_type",
                    models.CharField(
                        choices=[
                            ("all", "Все профили"),
                            ("student", "Студент"),
                            ("teacher", "Преподаватель"),
                            ("admin", "Администратор"),
                            ("methodist", "Методист"),
                            ("dean", "Декан/Заведующий кафедрой"),
                        ],
                        max_length=20,
                        verbose_name="Тип профиля",
                    ),
                ),
                (
                    "field_name",
                    models.CharField(max_length=100, verbose_name="Название поля"),
                ),
                (
                    "field_display_name",
                    models.CharField(
                        max_length=100, verbose_name="Отображаемое название"
                    ),
                ),
                (
                    "is_visible",
                    models.BooleanField(default=True, verbose_name="Отображается"),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Порядок отображения"
                    ),
                ),
            ],
            options={
                "verbose_name": "настройка поля профиля",
                "verbose_name_plural": "настройки полей профиля",
                "ordering": ["profile_type", "order"],
                "unique_together": {("profile_type", "field_name")},
            },
        ),
    ]
