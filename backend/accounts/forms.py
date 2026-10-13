from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from opportunities.models import Department

from .models import UserProfile


class RegistrationForm(UserCreationForm):
    ROLE_CHOICES = [
        (UserProfile.STUDENT, 'Student'),
        (UserProfile.TEACHER, 'Teacher'),
    ]

    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    phone = forms.CharField(max_length=30, required=False)
    student_number = forms.CharField(max_length=40, required=False)
    program = forms.CharField(max_length=120, required=False)
    position_title = forms.CharField(max_length=120, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role', 'department',
            'phone', 'student_number', 'program', 'position_title',
        )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        department = cleaned_data.get('department')
        if role == UserProfile.TEACHER and not department:
            self.add_error('department', 'Teachers must select their department.')
        if role == UserProfile.STUDENT and not cleaned_data.get('student_number'):
            self.add_error('student_number', 'Students must enter their student ID.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                department=self.cleaned_data.get('department'),
                phone=self.cleaned_data.get('phone', ''),
                student_number=self.cleaned_data.get('student_number', ''),
                program=self.cleaned_data.get('program', ''),
                position_title=self.cleaned_data.get('position_title', ''),
            )
        return user
