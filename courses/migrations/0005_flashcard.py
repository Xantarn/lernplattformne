from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_topic'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flashcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('front', models.TextField(help_text='Vorderseite der Karte (Frage)')),
                ('back', models.TextField(help_text='Rückseite der Karte (Antwort)')),
                ('order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcards', to='courses.course')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
    ]
