# Generated by Django 4.2.10 on 2025-05-06 21:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("site_settings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminProfileSettings",
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
                    "show_position",
                    models.BooleanField(
                        default=True, verbose_name="Показывать должность"
                    ),
                ),
                (
                    "show_department",
                    models.BooleanField(
                        default=True, verbose_name="Показывать подразделение"
                    ),
                ),
                (
                    "show_access_level",
                    models.BooleanField(
                        default=True, verbose_name="Показывать уровень доступа"
                    ),
                ),
                (
                    "show_responsibility_area",
                    models.BooleanField(
                        default=True, verbose_name="Показывать область ответственности"
                    ),
                ),
            ],
            options={
                "verbose_name": "настройки профиля администратора",
                "verbose_name_plural": "настройки профиля администратора",
            },
        ),
        migrations.CreateModel(
            name="DeanProfileSettings",
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
                    "show_position",
                    models.BooleanField(
                        default=True, verbose_name="Показывать должность"
                    ),
                ),
                (
                    "show_faculty",
                    models.BooleanField(
                        default=True, verbose_name="Показывать факультет"
                    ),
                ),
                (
                    "show_department",
                    models.BooleanField(
                        default=True, verbose_name="Показывать кафедру"
                    ),
                ),
                (
                    "show_academic_degree",
                    models.BooleanField(
                        default=True, verbose_name="Показывать учёную степень"
                    ),
                ),
                (
                    "show_academic_title",
                    models.BooleanField(
                        default=True, verbose_name="Показывать учёное звание"
                    ),
                ),
                (
                    "show_appointment_date",
                    models.BooleanField(
                        default=True, verbose_name="Показывать дату назначения"
                    ),
                ),
                (
                    "show_term_end_date",
                    models.BooleanField(
                        default=True,
                        verbose_name="Показывать срок окончания полномочий",
                    ),
                ),
                (
                    "show_has_teaching_duties",
                    models.BooleanField(
                        default=True,
                        verbose_name="Показывать преподавательскую деятельность",
                    ),
                ),
            ],
            options={
                "verbose_name": "настройки профиля декана/заведующего",
                "verbose_name_plural": "настройки профиля декана/заведующего",
            },
        ),
        migrations.CreateModel(
            name="MethodistProfileSettings",
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
                    "show_department",
                    models.BooleanField(
                        default=True, verbose_name="Показывать кафедру"
                    ),
                ),
                (
                    "show_employee_id",
                    models.BooleanField(
                        default=True, verbose_name="Показывать табельный номер"
                    ),
                ),
                (
                    "show_responsibilities",
                    models.BooleanField(
                        default=True, verbose_name="Показывать обязанности"
                    ),
                ),
                (
                    "show_managed_specializations",
                    models.BooleanField(
                        default=True, verbose_name="Показывать курируемые специализации"
                    ),
                ),
                (
                    "show_managed_groups",
                    models.BooleanField(
                        default=True, verbose_name="Показывать курируемые группы"
                    ),
                ),
            ],
            options={
                "verbose_name": "настройки профиля методиста",
                "verbose_name_plural": "настройки профиля методиста",
            },
        ),
        migrations.CreateModel(
            name="TeacherProfileSettings",
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
                    "show_department",
                    models.BooleanField(
                        default=True, verbose_name="Показывать кафедру"
                    ),
                ),
                (
                    "show_position",
                    models.BooleanField(
                        default=True, verbose_name="Показывать должность"
                    ),
                ),
                (
                    "show_academic_degree",
                    models.BooleanField(
                        default=True, verbose_name="Показывать учёную степень"
                    ),
                ),
                (
                    "show_academic_title",
                    models.BooleanField(
                        default=True, verbose_name="Показывать учёное звание"
                    ),
                ),
                (
                    "show_employment_type",
                    models.BooleanField(
                        default=True, verbose_name="Показывать тип занятости"
                    ),
                ),
                (
                    "show_specialization",
                    models.BooleanField(
                        default=True, verbose_name="Показывать специализацию"
                    ),
                ),
                (
                    "show_hire_date",
                    models.BooleanField(
                        default=True, verbose_name="Показывать дату приёма на работу"
                    ),
                ),
                (
                    "show_office_location",
                    models.BooleanField(
                        default=True, verbose_name="Показывать местоположение кабинета"
                    ),
                ),
                (
                    "show_office_hours",
                    models.BooleanField(
                        default=True, verbose_name="Показывать часы консультаций"
                    ),
                ),
                (
                    "show_bio",
                    models.BooleanField(
                        default=True, verbose_name="Показывать биографию"
                    ),
                ),
                (
                    "show_courses",
                    models.BooleanField(default=True, verbose_name="Показывать курсы"),
                ),
                (
                    "show_publications",
                    models.BooleanField(
                        default=True, verbose_name="Показывать публикации"
                    ),
                ),
            ],
            options={
                "verbose_name": "настройки профиля преподавателя",
                "verbose_name_plural": "настройки профиля преподавателя",
            },
        ),
    ]
