# Generated by Django 4.2.10 on 2025-05-05 21:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0003_teachersubject_subject_teachersubject_teacher_and_more"),
        ("university_structure", "0001_initial"),
        ("academic_performance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentrecord",
            name="student",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="record_book",
                to="accounts.studentprofile",
                verbose_name="Студент",
            ),
        ),
        migrations.AddField(
            model_name="scholarshipassignment",
            name="assigned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_scholarships",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто назначил",
            ),
        ),
        migrations.AddField(
            model_name="scholarshipassignment",
            name="scholarship",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="academic_performance.scholarship",
                verbose_name="Стипендия",
            ),
        ),
        migrations.AddField(
            model_name="scholarshipassignment",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="scholarships",
                to="university_structure.semester",
                verbose_name="Семестр",
            ),
        ),
        migrations.AddField(
            model_name="scholarshipassignment",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="scholarships",
                to="accounts.studentprofile",
                verbose_name="Студент",
            ),
        ),
        migrations.AddField(
            model_name="retakepermission",
            name="academic_debt",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="retake_permissions",
                to="academic_performance.academicdebt",
                verbose_name="Академическая задолженность",
            ),
        ),
        migrations.AddField(
            model_name="retakepermission",
            name="approved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_retake_permissions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто утвердил",
            ),
        ),
        migrations.AddField(
            model_name="retakepermission",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_retake_permissions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто создал",
            ),
        ),
    ]
