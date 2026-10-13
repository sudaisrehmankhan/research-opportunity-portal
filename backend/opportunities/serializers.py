from django.utils import timezone

from rest_framework import serializers

from accounts.models import UserProfile

from .models import Department, Opportunity


class OpportunitySerializer(serializers.ModelSerializer):
    title = serializers.CharField(trim_whitespace=True, allow_blank=False)
    description = serializers.CharField(trim_whitespace=True, allow_blank=False)
    research_area = serializers.CharField(trim_whitespace=True, allow_blank=False)
    faculty_name = serializers.CharField(read_only=True)
    required_skills = serializers.CharField(trim_whitespace=True, allow_blank=False)
    available_positions = serializers.IntegerField(min_value=1)
    application_deadline = serializers.DateField()
    status = serializers.ChoiceField(
        choices=Opportunity.STATUS_CHOICES,
        required=False,
        default='Open',
    )
    department = serializers.CharField(trim_whitespace=True, allow_blank=False)
    owner_id = serializers.IntegerField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True, default=None)

    class Meta:
        model = Opportunity
        fields = [
            'id',
            'title',
            'description',
            'research_area',
            'faculty_name',
            'department',
            'required_skills',
            'available_positions',
            'application_deadline',
            'status',
            'owner_id',
            'owner_username',
        ]

    def validate_department(self, value):
        department = Department.objects.filter(name__iexact=value).first()
        if department is None:
            raise serializers.ValidationError('Choose a department managed by the university.')
        request = self.context.get('request')
        profile = getattr(request.user, 'profile', None) if request and request.user.is_authenticated else None
        if profile and profile.role == UserProfile.TEACHER and not request.user.is_staff:
            if profile.department_id != department.id:
                raise serializers.ValidationError('Teachers can only manage opportunities in their department.')
        return department.name

    def validate(self, attrs):
        deadline = attrs.get('application_deadline')
        status = attrs.get('status', getattr(self.instance, 'status', 'Open'))
        if status == 'Open' and deadline and deadline < timezone.localdate():
            raise serializers.ValidationError({
                'application_deadline': 'Open opportunities must have a future deadline.',
            })
        return attrs

    def create(self, validated_data):
        department_name = validated_data['department']
        validated_data.pop('department')
        validated_data['department_record'] = Department.objects.get(name__iexact=department_name)
        request = self.context['request']
        validated_data['owner'] = request.user
        validated_data['faculty_name'] = request.user.get_full_name() or request.user.username
        return super().create(validated_data)

    def update(self, instance, validated_data):
        department_name = validated_data.get('department')
        if department_name is not None:
            instance.department = department_name
            validated_data['department_record'] = Department.objects.get(name__iexact=department_name)
        validated_data.pop('department', None)
        return super().update(instance, validated_data)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']
