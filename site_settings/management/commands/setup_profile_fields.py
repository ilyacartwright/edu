from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from site_settings.models import (
    StudentProfileDisplaySettings,
    TeacherProfileDisplaySettings,
    AdminProfileDisplaySettings,
    MethodistProfileDisplaySettings,
    DeanProfileDisplaySettings
)

class Command(BaseCommand):
    help = 'Initialize profile display settings if they do not exist'

    def handle(self, *args, **options):
        # Инициализация настроек для студента
        if not StudentProfileDisplaySettings.objects.exists():
            self.stdout.write(self.style.NOTICE('Creating student profile display settings...'))
            StudentProfileDisplaySettings.objects.create()
            self.stdout.write(self.style.SUCCESS('Student profile display settings created!'))
        else:
            self.stdout.write(self.style.NOTICE('Student profile display settings already exist.'))
        
        # Инициализация настроек для преподавателя
        if not TeacherProfileDisplaySettings.objects.exists():
            self.stdout.write(self.style.NOTICE('Creating teacher profile display settings...'))
            TeacherProfileDisplaySettings.objects.create()
            self.stdout.write(self.style.SUCCESS('Teacher profile display settings created!'))
        else:
            self.stdout.write(self.style.NOTICE('Teacher profile display settings already exist.'))
        
        # Инициализация настроек для администратора
        if not AdminProfileDisplaySettings.objects.exists():
            self.stdout.write(self.style.NOTICE('Creating admin profile display settings...'))
            AdminProfileDisplaySettings.objects.create()
            self.stdout.write(self.style.SUCCESS('Admin profile display settings created!'))
        else:
            self.stdout.write(self.style.NOTICE('Admin profile display settings already exist.'))
        
        # Инициализация настроек для методиста
        if not MethodistProfileDisplaySettings.objects.exists():
            self.stdout.write(self.style.NOTICE('Creating methodist profile display settings...'))
            MethodistProfileDisplaySettings.objects.create()
            self.stdout.write(self.style.SUCCESS('Methodist profile display settings created!'))
        else:
            self.stdout.write(self.style.NOTICE('Methodist profile display settings already exist.'))
        
        # Инициализация настроек для декана
        if not DeanProfileDisplaySettings.objects.exists():
            self.stdout.write(self.style.NOTICE('Creating dean profile display settings...'))
            DeanProfileDisplaySettings.objects.create()
            self.stdout.write(self.style.SUCCESS('Dean profile display settings created!'))
        else:
            self.stdout.write(self.style.NOTICE('Dean profile display settings already exist.'))
        
        self.stdout.write(self.style.SUCCESS('All profile display settings have been initialized!'))