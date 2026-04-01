from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from django.utils.safestring import mark_safe
from .models import Question


User = get_user_model()
AUTHORIZED_USER_ADMIN_USERNAME = "StasDj"


class RestrictedUserAdmin(UserAdmin):
	"""Only one specific username can see/manage Users in Django admin."""

	def _is_allowed(self, request):
		return bool(request.user.is_authenticated and request.user.username == AUTHORIZED_USER_ADMIN_USERNAME)

	def has_module_permission(self, request):
		if not self._is_allowed(request):
			return False
		return super().has_module_permission(request)

	def has_view_permission(self, request, obj=None):
		if not self._is_allowed(request):
			return False
		return super().has_view_permission(request, obj)

	def has_add_permission(self, request):
		if not self._is_allowed(request):
			return False
		return super().has_add_permission(request)

	def has_change_permission(self, request, obj=None):
		if not self._is_allowed(request):
			return False
		return super().has_change_permission(request, obj)

	def has_delete_permission(self, request, obj=None):
		if not self._is_allowed(request):
			return False
		return super().has_delete_permission(request, obj)


try:
	admin.site.unregister(User)
except NotRegistered:
	pass

admin.site.register(User, RestrictedUserAdmin)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
	list_display = ("id", "course", "lesson", "topic", "question_type", "difficulty", "question_text", "correct_answer")
	list_filter = ("course", "lesson", "topic", "question_type", "difficulty")
	search_fields = ("question_text", "review_note")
	readonly_fields = ("json_examples",)
	fieldsets = (
		("Basis", {
			"fields": ("course", "lesson", "topic", "question_type", "difficulty", "question_text", "review_note"),
		}),
		("Feedback & Häufige Fehler", {
			"fields": ("common_mistakes",),
			"description": "Häufige Fehler die Schüler machen (durch Komma getrennt)",
		}),
		("Beispiele (Copy/Paste)", {
			"fields": ("json_examples",),
			"description": "Nutze diese Beispiele direkt fuer die JSON-Felder.",
		}),
		("Klassische Antworten (Legacy MC)", {
			"fields": ("answer_a", "answer_b", "answer_c", "answer_d", "correct_answer"),
			"description": "Wird weiterhin fuer Multiple Choice (eine Antwort) verwendet.",
		}),
		("Flexible Antworten", {
			"fields": (
				"options_json",
				"correct_answers_json",
				"matching_pairs_json",
				"order_items_json",
				"blanks_json",
			),
			"description": "JSON-Felder fuer neue Fragetypen.",
		}),
		("Kontext", {
			"fields": (
				"prompt_image",
				"code_snippet",
				"code_language",
				"code_validation_mode",
				"code_starter",
				"code_test_input",
				"code_expected_output",
				"scenario_text",
			),
		}),
	)

	def json_examples(self, obj):
		return mark_safe(
			"""
			<pre style='white-space: pre-wrap; line-height:1.35;'>
mc_single (eine richtige):
options_json = ["Antwort A", "Antwort B", "Antwort C", "Antwort D"]
correct_answers_json = ["1"]

true_false:
correct_answers_json = ["TRUE"]

multi_select (mehrere richtige):
options_json = ["Python", "HTML", "Django", "Kaffee"]
correct_answers_json = ["0", "2"]

short_text:
correct_answers_json = ["polymorphie", "polymorphism"]

matching:
matching_pairs_json = [
  {{"left": "HTTP", "right": "Protokoll"}},
  {{"left": "SQL", "right": "Datenbanksprache"}}
]

ordering:
order_items_json = ["Planen", "Implementieren", "Testen", "Deployen"]

cloze:
blanks_json = ["Django", "Model", "View"]

image_single:
prompt_image = (Bild hochladen)
options_json = ["Katze", "Hund", "Vogel"]
correct_answers_json = ["1"]

code_single:
code_snippet = "Schreibe ein Programm ..."
code_language = "python" oder "cpp"
code_validation_mode = "syntax" oder "output"
code_starter = "print()"
code_test_input = "2\n"
code_expected_output = "4"

scenario_single:
scenario_text = "Ein Kunde meldet einen 500-Fehler..."
options_json = ["Server neustarten", "Logs prüfen", "Ignorieren"]
correct_answers_json = ["1"]

self_assessment:
correct_answers_json = ["4", "5"]
(zusätzlich muss der Nutzer eine Begründung schreiben)
			</pre>
			"""
		)

	json_examples.short_description = "JSON Schnellhilfe"

	class Media:
		js = ("admin/question_admin.js",)