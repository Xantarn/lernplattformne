# Generated migration to add lesson support to Result

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_topicfavorite'),
        ('exams', '0002_gamification'),
    ]

    operations = [
        # Add lesson to Result model
        migrations.AddField(
            model_name='result',
            name='lesson',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quiz_results', to='courses.lesson'),
        ),
    ]
