from django import forms
from django.utils import timezone

from accounts.models import UserProfile

from .models import Department, Opportunity


class OpportunityForm(forms.ModelForm):
    department = forms.ChoiceField()

    class Meta:
        model = Opportunity
        fields = [
            'title',
            'description',
            'research_area',
            'department',
            'required_skills',
            'available_positions',
            'application_deadline',
            'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'id': 'title'}),
            'description': forms.Textarea(attrs={'id': 'description'}),
            'research_area': forms.TextInput(attrs={'id': 'research_area'}),
            'required_skills': forms.TextInput(attrs={'id': 'required_skills'}),
            'available_positions': forms.NumberInput(attrs={'id': 'available_positions', 'min': 1}),
            'application_deadline': forms.DateInput(
                attrs={'id': 'application_deadline', 'type': 'date'},
            ),
            'status': forms.Select(attrs={'id': 'status'}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        profile = UserProfile.objects.select_related('department').filter(user=user).first()
        departments = Department.objects.all()
        if profile and profile.role == UserProfile.TEACHER and not user.is_staff:
            departments = departments.filter(pk=profile.department_id)
        self.fields['department'].choices = [
            ('', 'Choose a department'),
            *((department.name, department.name) for department in departments),
        ]
        if profile and profile.department:
            self.fields['department'].initial = profile.department.name

    def clean_available_positions(self):
        positions = self.cleaned_data['available_positions']
        if positions < 1:
            raise forms.ValidationError('At least one position must be available.')
        return positions

    def clean(self):
        cleaned_data = super().clean()
        deadline = cleaned_data.get('application_deadline')
        status = cleaned_data.get('status', 'Open')
        if status == 'Open' and deadline and deadline < timezone.localdate():
            self.add_error(
                'application_deadline',
                'Open opportunities must have a future application deadline.',
            )
        return cleaned_data

    def save(self, commit=True):
        opportunity = super().save(commit=False)
        profile = UserProfile.objects.select_related('department').filter(user=self.user).first()
        opportunity.department = self.cleaned_data['department']
        opportunity.faculty_name = self.user.get_full_name() or self.user.username
        if opportunity.pk is None:
            opportunity.owner = self.user
        if profile and profile.role == UserProfile.TEACHER and not self.user.is_staff:
            opportunity.department = profile.department.name
        if commit:
            opportunity.save()
        return opportunity
