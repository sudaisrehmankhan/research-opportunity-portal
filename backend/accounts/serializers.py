from rest_framework import serializers

from opportunities.models import Department

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    department = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Department.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name', 'role', 'department',
            'phone', 'student_number', 'program', 'position_title',
        ]
        read_only_fields = ['role']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        instance.user.save()
        return super().update(instance, validated_data)
