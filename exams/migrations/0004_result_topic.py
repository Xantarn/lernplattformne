# Generated migration to add topic to Result

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_topicfavorite'),
        ('exams', '0003_add_lesson_to_result_and_question'),
    ]

    operations = [
        # Add topic to Result model
        migrations.AddField(
            model_name='result',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quiz_results', to='courses.topic'),
        ),
    ]
