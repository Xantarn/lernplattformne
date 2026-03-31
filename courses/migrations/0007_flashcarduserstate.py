from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0006_alter_flashcard_back_flashcardoption"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FlashcardUserState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_favorite", models.BooleanField(default=False)),
                ("last_result", models.CharField(blank=True, max_length=20)),
                ("consecutive_correct", models.IntegerField(default=0)),
                ("review_count", models.IntegerField(default=0)),
                ("interval_days", models.IntegerField(default=0)),
                ("next_review_at", models.DateTimeField(blank=True, null=True)),
                ("last_reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("flashcard", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_states", to="courses.flashcard")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="flashcard_states", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["next_review_at", "id"],
                "unique_together": {("user", "flashcard")},
            },
        ),
    ]
