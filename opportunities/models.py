from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='members',
    )
    phone = models.CharField(max_length=30, blank=True)
    student_number = models.CharField(max_length=40, blank=True)
    program = models.CharField(max_length=120, blank=True)
    position_title = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


class Opportunity(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    research_area = models.CharField(max_length=100)
    faculty_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    required_skills = models.TextField()
    available_positions = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    application_deadline = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Open',
    )
    department_record = models.ForeignKey(
        Department,
        null=True,
        on_delete=models.PROTECT,
        related_name='opportunities',
    )
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='research_opportunities',
    )

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if self.department:
            department, _ = Department.objects.get_or_create(name=self.department.strip())
            self.department_record = department
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
