from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0005_question_types_and_payload_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='difficulty',
            field=models.CharField(choices=[('easy', 'Einfach (10 XP)'), ('medium', 'Mittel (25 XP)'), ('hard', 'Schwer (50 XP)')], default='medium', max_length=20),
        ),
        migrations.AddField(
            model_name='question',
            name='common_mistakes',
            field=models.TextField(blank=True, help_text='Häufige Fehler (durch Komma getrennt)'),
        ),
    ]
