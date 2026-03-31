from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_flashcarduserstate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TopicViewState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_viewed_at", models.DateTimeField(auto_now=True)),
                ("visit_count", models.IntegerField(default=0)),
                (
                    "topic",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="view_states", to="courses.topic"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topic_view_states", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-last_viewed_at", "id"],
                "unique_together": {("user", "topic")},
            },
        ),
    ]
