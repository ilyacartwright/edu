from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import os
import json


def get_quiz_image_path(instance, filename):
    """
    Функция для определения пути сохранения изображений к вопросам теста
    """
    quiz_id = instance.quiz.id
    question_id = instance.id
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('quiz_images', str(quiz_id), str(question_id), filename)


def get_assignment_file_path(instance, filename):
    """
    Функция для определения пути сохранения файлов заданий
    """
    assignment_id = instance.assignment.id
    return os.path.join('assignment_files', str(assignment_id), filename)


def get_solution_file_path(instance, filename):
    """
    Функция для определения пути сохранения файлов решений заданий
    """
    submission_id = instance.id
    assignment_id = instance.assignment.id
    student_id = instance.student.id
    ext = filename.split('.')[-1]
    filename = f"solution_{submission_id}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('solution_files', str(assignment_id), str(student_id), filename)


class LectureContent(models.Model):
    """
    Модель содержимого лекции
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='lecture_content', verbose_name=_('Элемент курса'))
    content = models.TextField(_('Содержимое'), blank=True)
    
    # Форматирование
    FORMAT_CHOICES = (
        ('markdown', _('Markdown')),
        ('html', _('HTML')),
        ('plain', _('Простой текст')),
    )
    format = models.CharField(_('Формат'), max_length=10, choices=FORMAT_CHOICES, default='markdown')
    
    # Настройки отображения
    show_toc = models.BooleanField(_('Показывать оглавление'), default=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Статистика
    word_count = models.PositiveIntegerField(_('Количество слов'), default=0)
    estimated_read_time = models.PositiveSmallIntegerField(_('Оценочное время чтения (мин)'), default=0)
    
    class Meta:
        verbose_name = _('содержимое лекции')
        verbose_name_plural = _('содержимое лекций')
    
    def __str__(self):
        return f"Лекция: {self.element.title}"
    
    def save(self, *args, **kwargs):
        # Подсчет слов и времени чтения
        if self.content:
            self.word_count = len(self.content.split())
            self.estimated_read_time = max(1, int(self.word_count / 200))  # ~200 слов в минуту
        
        super().save(*args, **kwargs)
        
        # Обновляем оценочное время прохождения элемента
        if self.element.estimated_time != self.estimated_read_time:
            self.element.estimated_time = self.estimated_read_time
            self.element.save(update_fields=['estimated_time'])


class VideoContent(models.Model):
    """
    Модель видео-содержимого
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='video_content', verbose_name=_('Элемент курса'))
    
    # Источник видео
    VIDEO_SOURCES = (
        ('youtube', _('YouTube')),
        ('vimeo', _('Vimeo')),
        ('uploaded', _('Загруженное видео')),
        ('external', _('Внешняя ссылка')),
    )
    source_type = models.CharField(_('Тип источника'), max_length=20, choices=VIDEO_SOURCES)
    
    # Идентификатор или URL
    video_id = models.CharField(_('ID видео'), max_length=255, blank=True)
    video_url = models.URLField(_('URL видео'), blank=True)
    
    # Загруженное видео
    video_file = models.FileField(_('Видео файл'), upload_to='course_videos/', null=True, blank=True)
    
    # Параметры видео
    duration = models.PositiveIntegerField(_('Длительность (сек)'), default=0)
    start_time = models.PositiveSmallIntegerField(_('Время начала (сек)'), default=0)
    end_time = models.PositiveIntegerField(_('Время окончания (сек)'), null=True, blank=True)
    
    # Настройки отображения
    allow_download = models.BooleanField(_('Разрешить скачивание'), default=False)
    autoplay = models.BooleanField(_('Автовоспроизведение'), default=False)
    show_controls = models.BooleanField(_('Показывать элементы управления'), default=True)
    
    # Дополнительные материалы
    transcript = models.TextField(_('Расшифровка/субтитры'), blank=True)
    
    class Meta:
        verbose_name = _('видео-содержимое')
        verbose_name_plural = _('видео-содержимое')
    
    def __str__(self):
        return f"Видео: {self.element.title}"
    
    def save(self, *args, **kwargs):
        # Обновляем оценочное время прохождения элемента
        estimated_minutes = max(1, int(self.duration / 60))
        if self.element.estimated_time != estimated_minutes:
            self.element.estimated_time = estimated_minutes
            self.element.save(update_fields=['estimated_time'])
        
        super().save(*args, **kwargs)


class Quiz(models.Model):
    """
    Модель теста
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='quiz', verbose_name=_('Элемент курса'))
    
    # Настройки прохождения
    time_limit = models.PositiveIntegerField(_('Ограничение времени (мин)'), null=True, blank=True)
    attempts_allowed = models.PositiveSmallIntegerField(_('Разрешено попыток'), default=1)
    passing_score = models.PositiveSmallIntegerField(_('Проходной балл (%)'), default=70,
                                                  validators=[MinValueValidator(0), MaxValueValidator(100)])
    randomize_questions = models.BooleanField(_('Случайный порядок вопросов'), default=False)
    show_correct_answers = models.BooleanField(_('Показывать правильные ответы'), default=True)
    
    # Инструкции
    instructions = models.TextField(_('Инструкции'), blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('тест')
        verbose_name_plural = _('тесты')
    
    def __str__(self):
        return f"Тест: {self.element.title}"
    
    @property
    def total_questions(self):
        """Возвращает общее количество вопросов в тесте"""
        return self.questions.count()
    
    @property
    def total_points(self):
        """Возвращает общее количество баллов в тесте"""
        return self.questions.aggregate(models.Sum('points'))['points__sum'] or 0


class QuizQuestion(models.Model):
    """
    Модель вопроса теста
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,
                            related_name='questions', verbose_name=_('Тест'))
    
    # Содержимое вопроса
    text = models.TextField(_('Текст вопроса'))
    image = models.ImageField(_('Изображение'), upload_to=get_quiz_image_path, null=True, blank=True)
    
    # Тип вопроса
    QUESTION_TYPES = (
        ('single', _('Одиночный выбор')),
        ('multiple', _('Множественный выбор')),
        ('true_false', _('Верно/Неверно')),
        ('text', _('Текстовый ответ')),
        ('numeric', _('Числовой ответ')),
        ('matching', _('Сопоставление')),
        ('ordering', _('Упорядочивание')),
    )
    question_type = models.CharField(_('Тип вопроса'), max_length=20, choices=QUESTION_TYPES)
    
    # Порядок отображения
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    # Оценка
    points = models.PositiveSmallIntegerField(_('Баллы'), default=1)
    
    # Дополнительные настройки
    explanation = models.TextField(_('Объяснение'), blank=True,
                                 help_text=_('Объяснение правильного ответа'))
    
    class Meta:
        verbose_name = _('вопрос теста')
        verbose_name_plural = _('вопросы теста')
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"Вопрос {self.order}: {self.text[:50]}"


class QuizOption(models.Model):
    """
    Модель варианта ответа на вопрос теста
    """
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE,
                                related_name='options', verbose_name=_('Вопрос'))
    
    # Содержимое варианта
    text = models.CharField(_('Текст варианта'), max_length=255)
    image = models.ImageField(_('Изображение'), upload_to=get_quiz_image_path, null=True, blank=True)
    
    # Правильный ли вариант
    is_correct = models.BooleanField(_('Правильный'), default=False)
    
    # Для вопросов сопоставления
    match_text = models.CharField(_('Текст для сопоставления'), max_length=255, blank=True)
    
    # Порядок отображения
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    class Meta:
        verbose_name = _('вариант ответа')
        verbose_name_plural = _('варианты ответа')
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"Вариант {self.order}: {self.text[:30]}"


class QuizAttempt(models.Model):
    """
    Модель попытки прохождения теста
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,
                            related_name='attempts', verbose_name=_('Тест'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                               related_name='quiz_attempts', verbose_name=_('Студент'))
    
    # Статус попытки
    ATTEMPT_STATUSES = (
        ('in_progress', _('В процессе')),
        ('completed', _('Завершена')),
        ('timed_out', _('Время истекло')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=ATTEMPT_STATUSES, default='in_progress')
    
    # Метаданные
    started_at = models.DateTimeField(_('Время начала'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Время завершения'), null=True, blank=True)
    time_spent = models.PositiveIntegerField(_('Затраченное время (сек)'), default=0)
    
    # Результаты
    score = models.PositiveSmallIntegerField(_('Баллы'), default=0)
    max_score = models.PositiveSmallIntegerField(_('Максимальный балл'), default=0)
    score_percentage = models.DecimalField(_('Процент'), max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(_('Пройден'), default=False)
    
    class Meta:
        verbose_name = _('попытка теста')
        verbose_name_plural = _('попытки теста')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Попытка {self.quiz} - {self.student} ({self.started_at})"
    
    def calculate_score(self):
        """
        Вычисляет результат попытки на основе ответов
        """
        # Получаем все ответы этой попытки
        answers = self.answers.all()
        
        total_points = 0
        earned_points = 0
        
        # Проверяем каждый ответ
        for answer in answers:
            question = answer.question
            total_points += question.points
            
            if answer.is_correct:
                earned_points += question.points
        
        # Обновляем результаты
        self.score = earned_points
        self.max_score = total_points
        
        if total_points > 0:
            self.score_percentage = (earned_points / total_points) * 100
        else:
            self.score_percentage = 0
        
        self.passed = self.score_percentage >= self.quiz.passing_score
        
        # Сохраняем результаты
        self.save(update_fields=['score', 'max_score', 'score_percentage', 'passed'])
        
        # Обновляем прогресс студента по элементу курса
        self.update_progress()
        
        return self.score_percentage
    
    def complete(self):
        """
        Завершает попытку и вычисляет результат
        """
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.time_spent = (self.completed_at - self.started_at).total_seconds()
            self.save(update_fields=['status', 'completed_at', 'time_spent'])
            
            # Вычисляем результат
            self.calculate_score()
    
    def update_progress(self):
        """
        Обновляет прогресс студента по элементу курса на основе результатов теста
        """
        from courses.models import CourseElementProgress, CourseEnrollment
        
        # Получаем запись на курс
        try:
            enrollment = CourseEnrollment.objects.get(
                student=self.student,
                course=self.quiz.element.course
            )
            
            # Получаем или создаем запись о прогрессе
            progress, created = CourseElementProgress.objects.get_or_create(
                enrollment=enrollment,
                course_element=self.quiz.element
            )
            
            # Если попытка завершена, обновляем информацию о прогрессе
            if self.status == 'completed':
                progress.is_viewed = True
                progress.is_completed = self.passed
                progress.grade = self.score_percentage
                progress.grade_percent = int(self.score_percentage)
                
                if not progress.first_viewed_at:
                    progress.first_viewed_at = self.started_at
                
                progress.last_viewed_at = self.completed_at
                
                if self.passed and not progress.completed_at:
                    progress.completed_at = self.completed_at
                
                progress.save()
            
        except CourseEnrollment.DoesNotExist:
            # Если записи на курс нет, ничего не делаем
            pass


class QuizAnswer(models.Model):
    """
    Модель ответа на вопрос теста
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE,
                               related_name='answers', verbose_name=_('Попытка'))
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE,
                                related_name='answers', verbose_name=_('Вопрос'))
    
    # Выбранные варианты ответов (для вопросов с выбором)
    selected_options = models.ManyToManyField(QuizOption, related_name='selected_in_answers', blank=True)
    
    # Текстовый или числовой ответ
    text_answer = models.TextField(_('Текстовый ответ'), blank=True)
    numeric_answer = models.DecimalField(_('Числовой ответ'), max_digits=15, decimal_places=5,
                                       null=True, blank=True)
    
    # Порядок вариантов (для вопросов на упорядочивание, хранится как JSON)
    order_answer = models.TextField(_('Ответ с порядком'), blank=True)
    
    # Результат ответа
    is_correct = models.BooleanField(_('Правильный'), default=False)
    partial_score = models.DecimalField(_('Частичный балл'), max_digits=5, decimal_places=2, default=0)
    
    # Метаданные
    answered_at = models.DateTimeField(_('Время ответа'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('ответ на вопрос')
        verbose_name_plural = _('ответы на вопросы')
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Ответ на {self.question} в {self.attempt}"
    
    def check_correctness(self):
        """
        Проверяет правильность ответа в зависимости от типа вопроса
        """
        question_type = self.question.question_type
        
        if question_type == 'single':
            # Один правильный вариант
            selected = self.selected_options.first()
            if selected and selected.is_correct:
                self.is_correct = True
                self.partial_score = 1.0
            else:
                self.is_correct = False
                self.partial_score = 0.0
                
        elif question_type == 'multiple':
            # Несколько правильных вариантов
            all_options = self.question.options.all()
            correct_options = self.question.options.filter(is_correct=True)
            
            if not correct_options.exists():
                self.is_correct = False
                self.partial_score = 0.0
                return
            
            selected_options = self.selected_options.all()
            selected_correct = selected_options.filter(is_correct=True)
            selected_incorrect = selected_options.filter(is_correct=False)
            
            # Все правильные выбраны и нет неправильных
            if (selected_correct.count() == correct_options.count() and 
                selected_incorrect.count() == 0):
                self.is_correct = True
                self.partial_score = 1.0
            else:
                self.is_correct = False
                
                # Частичный балл: (верно отмеченные - неверно отмеченные) / общее число правильных
                correct_count = selected_correct.count()
                incorrect_count = selected_incorrect.count()
                
                partial = (correct_count - incorrect_count) / correct_options.count()
                self.partial_score = max(0, partial)
                
        elif question_type == 'true_false':
            # Верно/неверно (аналогично одиночному выбору)
            selected = self.selected_options.first()
            if selected and selected.is_correct:
                self.is_correct = True
                self.partial_score = 1.0
            else:
                self.is_correct = False
                self.partial_score = 0.0
                
        elif question_type == 'text':
            # Текстовый ответ (требуется ручная проверка)
            # В данной реализации считаем правильным, если есть текст
            self.is_correct = False
            self.partial_score = 0.0
            
        elif question_type == 'numeric':
            # Числовой ответ (проверка на точное совпадение)
            if self.numeric_answer is not None:
                # Получаем правильный ответ из первого варианта (специфика реализации)
                correct_option = self.question.options.filter(is_correct=True).first()
                if correct_option:
                    try:
                        correct_value = float(correct_option.text)
                        if abs(self.numeric_answer - correct_value) < 0.00001:
                            self.is_correct = True
                            self.partial_score = 1.0
                        else:
                            self.is_correct = False
                            self.partial_score = 0.0
                    except (ValueError, TypeError):
                        self.is_correct = False
                        self.partial_score = 0.0
                else:
                    self.is_correct = False
                    self.partial_score = 0.0
            else:
                self.is_correct = False
                self.partial_score = 0.0
                
        elif question_type == 'matching':
            # Сопоставление (проверка каждой пары)
            if not self.order_answer:
                self.is_correct = False
                self.partial_score = 0.0
                return
            
            try:
                # В order_answer хранится JSON с сопоставлениями
                # Формат: {"option_id1": "match_id1", "option_id2": "match_id2", ...}
                matches = json.loads(self.order_answer)
                
                all_options = self.question.options.all()
                correct_count = 0
                
                for option in all_options:
                    option_id = str(option.id)
                    if option_id in matches:
                        # Проверяем, правильное ли сопоставление
                        match_id = matches[option_id]
                        try:
                            matched_option = QuizOption.objects.get(id=match_id)
                            if option.match_text == matched_option.text:
                                correct_count += 1
                        except QuizOption.DoesNotExist:
                            pass
                
                if all_options.count() > 0:
                    self.partial_score = correct_count / all_options.count()
                    self.is_correct = self.partial_score >= 1.0
                else:
                    self.is_correct = False
                    self.partial_score = 0.0
                    
            except (json.JSONDecodeError, TypeError):
                self.is_correct = False
                self.partial_score = 0.0
                
        elif question_type == 'ordering':
            # Упорядочивание
            if not self.order_answer:
                self.is_correct = False
                self.partial_score = 0.0
                return
            
            try:
                # В order_answer хранится JSON с порядком
                # Формат: [option_id1, option_id2, ...]
                order = json.loads(self.order_answer)
                
                # Получаем правильный порядок
                correct_order = list(self.question.options.order_by('order').values_list('id', flat=True))
                
                # Проверяем, совпадает ли порядок
                if len(order) == len(correct_order):
                    # Полная проверка
                    is_fully_correct = True
                    for i, opt_id in enumerate(order):
                        if int(opt_id) != correct_order[i]:
                            is_fully_correct = False
                            break
                    
                    if is_fully_correct:
                        self.is_correct = True
                        self.partial_score = 1.0
                    else:
                        # Подсчет количества правильных соседних пар
                        correct_pairs = 0
                        total_pairs = len(order) - 1
                        
                        for i in range(total_pairs):
                            curr_idx = correct_order.index(int(order[i]))
                            next_idx = correct_order.index(int(order[i+1]))
                            
                            if curr_idx + 1 == next_idx:
                                correct_pairs += 1
                        
                        if total_pairs > 0:
                            self.partial_score = correct_pairs / total_pairs
                        else:
                            self.partial_score = 0.0
                            
                        self.is_correct = self.partial_score >= 1.0
                else:
                    self.is_correct = False
                    self.partial_score = 0.0
                    
            except (json.JSONDecodeError, TypeError, ValueError):
                self.is_correct = False
                self.partial_score = 0.0
        
        # Сохраняем результат
        self.save(update_fields=['is_correct', 'partial_score'])
        
        return self.is_correct


class Assignment(models.Model):
    """
    Модель задания
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='assignment', verbose_name=_('Элемент курса'))
    
    # Описание задания
    description = models.TextField(_('Описание задания'))
    
    # Требования к выполнению
    requirements = models.TextField(_('Требования'), blank=True)
    
    # Файлы задания
    attachment = models.FileField(_('Вложение'), upload_to=get_assignment_file_path, null=True, blank=True)
    
    # Настройки проверки
    max_score = models.PositiveSmallIntegerField(_('Максимальный балл'), default=100)
    passing_score = models.PositiveSmallIntegerField(_('Проходной балл'), default=60)
    
    # Настройки сроков
    due_date = models.DateTimeField(_('Срок сдачи'), null=True, blank=True)
    late_submissions_allowed = models.BooleanField(_('Разрешить поздние сдачи'), default=True)
    late_submissions_deadline = models.DateTimeField(_('Крайний срок поздних сдач'), null=True, blank=True)
    
    # Настройки файлов ответа
    max_file_size_mb = models.PositiveSmallIntegerField(_('Максимальный размер файла (МБ)'), default=10)
    allowed_file_types = models.CharField(_('Разрешенные типы файлов'), max_length=255, blank=True,
                                        help_text=_('Список расширений файлов через запятую, например: pdf,docx,zip'))
    
    # Политика переотправки
    resubmissions_allowed = models.BooleanField(_('Разрешить переотправку'), default=True)
    max_attempts = models.PositiveSmallIntegerField(_('Максимальное количество попыток'), null=True, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('задание')
        verbose_name_plural = _('задания')
    
    def __str__(self):
        return f"Задание: {self.element.title}"
    
    @property
    def is_overdue(self):
        """Проверяет, прошел ли срок сдачи задания"""
        if not self.due_date:
            return False
        return timezone.now() > self.due_date
    
    @property
    def is_closed(self):
        """Проверяет, закрыто ли задание для сдачи"""
        if not self.late_submissions_allowed:
            return self.is_overdue
        
        if not self.late_submissions_deadline:
            return False
        
        return timezone.now() > self.late_submissions_deadline


class AssignmentSubmission(models.Model):
    """
    Модель решения задания
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE,
                                  related_name='submissions', verbose_name=_('Задание'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                               related_name='assignment_submissions', verbose_name=_('Студент'))
    
    # Текст ответа
    text_answer = models.TextField(_('Текстовый ответ'), blank=True)
    
    # Прикрепленные файлы
    file = models.FileField(_('Файл решения'), upload_to=get_solution_file_path, null=True, blank=True)
    file_name = models.CharField(_('Имя файла'), max_length=255, blank=True)
    file_size = models.PositiveIntegerField(_('Размер файла (байт)'), default=0)
    
    # Метаданные подачи
    attempt_number = models.PositiveSmallIntegerField(_('Номер попытки'), default=1)
    submission_date = models.DateTimeField(_('Дата подачи'), auto_now_add=True)
    is_late = models.BooleanField(_('Подано с опозданием'), default=False)
    
    # Статус проверки
    STATUS_CHOICES = (
        ('submitted', _('Подано')),
        ('being_checked', _('Проверяется')),
        ('graded', _('Оценено')),
        ('returned_for_revision', _('Возвращено на доработку')),
    )
    status = models.CharField(_('Статус'), max_length=25, choices=STATUS_CHOICES, default='submitted')
    
    # Оценка
    score = models.PositiveSmallIntegerField(_('Баллы'), null=True, blank=True)
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                 related_name='graded_submissions', null=True, blank=True,
                                 verbose_name=_('Проверил'))
    graded_at = models.DateTimeField(_('Дата проверки'), null=True, blank=True)
    
    # Комментарии
    feedback = models.TextField(_('Отзыв преподавателя'), blank=True)
    
    class Meta:
        verbose_name = _('решение задания')
        verbose_name_plural = _('решения заданий')
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"Решение {self.assignment} от {self.student}"
    
    
class Discussion(models.Model):
    """
    Модель обсуждения (форума)
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='discussion', verbose_name=_('Элемент курса'))
    
    # Настройки обсуждения
    description = models.TextField(_('Описание обсуждения'), blank=True)
    is_graded = models.BooleanField(_('Оцениваемое обсуждение'), default=False)
    max_score = models.PositiveSmallIntegerField(_('Максимальный балл'), default=10)
    
    # Требования к участию
    required_posts = models.PositiveSmallIntegerField(_('Необходимое количество постов'), default=1)
    required_replies = models.PositiveSmallIntegerField(_('Необходимое количество ответов'), default=2)
    
    # Дополнительные настройки
    allow_anonymous = models.BooleanField(_('Разрешить анонимные сообщения'), default=False)
    require_approval = models.BooleanField(_('Требуется одобрение сообщений'), default=False)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('обсуждение')
        verbose_name_plural = _('обсуждения')
    
    def __str__(self):
        return f"Обсуждение: {self.element.title}"


class DiscussionTopic(models.Model):
    """
    Модель темы обсуждения
    """
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE,
                                  related_name='topics', verbose_name=_('Обсуждение'))
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                              related_name='discussion_topics', verbose_name=_('Автор'))
    
    # Содержимое
    title = models.CharField(_('Заголовок'), max_length=255)
    content = models.TextField(_('Содержимое'))
    
    # Настройки отображения
    is_pinned = models.BooleanField(_('Закреплено'), default=False)
    is_closed = models.BooleanField(_('Закрыто'), default=False)
    is_anonymous = models.BooleanField(_('Анонимно'), default=False)
    
    # Статус модерации
    is_approved = models.BooleanField(_('Одобрено'), default=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                   related_name='approved_topics', null=True, blank=True,
                                   verbose_name=_('Одобрил'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    
    class Meta:
        verbose_name = _('тема обсуждения')
        verbose_name_plural = _('темы обсуждения')
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title


class DiscussionMessage(models.Model):
    """
    Модель сообщения в обсуждении
    """
    topic = models.ForeignKey(DiscussionTopic, on_delete=models.CASCADE,
                             related_name='messages', verbose_name=_('Тема'))
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                              related_name='discussion_messages', verbose_name=_('Автор'))
    
    # Связь с родительским сообщением (для ответов)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                              related_name='replies', null=True, blank=True,
                              verbose_name=_('Родительское сообщение'))
    
    # Содержимое
    content = models.TextField(_('Содержимое'))
    
    # Настройки отображения
    is_solution = models.BooleanField(_('Отмечено как решение'), default=False)
    is_anonymous = models.BooleanField(_('Анонимно'), default=False)
    
    # Статус модерации
    is_approved = models.BooleanField(_('Одобрено'), default=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                   related_name='approved_messages', null=True, blank=True,
                                   verbose_name=_('Одобрил'))
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Рейтинг
    upvotes = models.ManyToManyField('accounts.User', related_name='upvoted_messages', blank=True)
    downvotes = models.ManyToManyField('accounts.User', related_name='downvoted_messages', blank=True)
    
    class Meta:
        verbose_name = _('сообщение обсуждения')
        verbose_name_plural = _('сообщения обсуждения')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Сообщение от {self.author} в {self.topic}"
    
    @property
    def rating(self):
        """Вычисляет рейтинг сообщения"""
        return self.upvotes.count() - self.downvotes.count()


class DiscussionAttachment(models.Model):
    """
    Модель вложения к сообщению в обсуждении
    """
    message = models.ForeignKey(DiscussionMessage, on_delete=models.CASCADE,
                               related_name='attachments', verbose_name=_('Сообщение'))
    file = models.FileField(_('Файл'), upload_to='discussion_attachments/')
    filename = models.CharField(_('Имя файла'), max_length=255)
    file_size = models.PositiveIntegerField(_('Размер файла'), default=0)  # В байтах
    
    class Meta:
        verbose_name = _('вложение к обсуждению')
        verbose_name_plural = _('вложения к обсуждениям')
    
    def __str__(self):
        return f"{self.filename} ({self.message})"


class DiscussionParticipation(models.Model):
    """
    Модель участия студента в обсуждении (для оценивания)
    """
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE,
                                  related_name='participations', verbose_name=_('Обсуждение'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                               related_name='discussion_participations', verbose_name=_('Студент'))
    
    # Статистика
    topics_created = models.PositiveSmallIntegerField(_('Создано тем'), default=0)
    messages_posted = models.PositiveSmallIntegerField(_('Отправлено сообщений'), default=0)
    replies_posted = models.PositiveSmallIntegerField(_('Отправлено ответов'), default=0)
    
    # Оценка (для оцениваемых обсуждений)
    grade = models.PositiveSmallIntegerField(_('Оценка'), null=True, blank=True)
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                 related_name='graded_discussions', null=True, blank=True,
                                 verbose_name=_('Оценил'))
    graded_at = models.DateTimeField(_('Дата оценки'), null=True, blank=True)
    feedback = models.TextField(_('Отзыв преподавателя'), blank=True)
    
    class Meta:
        verbose_name = _('участие в обсуждении')
        verbose_name_plural = _('участие в обсуждениях')
        unique_together = ['discussion', 'student']
    
    def __str__(self):
        return f"Участие {self.student} в {self.discussion}"
    
    def update_statistics(self):
        """
        Обновляет статистику участия
        """
        # Количество созданных тем
        self.topics_created = DiscussionTopic.objects.filter(
            discussion=self.discussion,
            author=self.student.user
        ).count()
        
        # Количество отправленных сообщений (всего)
        self.messages_posted = DiscussionMessage.objects.filter(
            topic__discussion=self.discussion,
            author=self.student.user
        ).count()
        
        # Количество ответов
        self.replies_posted = DiscussionMessage.objects.filter(
            topic__discussion=self.discussion,
            author=self.student.user,
            parent__isnull=False
        ).count()
        
        self.save(update_fields=['topics_created', 'messages_posted', 'replies_posted'])
    
    def update_progress(self):
        """
        Обновляет прогресс студента по элементу курса
        """
        from courses.models import CourseElementProgress, CourseEnrollment
        
        # Только для оцененных обсуждений
        if not self.discussion.is_graded or self.grade is None:
            return
        
        # Получаем запись на курс
        try:
            enrollment = CourseEnrollment.objects.get(
                student=self.student,
                course=self.discussion.element.course
            )
            
            # Получаем или создаем запись о прогрессе
            progress, created = CourseElementProgress.objects.get_or_create(
                enrollment=enrollment,
                course_element=self.discussion.element
            )
            
            # Обновляем прогресс
            progress.is_viewed = True
            progress.is_completed = self.messages_posted >= self.discussion.required_posts and \
                                   self.replies_posted >= self.discussion.required_replies
            
            progress.grade = self.grade
            progress.grade_percent = int((self.grade / self.discussion.max_score) * 100)
            
            if not progress.first_viewed_at:
                # Получаем время первого сообщения
                first_message = DiscussionMessage.objects.filter(
                    topic__discussion=self.discussion,
                    author=self.student.user
                ).order_by('created_at').first()
                
                if first_message:
                    progress.first_viewed_at = first_message.created_at
                else:
                    progress.first_viewed_at = timezone.now()
            
            # Получаем время последнего сообщения
            last_message = DiscussionMessage.objects.filter(
                topic__discussion=self.discussion,
                author=self.student.user
            ).order_by('-created_at').first()
            
            if last_message:
                progress.last_viewed_at = last_message.created_at
            else:
                progress.last_viewed_at = timezone.now()
            
            if progress.is_completed and not progress.completed_at:
                progress.completed_at = self.graded_at or progress.last_viewed_at
            
            progress.save()
            
        except CourseEnrollment.DoesNotExist:
            # Если записи на курс нет, ничего не делаем
            pass


class Survey(models.Model):
    """
    Модель опроса
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='survey', verbose_name=_('Элемент курса'))
    
    # Описание опроса
    description = models.TextField(_('Описание опроса'), blank=True)
    
    # Настройки опроса
    is_anonymous = models.BooleanField(_('Анонимный опрос'), default=True)
    show_results = models.BooleanField(_('Показывать результаты'), default=True)
    allow_multiple_submissions = models.BooleanField(_('Разрешить несколько попыток'), default=False)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('опрос')
        verbose_name_plural = _('опросы')
    
    def __str__(self):
        return f"Опрос: {self.element.title}"


class SurveyQuestion(models.Model):
    """
    Модель вопроса опроса
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE,
                              related_name='questions', verbose_name=_('Опрос'))
    
    # Содержимое вопроса
    text = models.TextField(_('Текст вопроса'))
    
    # Тип вопроса
    QUESTION_TYPES = (
        ('text', _('Текстовый ответ')),
        ('textarea', _('Многострочный текст')),
        ('single', _('Одиночный выбор')),
        ('multiple', _('Множественный выбор')),
        ('likert', _('Шкала Ликерта')),
        ('rating', _('Рейтинговая шкала')),
    )
    question_type = models.CharField(_('Тип вопроса'), max_length=20, choices=QUESTION_TYPES)
    
    # Дополнительные параметры
    is_required = models.BooleanField(_('Обязательный вопрос'), default=True)
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    # Для рейтинговых шкал
    scale_min = models.SmallIntegerField(_('Минимальное значение шкалы'), default=1)
    scale_max = models.SmallIntegerField(_('Максимальное значение шкалы'), default=5)
    scale_min_label = models.CharField(_('Подпись минимума'), max_length=100, blank=True)
    scale_max_label = models.CharField(_('Подпись максимума'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('вопрос опроса')
        verbose_name_plural = _('вопросы опроса')
        ordering = ['survey', 'order']
    
    def __str__(self):
        return f"Вопрос {self.order}: {self.text[:50]}"


class SurveyOption(models.Model):
    """
    Модель варианта ответа на вопрос опроса
    """
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE,
                                related_name='options', verbose_name=_('Вопрос'))
    
    # Содержимое варианта
    text = models.CharField(_('Текст варианта'), max_length=255)
    
    # Порядок отображения
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    class Meta:
        verbose_name = _('вариант ответа опроса')
        verbose_name_plural = _('варианты ответа опроса')
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"Вариант {self.order}: {self.text[:30]}"


class SurveySubmission(models.Model):
    """
    Модель заполненного опроса
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE,
                              related_name='submissions', verbose_name=_('Опрос'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                               related_name='survey_submissions', verbose_name=_('Студент'),
                               null=True, blank=True)  # Может быть NULL для анонимных опросов
    
    # Метаданные
    submission_date = models.DateTimeField(_('Дата отправки'), auto_now_add=True)
    attempt_number = models.PositiveSmallIntegerField(_('Номер попытки'), default=1)
    
    class Meta:
        verbose_name = _('ответ на опрос')
        verbose_name_plural = _('ответы на опрос')
        ordering = ['-submission_date']
    
    def __str__(self):
        if self.student:
            return f"Ответ на опрос {self.survey} от {self.student}"
        return f"Анонимный ответ на опрос {self.survey} ({self.submission_date})"
    
    def update_progress(self):
        """
        Обновляет прогресс студента по элементу курса
        """
        from courses.models import CourseElementProgress, CourseEnrollment
        
        # Только для идентифицированных студентов
        if not self.student:
            return
        
        # Получаем запись на курс
        try:
            enrollment = CourseEnrollment.objects.get(
                student=self.student,
                course=self.survey.element.course
            )
            
            # Получаем или создаем запись о прогрессе
            progress, created = CourseElementProgress.objects.get_or_create(
                enrollment=enrollment,
                course_element=self.survey.element
            )
            
            # Обновляем прогресс
            progress.is_viewed = True
            progress.is_completed = True  # Если опрос отправлен, считаем его завершенным
            
            if not progress.first_viewed_at:
                progress.first_viewed_at = self.submission_date
            
            progress.last_viewed_at = self.submission_date
            
            if not progress.completed_at:
                progress.completed_at = self.submission_date
            
            progress.save()
            
        except CourseEnrollment.DoesNotExist:
            # Если записи на курс нет, ничего не делаем
            pass


class SurveyAnswer(models.Model):
    """
    Модель ответа на вопрос опроса
    """
    submission = models.ForeignKey(SurveySubmission, on_delete=models.CASCADE,
                                  related_name='answers', verbose_name=_('Отправка'))
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE,
                                related_name='answers', verbose_name=_('Вопрос'))
    
    # Различные типы ответов
    text_answer = models.TextField(_('Текстовый ответ'), blank=True)
    selected_options = models.ManyToManyField(SurveyOption, related_name='selected_in_answers', blank=True)
    numeric_answer = models.SmallIntegerField(_('Числовой ответ'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('ответ на вопрос опроса')
        verbose_name_plural = _('ответы на вопросы опроса')
        unique_together = ['submission', 'question']
    
    def __str__(self):
        return f"Ответ на вопрос {self.question} в {self.submission}"


class InteractiveContent(models.Model):
    """
    Модель интерактивного содержимого
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='interactive_content', verbose_name=_('Элемент курса'))
    
    # Тип интерактивного содержимого
    CONTENT_TYPES = (
        ('h5p', _('H5P')),
        ('embedded', _('Внешнее встроенное содержимое')),
        ('iframe', _('iFrame')),
        ('custom', _('Свой HTML/JavaScript')),
    )
    content_type = models.CharField(_('Тип содержимого'), max_length=20, choices=CONTENT_TYPES)
    
    # Содержимое
    content_url = models.URLField(_('URL содержимого'), blank=True)
    content_embed_code = models.TextField(_('Код встраивания'), blank=True)
    content_html = models.TextField(_('HTML-содержимое'), blank=True)
    content_js = models.TextField(_('JavaScript-содержимое'), blank=True)
    
    # H5P-контент
    h5p_content_id = models.PositiveIntegerField(_('ID H5P-контента'), null=True, blank=True)
    
    # Настройки отображения
    width = models.CharField(_('Ширина'), max_length=20, default='100%')
    height = models.CharField(_('Высота'), max_length=20, default='600px')
    
    # Настройки безопасности
    allow_fullscreen = models.BooleanField(_('Разрешить полноэкранный режим'), default=True)
    
    # Оценивание
    is_gradable = models.BooleanField(_('Оцениваемый элемент'), default=False)
    max_score = models.PositiveSmallIntegerField(_('Максимальный балл'), default=100)
    passing_score = models.PositiveSmallIntegerField(_('Проходной балл (%)'), default=70)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('интерактивное содержимое')
        verbose_name_plural = _('интерактивное содержимое')
    
    def __str__(self):
        return f"Интерактивное содержимое: {self.element.title}"


class InteractiveAttempt(models.Model):
    """
    Модель попытки интерактивного содержимого
    """
    interactive_content = models.ForeignKey(InteractiveContent, on_delete=models.CASCADE,
                                          related_name='attempts', verbose_name=_('Интерактивное содержимое'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                               related_name='interactive_attempts', verbose_name=_('Студент'))
    
    # Результаты
    score = models.PositiveSmallIntegerField(_('Баллы'), default=0)
    max_score = models.PositiveSmallIntegerField(_('Максимальный балл'), default=0)
    score_percentage = models.DecimalField(_('Процент'), max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(_('Пройден'), default=False)
    
    # Данные, возвращаемые интерактивным содержимым
    raw_result = models.JSONField(_('Результаты в JSON'), default=dict, blank=True)
    
    # Метаданные
    started_at = models.DateTimeField(_('Время начала'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Время завершения'), null=True, blank=True)
    time_spent = models.PositiveIntegerField(_('Затраченное время (сек)'), default=0)
    
    class Meta:
        verbose_name = _('попытка интерактивного содержимого')
        verbose_name_plural = _('попытки интерактивного содержимого')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Попытка {self.interactive_content} - {self.student}"
    
    def complete(self, raw_result=None, score=None, max_score=None):
        """
        Завершает попытку и записывает результаты
        """
        self.completed_at = timezone.now()
        self.time_spent = (self.completed_at - self.started_at).total_seconds()
        
        if raw_result:
            self.raw_result = raw_result
        
        if score is not None:
            self.score = score
        
        if max_score is not None and max_score > 0:
            self.max_score = max_score
            self.score_percentage = (self.score / self.max_score) * 100
        else:
            self.score_percentage = 0
        
        self.passed = self.score_percentage >= self.interactive_content.passing_score
        
        self.save()
        
        # Обновляем прогресс
        self.update_progress()
        
        return self.passed
    
    def update_progress(self):
        """
        Обновляет прогресс студента по элементу курса
        """
        from courses.models import CourseElementProgress, CourseEnrollment
        
        # Только для оцениваемого контента
        if not self.interactive_content.is_gradable:
            return
        
        # Получаем запись на курс
        try:
            enrollment = CourseEnrollment.objects.get(
                student=self.student,
                course=self.interactive_content.element.course
            )
            
            # Получаем или создаем запись о прогрессе
            progress, created = CourseElementProgress.objects.get_or_create(
                enrollment=enrollment,
                course_element=self.interactive_content.element
            )
            
            # Обновляем прогресс
            progress.is_viewed = True
            progress.is_completed = self.passed
            progress.grade = self.score
            progress.grade_percent = int(self.score_percentage)
            
            if not progress.first_viewed_at:
                progress.first_viewed_at = self.started_at
            
            progress.last_viewed_at = self.completed_at or timezone.now()
            
            if self.passed and not progress.completed_at:
                progress.completed_at = self.completed_at
            
            progress.save()
            
        except CourseEnrollment.DoesNotExist:
            # Если записи на курс нет, ничего не делаем
            pass


class Webinar(models.Model):
    """
    Модель вебинара
    """
    element = models.OneToOneField('courses.CourseElement', on_delete=models.CASCADE,
                                  related_name='webinar', verbose_name=_('Элемент курса'))
    
    # Тип вебинара
    WEBINAR_TYPES = (
        ('live', _('Живая трансляция')),
        ('recorded', _('Запись')),
        ('upcoming', _('Предстоящий вебинар')),
    )
    webinar_type = models.CharField(_('Тип вебинара'), max_length=20, choices=WEBINAR_TYPES)
    
    # Информация о времени проведения
    start_datetime = models.DateTimeField(_('Дата и время начала'), null=True, blank=True)
    end_datetime = models.DateTimeField(_('Дата и время окончания'), null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(_('Длительность (мин)'), default=60)
    timezone_info = models.CharField(_('Часовой пояс'), max_length=50, blank=True)
    
    # Описание и информация для студентов
    description = models.TextField(_('Описание вебинара'), blank=True)
    prerequisites = models.TextField(_('Требования для участия'), blank=True)
    
    # Платформа проведения
    PLATFORM_CHOICES = (
        ('zoom', _('Zoom')),
        ('teams', _('Microsoft Teams')),
        ('meet', _('Google Meet')),
        ('skype', _('Skype')),
        ('webex', _('Cisco Webex')),
        ('youtube', _('YouTube Live')),
        ('custom', _('Другая платформа')),
    )
    platform = models.CharField(_('Платформа'), max_length=20, choices=PLATFORM_CHOICES)
    platform_name = models.CharField(_('Название платформы'), max_length=100, blank=True)
    
    # Данные для подключения
    meeting_url = models.URLField(_('Ссылка на встречу'), blank=True)
    meeting_id = models.CharField(_('ID встречи'), max_length=100, blank=True)
    password = models.CharField(_('Пароль'), max_length=100, blank=True)
    
    # Записанный вебинар
    recording_url = models.URLField(_('Ссылка на запись'), blank=True)
    
    # Дополнительные материалы
    presentation_file = models.FileField(_('Файл презентации'), upload_to='webinar_files/', null=True, blank=True)
    
    # Ведущие
    host = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE,
                           related_name='hosted_webinars', verbose_name=_('Ведущий'))
    co_hosts = models.ManyToManyField('accounts.TeacherProfile', related_name='co_hosted_webinars',
                                    blank=True, verbose_name=_('Со-ведущие'))
    
    # Настройки присутствия
    track_attendance = models.BooleanField(_('Отслеживать присутствие'), default=True)
    minimum_attendance_minutes = models.PositiveSmallIntegerField(_('Минимальное время присутствия (мин)'),
                                                               default=45)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('вебинар')
        verbose_name_plural = _('вебинары')
    
    def __str__(self):
        return f"Вебинар: {self.element.title}"
    
    @property
    def is_past(self):
        """Проверяет, прошел ли вебинар"""
        if not self.start_datetime:
            return False
        return timezone.now() > self.start_datetime
    
    @property
    def is_live(self):
        """Проверяет, идет ли вебинар сейчас"""
        if not self.start_datetime or not self.end_datetime:
            return False
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime


class WebinarAttendance(models.Model):
    """
    Модель посещения вебинара
    """
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE,
                               related_name='attendances', verbose_name=_('Вебинар'))
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE,
                               related_name='webinar_attendances', verbose_name=_('Студент'))
    
    # Информация о посещении
    joined_at = models.DateTimeField(_('Время входа'), null=True, blank=True)
    left_at = models.DateTimeField(_('Время выхода'), null=True, blank=True)
    attendance_minutes = models.PositiveSmallIntegerField(_('Время присутствия (мин)'), default=0)
    
    # Статус присутствия
    STATUS_CHOICES = (
        ('registered', _('Зарегистрирован')),
        ('attended', _('Присутствовал')),
        ('partial', _('Частично присутствовал')),
        ('absent', _('Отсутствовал')),
        ('watched_recording', _('Просмотрел запись')),
    )
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES, default='registered')
    
    # Дополнительная информация
    has_participated = models.BooleanField(_('Участвовал в обсуждении'), default=False)
    ip_address = models.GenericIPAddressField(_('IP-адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User-Agent'), blank=True)
    
    # Комментарии преподавателя
    teacher_notes = models.TextField(_('Заметки преподавателя'), blank=True)
    
    class Meta:
        verbose_name = _('посещение вебинара')
        verbose_name_plural = _('посещения вебинаров')
        unique_together = ['webinar', 'student']
    
    def __str__(self):
        return f"Посещение {self.webinar} - {self.student}"
    
    def update_progress(self):
        """
        Обновляет прогресс студента по элементу курса
        """
        from courses.models import CourseElementProgress, CourseEnrollment
        
        # Определяем, засчитывается ли посещение
        is_completed = False
        
        if self.status == 'attended':
            is_completed = True
        elif self.status == 'partial' and self.attendance_minutes >= self.webinar.minimum_attendance_minutes:
            is_completed = True
        elif self.status == 'watched_recording':
            is_completed = True
        
        # Получаем запись на курс
        try:
            enrollment = CourseEnrollment.objects.get(
                student=self.student,
                course=self.webinar.element.course
            )
            
            # Получаем или создаем запись о прогрессе
            progress, created = CourseElementProgress.objects.get_or_create(
                enrollment=enrollment,
                course_element=self.webinar.element
            )
            
            # Обновляем прогресс
            progress.is_viewed = self.status in ['attended', 'partial', 'watched_recording']
            progress.is_completed = is_completed
            
            if not progress.first_viewed_at and self.joined_at:
                progress.first_viewed_at = self.joined_at
            
            if self.left_at:
                progress.last_viewed_at = self.left_at
            
            if is_completed and not progress.completed_at:
                progress.completed_at = self.left_at or timezone.now()
            
            progress.save()
            
        except CourseEnrollment.DoesNotExist:
            # Если записи на курс нет, ничего не делаем
            pass


# Сигналы для автоматизации работы
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='courses.CourseElement')
def create_element_content(sender, instance, created, **kwargs):
    """
    Создает соответствующий контент в зависимости от типа элемента курса
    """
    if created and hasattr(instance, 'element_type'):
        element_type_code = instance.element_type.code
        
        # Создаем соответствующий контент в зависимости от типа элемента
        if element_type_code == 'lecture':
            LectureContent.objects.create(element=instance)
        elif element_type_code == 'video':
            VideoContent.objects.create(element=instance)
        elif element_type_code == 'quiz':
            Quiz.objects.create(element=instance)
        elif element_type_code == 'assignment':
            Assignment.objects.create(element=instance)
        elif element_type_code == 'discussion':
            Discussion.objects.create(element=instance)
        elif element_type_code == 'survey':
            Survey.objects.create(element=instance)
        elif element_type_code == 'interactive':
            InteractiveContent.objects.create(element=instance)
        elif element_type_code == 'webinar':
            # Для вебинара требуется дополнительная информация, поэтому создаем базовую запись
            # Далее преподаватель должен заполнить остальную информацию
            Webinar.objects.create(
                element=instance,
                webinar_type='upcoming',
                host=instance.course.author.teacher_profile  # Предполагаем, что автор курса - преподаватель
            )

@receiver(post_save, sender=QuizAttempt)
def update_quiz_progress(sender, instance, **kwargs):
    """
    Обновляет прогресс по элементу курса при завершении попытки теста
    """
    if instance.status == 'completed':
        # Получаем элемент прогресса
        from courses.models import CourseElementProgress, CourseEnrollment
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=instance.student,
                course=instance.quiz.element.course
            )
            
            progress, created = CourseElementProgress.objects.get_or_create(
                enrollment=enrollment,
                course_element=instance.quiz.element
            )
            
            # Обновляем прогресс
            progress.is_viewed = True
            progress.is_completed = instance.passed
            
            # Записываем оценку
            progress.grade = instance.score_percentage
            progress.grade_percent = int(instance.score_percentage)
            
            if not progress.first_viewed_at:
                progress.first_viewed_at = instance.started_at
            
            progress.last_viewed_at = instance.completed_at
            
            if instance.passed and not progress.completed_at:
                progress.completed_at = instance.completed_at
            
            progress.save()
            
        except CourseEnrollment.DoesNotExist:
            # Если записи на курс нет, ничего не делаем
            pass

@receiver(post_save, sender=AssignmentSubmission)
def update_assignment_status(sender, instance, **kwargs):
    """
    Обновляет статус задания при изменении решения
    """
    if instance.status == 'graded':
        instance.update_progress()