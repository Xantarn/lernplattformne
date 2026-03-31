from django.db import models
from courses.models import Course, Lesson, Topic

class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
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
    ]
    
    DIFFICULTY_CHOICES = [
        ("easy", "Einfach (10 XP)"),
        ("medium", "Mittel (25 XP)"),
        ("hard", "Schwer (50 XP)"),
    ]

    CODE_LANGUAGE_CHOICES = [
        ("python", "Python"),
        ("cpp", "C++"),
    ]

    CODE_VALIDATION_MODE_CHOICES = [
        ("syntax", "Nur Syntax/Compiler"),
        ("output", "Ausgabe prüfen"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="questions")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES, default="mc_single")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="medium")
    common_mistakes = models.TextField(blank=True, help_text="Häufige Fehler (durch Komma getrennt)")

    answer_a = models.CharField(max_length=200, blank=True)
    answer_b = models.CharField(max_length=200, blank=True)
    answer_c = models.CharField(max_length=200, blank=True)
    answer_d = models.CharField(max_length=200, blank=True)

    correct_answer = models.CharField(max_length=200, blank=True)
    review_note = models.TextField(blank=True)

    # Flexible fields for additional question types.
    options_json = models.JSONField(default=list, blank=True)
    correct_answers_json = models.JSONField(default=list, blank=True)
    matching_pairs_json = models.JSONField(default=list, blank=True)
    order_items_json = models.JSONField(default=list, blank=True)
    blanks_json = models.JSONField(default=list, blank=True)
    prompt_image = models.ImageField(upload_to="quiz/question_images/", blank=True, null=True)
    code_snippet = models.TextField(blank=True)
    code_language = models.CharField(max_length=20, choices=CODE_LANGUAGE_CHOICES, default="python")
    code_validation_mode = models.CharField(max_length=20, choices=CODE_VALIDATION_MODE_CHOICES, default="syntax")
    code_starter = models.TextField(blank=True, help_text="Starter-Code für den Lernenden")
    code_test_input = models.TextField(blank=True, help_text="Eingabe für Ausgabetest (stdin)")
    code_expected_output = models.TextField(blank=True, help_text="Erwartete Ausgabe für Ausgabetest")
    scenario_text = models.TextField(blank=True)

    def __str__(self):
        return self.question_text
    
    def get_xp_value(self):
        """Gibt die XP-Wert basierend auf Schwierigkeit zurück"""
        xp_map = {"easy": 10, "medium": 25, "hard": 50}
        return xp_map.get(self.difficulty, 25)