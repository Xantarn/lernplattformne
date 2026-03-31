from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0003_alter_question_course"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="review_note",
            field=models.TextField(blank=True),
        ),
    ]
