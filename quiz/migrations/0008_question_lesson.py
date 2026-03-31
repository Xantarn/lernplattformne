# Generated migration to add lesson support to Question

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_topicfavorite'),
        ('quiz', '0007_question_code_validation_fields'),
    ]

    operations = [
        # Add lesson to Question model
        migrations.AddField(
            model_name='question',
            name='lesson',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.lesson'),
        ),
    ]
