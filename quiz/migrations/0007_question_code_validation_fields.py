from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0006_question_difficulty_mistakes"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="code_expected_output",
            field=models.TextField(blank=True, help_text="Erwartete Ausgabe für Ausgabetest"),
        ),
        migrations.AddField(
            model_name="question",
            name="code_language",
            field=models.CharField(
                choices=[("python", "Python"), ("cpp", "C++")],
                default="python",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="code_starter",
            field=models.TextField(blank=True, help_text="Starter-Code für den Lernenden"),
        ),
        migrations.AddField(
            model_name="question",
            name="code_test_input",
            field=models.TextField(blank=True, help_text="Eingabe für Ausgabetest (stdin)"),
        ),
        migrations.AddField(
            model_name="question",
            name="code_validation_mode",
            field=models.CharField(
                choices=[("syntax", "Nur Syntax/Compiler"), ("output", "Ausgabe prüfen")],
                default="syntax",
                max_length=20,
            ),
        ),
    ]
