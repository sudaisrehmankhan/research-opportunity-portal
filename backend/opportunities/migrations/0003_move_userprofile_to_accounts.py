from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('opportunities', '0002_department_opportunity_owner_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='UserProfile'),
            ],
        ),
    ]
