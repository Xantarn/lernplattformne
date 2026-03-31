from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0008_topicviewstate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TopicFavorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "topic",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to="courses.topic"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topic_favorites", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at", "id"],
                "unique_together": {("user", "topic")},
            },
        ),
    ]
