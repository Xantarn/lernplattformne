from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0004_question_review_note"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="blanks_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="question",
            name="code_snippet",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="question",
            name="matching_pairs_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="question",
            name="options_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="question",
            name="order_items_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="question",
            name="prompt_image",
            field=models.ImageField(blank=True, null=True, upload_to="quiz/question_images/"),
        ),
        migrations.AddField(
            model_name="question",
            name="question_type",
            field=models.CharField(
                choices=[
                    ("mc_single", "Multiple Choice (eine Antwort)"),
                    ("true_false", "Wahr/Falsch"),
                    ("multi_select", "Mehrfachauswahl"),
                    ("short_text", "Freitext (kurze Antwort)"),
                    ("matching", "Zuordnen"),
                    ("ordering", "Reihenfolge"),
                    ("cloze", "Lueckentext"),
                    ("image_single", "Bildfrage"),
                    ("code_single", "Code-Frage"),
                    ("scenario_single", "Szenario-Frage"),
                    ("self_assessment", "Selbsteinschaetzung + Begruendung"),
                ],
                default="mc_single",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="scenario_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="question",
            name="correct_answers_json",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name="question",
            name="answer_a",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="question",
            name="answer_b",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="question",
            name="answer_c",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="question",
            name="answer_d",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="question",
            name="correct_answer",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
