from django.conf import settings
from django.db import models

from opportunities.models import Department


class UserProfile(models.Model):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
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

    class Meta:
        db_table = 'opportunities_userprofile'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
