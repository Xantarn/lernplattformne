import io
import os

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import path, reverse
from django_ckeditor_5.widgets import CKEditor5Widget
from django.conf import settings
from .models import Category, Course, Lesson, Topic, Flashcard, FlashcardOption, FlashcardUserState


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name",)
	search_fields = ("name",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	list_display = ("title", "category")
	list_filter = ("category",)
	search_fields = ("title",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
	list_display = ("title", "course", "order")
	list_filter = ("course",)


class TopicAdminForm(forms.ModelForm):
	class Meta:
		model = Topic
		fields = "__all__"
		widgets = {
			"learning_material": CKEditor5Widget(config_name="default"),
		}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
	form = TopicAdminForm
	list_display = ("title", "lesson", "order")
	list_filter = ("lesson",)
	search_fields = ("title",)

	def get_form(self, request, obj=None, change=False, **kwargs):
		form = super().get_form(request, obj=obj, change=change, **kwargs)
		ocr_url = reverse("admin:courses_topic_ocr_pdf")
		widget = form.base_fields["learning_material"].widget
		widget.attrs["data-ocr-url"] = ocr_url
		return form

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"ocr-pdf/",
				self.admin_site.admin_view(self.ocr_pdf_view),
				name="courses_topic_ocr_pdf",
			),
		]
		return custom_urls + urls

	def ocr_pdf_view(self, request):
		if request.method != "POST":
			return JsonResponse({"error": "Nur POST erlaubt."}, status=405)

		if not self.has_add_permission(request) and not self.has_change_permission(request):
			raise PermissionDenied

		pdf_file = request.FILES.get("pdf_file")
		if not pdf_file:
			return JsonResponse({"error": "Keine PDF-Datei erhalten."}, status=400)

		if not pdf_file.name.lower().endswith(".pdf"):
			return JsonResponse({"error": "Bitte eine PDF-Datei hochladen."}, status=400)

		max_mb = int(getattr(settings, "TOPIC_OCR_MAX_FILE_MB", 20))
		if pdf_file.size > max_mb * 1024 * 1024:
			return JsonResponse({"error": f"Datei ist zu gross (max. {max_mb} MB)."}, status=400)

		try:
			text, used_ocr = extract_text_from_pdf_bytes(pdf_file.read())
		except RuntimeError as exc:
			return JsonResponse({"error": str(exc)}, status=400)
		except Exception:
			return JsonResponse({"error": "PDF konnte nicht verarbeitet werden."}, status=500)

		if not text.strip():
			return JsonResponse({"error": "Kein lesbarer Text in der PDF gefunden."}, status=400)

		max_chars = int(getattr(settings, "TOPIC_OCR_MAX_TEXT_CHARS", 120000))
		truncated = False
		if len(text) > max_chars:
			text = text[:max_chars]
			truncated = True

		return JsonResponse(
			{
				"text": text,
				"used_ocr": used_ocr,
				"truncated": truncated,
			}
		)

	class Media:
		css = {
			"all": ("admin/topic_layout_palette.css",),
		}
		js = ("admin/ckeditor_topic_layouts.js",)


def extract_text_from_pdf_bytes(pdf_bytes):
	"""Extract text from PDF; try native extraction first, then OCR fallback."""
	import sys
	max_pages = int(getattr(settings, "TOPIC_OCR_MAX_PAGES", 40))
	text_chunks = []

	# Step 1: Try native text extraction (text-based PDFs).
	try:
		from pypdf import PdfReader
		reader = PdfReader(io.BytesIO(pdf_bytes))
		for page in reader.pages[:max_pages]:
			page_text = (page.extract_text() or "").strip()
			if page_text:
				text_chunks.append(page_text)
		if text_chunks:
			return "\n\n".join(text_chunks), False
	except Exception:
		pass

	# Step 2: OCR fallback for scanned PDFs.
	try:
		from pdf2image import convert_from_bytes
	except ImportError as exc:
		raise RuntimeError(
			f"pdf2image nicht verfuegbar (Python: {sys.executable}). Fehler: {exc}"
		) from exc

	try:
		import pytesseract
	except ImportError as exc:
		raise RuntimeError(
			f"pytesseract nicht verfuegbar (Python: {sys.executable}). Fehler: {exc}"
		) from exc

	# Configure Tesseract binary and tessdata.
	tesseract_cmd = getattr(settings, "TOPIC_OCR_TESSERACT_CMD", "").strip()
	if tesseract_cmd:
		pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

	tessdata_dir = getattr(settings, "TOPIC_OCR_TESSDATA_DIR", "").strip()
	if tessdata_dir:
		os.environ["TESSDATA_PREFIX"] = tessdata_dir
	tesseract_config = ""

	poppler_path = getattr(settings, "TOPIC_OCR_POPPLER_PATH", "").strip() or None

	try:
		images = convert_from_bytes(
			pdf_bytes,
			dpi=int(getattr(settings, "TOPIC_OCR_DPI", 300)),
			fmt="png",
			poppler_path=poppler_path,
		)
	except Exception as exc:
		raise RuntimeError(
			f"PDF konnte nicht in Bilder umgewandelt werden: {exc}"
		) from exc

	# Pick available language(s).
	lang = getattr(settings, "TOPIC_OCR_LANG", "deu+eng")
	try:
		available_langs = pytesseract.get_languages(config=tesseract_config)
		requested = [l for l in lang.split("+") if l]
		lang = "+".join(l for l in requested if l in available_langs) or available_langs[0]
	except Exception:
		lang = "eng"

	for image in images[:max_pages]:
		page_text = (pytesseract.image_to_string(image, lang=lang, config=tesseract_config) or "").strip()
		if page_text:
			text_chunks.append(page_text)

	return "\n\n".join(text_chunks), True


class FlashcardOptionInline(admin.TabularInline):
	"""Inline-Edit für Multiple-Choice-Optionen"""
	model = FlashcardOption
	extra = 2
	fields = ("text", "is_correct", "order")
	ordering = ("order", "id")


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
	list_display = ("course", "created_by", "front", "has_mc_indicator", "order")
	list_filter = ("course",)
	search_fields = ("front", "back")
	ordering = ("course", "order")
	inlines = [FlashcardOptionInline]
	
	def has_mc_indicator(self, obj):
		"""Zeige Symbol wenn Multiple-Choice vorhanden"""
		if obj.has_multiple_choice:
			return "✓ MC"
		return "-"
	has_mc_indicator.short_description = "Multiple-Choice"


@admin.register(FlashcardOption)
class FlashcardOptionAdmin(admin.ModelAdmin):
	list_display = ("flashcard", "text", "is_correct", "order")
	list_filter = ("flashcard__course", "is_correct")
	search_fields = ("text", "flashcard__front")
	ordering = ("flashcard", "order")


@admin.register(FlashcardUserState)
class FlashcardUserStateAdmin(admin.ModelAdmin):
	list_display = ("user", "flashcard", "is_favorite", "last_result", "interval_days", "next_review_at")
	list_filter = ("is_favorite", "last_result", "flashcard__course")
	search_fields = ("user__username", "flashcard__front")