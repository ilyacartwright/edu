# Generated by Django 4.2.10 on 2025-05-05 21:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_adminprofile_deanprofile_methodistprofile_and_more"),
        ("university_structure", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="teachersubject",
            name="subject",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="teachers",
                to="university_structure.subject",
            ),
        ),
        migrations.AddField(
            model_name="teachersubject",
            name="teacher",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="teaching_subjects",
                to="accounts.teacherprofile",
            ),
        ),
        migrations.AddField(
            model_name="teacherprofile",
            name="department",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="teachers",
                to="university_structure.department",
            ),
        ),
        migrations.AddField(
            model_name="teacherprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="teacher_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="students",
                to="university_structure.group",
            ),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="student_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="methodistprofile",
            name="department",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="methodists",
                to="university_structure.department",
            ),
        ),
        migrations.AddField(
            model_name="methodistprofile",
            name="managed_groups",
            field=models.ManyToManyField(
                blank=True, related_name="methodists", to="university_structure.group"
            ),
        ),
        migrations.AddField(
            model_name="methodistprofile",
            name="managed_specializations",
            field=models.ManyToManyField(
                blank=True,
                related_name="methodists",
                to="university_structure.specialization",
            ),
        ),
        migrations.AddField(
            model_name="methodistprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="methodist_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="deanprofile",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="heads",
                to="university_structure.department",
            ),
        ),
        migrations.AddField(
            model_name="deanprofile",
            name="faculty",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deans",
                to="university_structure.faculty",
            ),
        ),
        migrations.AddField(
            model_name="deanprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dean_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="adminprofile",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="admins",
                to="university_structure.department",
            ),
        ),
        migrations.AddField(
            model_name="adminprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="admin_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="teachersubject",
            unique_together={
                ("teacher", "subject", "academic_year", "semester", "role")
            },
        ),
        migrations.AddConstraint(
            model_name="deanprofile",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("faculty__isnull", False), ("position", "dean")),
                    models.Q(("faculty__isnull", False), ("position", "vice_dean")),
                    models.Q(
                        ("department__isnull", False),
                        ("position", "head_of_department"),
                    ),
                    _connector="OR",
                ),
                name="position_matches_entity",
            ),
        ),
    ]
