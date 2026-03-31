# Generated migration to add topic to Question

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_topicfavorite'),
        ('quiz', '0008_question_lesson'),
    ]

    operations = [
        # Add topic to Question model
        migrations.AddField(
            model_name='question',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.topic'),
        ),
    ]
