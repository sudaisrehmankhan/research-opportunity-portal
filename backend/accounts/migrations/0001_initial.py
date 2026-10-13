import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def move_profile_content_type_to_accounts(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    old_content_type = ContentType.objects.filter(
        app_label='opportunities',
        model='userprofile',
    ).first()
    if old_content_type is None:
        return
    if ContentType.objects.filter(app_label='accounts', model='userprofile').exists():
        raise RuntimeError('Both old and new UserProfile content types exist; refusing to merge implicitly.')
    old_content_type.app_label = 'accounts'
    old_content_type.save(update_fields=['app_label'])


def move_profile_content_type_to_opportunities(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(
        app_label='accounts',
        model='userprofile',
    ).update(app_label='opportunities')


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('opportunities', '0002_department_opportunity_owner_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='UserProfile',
                    fields=[
                        (
                            'id',
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name='ID',
                            ),
                        ),
                        (
                            'role',
                            models.CharField(
                                choices=[('student', 'Student'), ('teacher', 'Teacher')],
                                max_length=10,
                            ),
                        ),
                        ('phone', models.CharField(blank=True, max_length=30)),
                        ('student_number', models.CharField(blank=True, max_length=40)),
                        ('program', models.CharField(blank=True, max_length=120)),
                        ('position_title', models.CharField(blank=True, max_length=120)),
                        (
                            'department',
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name='members',
                                to='opportunities.department',
                            ),
                        ),
                        (
                            'user',
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='profile',
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={'db_table': 'opportunities_userprofile'},
                ),
            ],
        ),
        migrations.RunPython(
            move_profile_content_type_to_accounts,
            move_profile_content_type_to_opportunities,
        ),
    ]
