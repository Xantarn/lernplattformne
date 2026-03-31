import json

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from exams.models import Result

from .models import Category, Course, Flashcard, FlashcardOption, FlashcardUserState


def describe_next_review(state, now=None):
    if not state or not state.next_review_at:
        return "Neu"

    now = now or timezone.now()
    if state.next_review_at <= now:
        return "Jetzt fällig"

    delta = state.next_review_at - now
    hours = int(delta.total_seconds() // 3600)
    days = delta.days

    if hours < 24:
        return f"In {max(1, hours)} Std."
    return f"In {max(1, days)} Tagen"


def apply_spaced_repetition_result(state, was_known):
    now = timezone.now()
    state.last_reviewed_at = now
    state.review_count += 1
    state.last_result = "known" if was_known else "unknown"

    if was_known:
        state.consecutive_correct += 1
        if state.consecutive_correct == 1:
            state.interval_days = 1
        elif state.consecutive_correct == 2:
            state.interval_days = 3
        elif state.consecutive_correct == 3:
            state.interval_days = 7
        else:
            current_interval = state.interval_days or 7
            state.interval_days = min(45, current_interval * 2)
        state.next_review_at = now + timezone.timedelta(days=state.interval_days)
    else:
        state.consecutive_correct = 0
        state.interval_days = 0
        state.next_review_at = now

    state.save()


def build_flashcard_payload(flashcard, state, now):
    return {
        "id": flashcard.id,
        "front": flashcard.front,
        "back": flashcard.back,
        "has_mc": flashcard.has_multiple_choice,
        "is_favorite": bool(state and state.is_favorite),
        "next_review_label": describe_next_review(state, now),
        "options": [
            {
                "text": option.text,
                "is_correct": option.is_correct,
            }
            for option in flashcard.options.all()
        ],
    }


def get_sidebar_context(request):
    """Kontext für Sidebar-Navigation"""
    categories = Category.objects.prefetch_related("courses__lessons__topics", "courses__questions").all()
    uncategorized_courses = Course.objects.filter(category__isnull=True).prefetch_related("lessons__topics", "questions")

    best_scores = {}
    if request.user.is_authenticated:
        # Get the latest result for each course (ordered by date, newest first)
        last_scores = {}
        for result in Result.objects.filter(user=request.user).order_by('-date'):
            # For each course, keep only the first (newest) result
            if result.course_id not in last_scores:
                last_scores[result.course_id] = result.score
        best_scores = last_scores

    def course_is_completed(course, best_scores):
        if course.id not in best_scores:
            return False
        total_questions = course.questions.count()
        if total_questions == 0:
            return False
        return best_scores[course.id] == total_questions

    def get_course_progress(course, best_scores):
        if course.id not in best_scores:
            return 0
        total_questions = course.questions.count()
        if total_questions == 0:
            return 0
        return int((best_scores[course.id] / total_questions) * 100)

    for category in categories:
        category_courses = list(category.courses.all())
        category.total_courses = len(category_courses)
        category.completed_courses = sum(
            1 for course in category_courses if course_is_completed(course, best_scores)
        )
        
        # Add progress to each course
        for course in category_courses:
            course.progress = get_course_progress(course, best_scores)
        
        # Calculate category progress as average of all courses
        if category_courses:
            category.progress = int(sum(course.progress for course in category_courses) / len(category_courses))
        else:
            category.progress = 0

    uncategorized_courses_list = list(uncategorized_courses)
    uncategorized_total_courses = len(uncategorized_courses_list)
    uncategorized_completed_courses = sum(
        1 for course in uncategorized_courses_list if course_is_completed(course, best_scores)
    )
    
    # Add progress to each uncategorized course
    for course in uncategorized_courses_list:
        course.progress = get_course_progress(course, best_scores)
    
    # Calculate uncategorized progress as average of all courses
    if uncategorized_courses_list:
        uncategorized_progress = int(sum(course.progress for course in uncategorized_courses_list) / len(uncategorized_courses_list))
    else:
        uncategorized_progress = 0

    return {
        "categories": categories,
        "uncategorized_courses": uncategorized_courses,
        "uncategorized_progress": uncategorized_progress,
        "uncategorized_completed_courses": uncategorized_completed_courses,
        "uncategorized_total_courses": uncategorized_total_courses,
    }


@login_required
def flashcard_view(request, course_id):
    """Zeige Karteikarten für einen Kurs"""
    course = get_object_or_404(Course, id=course_id)
    now = timezone.now()
    selected_filter = request.GET.get("filter", "all")
    all_flashcards = list(
        Flashcard.objects.filter(course=course, created_by=request.user).prefetch_related("options")
    )
    user_states = {}

    if request.user.is_authenticated:
        user_states = {
            state.flashcard_id: state
            for state in FlashcardUserState.objects.filter(
                user=request.user,
                flashcard__course=course,
            )
        }

    favorites_count = 0
    due_count = 0
    new_count = 0
    filtered_flashcards = []

    for flashcard in all_flashcards:
        state = user_states.get(flashcard.id)
        flashcard.user_state = state
        flashcard.is_favorite = bool(state and state.is_favorite)
        flashcard.is_new = not state or state.review_count == 0
        flashcard.is_due = flashcard.is_new or not state or not state.next_review_at or state.next_review_at <= now
        flashcard.next_review_label = describe_next_review(state, now)

        if flashcard.is_favorite:
            favorites_count += 1
        if flashcard.is_due:
            due_count += 1
        if flashcard.is_new:
            new_count += 1

        include_card = True
        if selected_filter == "favorites":
            include_card = flashcard.is_favorite
        elif selected_filter == "due":
            include_card = flashcard.is_due
        elif selected_filter == "new":
            include_card = flashcard.is_new

        if include_card:
            filtered_flashcards.append(flashcard)

    flashcards_payload = [build_flashcard_payload(flashcard, user_states.get(flashcard.id), now) for flashcard in filtered_flashcards]
    
    context = {
        "course": course,
        "flashcards": filtered_flashcards,
        "all_flashcards_count": len(all_flashcards),
        "selected_filter": selected_filter,
        "favorites_count": favorites_count,
        "due_count": due_count,
        "new_count": new_count,
        "flashcards_payload": flashcards_payload,
        **get_sidebar_context(request),
    }
    
    return render(request, "flashcards.html", context)

@login_required
def create_flashcard(request, course_id):
    """Erstelle eine neue Karteikarte"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == "POST":
        front = request.POST.get("front", "").strip()
        back = request.POST.get("back", "").strip()

        if not front or not back:
            context = {
                "course": course,
                "form_error": "Bitte Frage und Antwort ausfüllen.",
                **get_sidebar_context(request),
            }
            return render(request, "create_flashcard.html", context)

        flashcard = Flashcard.objects.create(
            created_by=request.user,
            course=course,
            front=front,
            back=back,
        )

        options = [option.strip() for option in request.POST.getlist("options") if option.strip()]
        correct_index = int(request.POST.get("correct_option", 0) or 0)
        for idx, option_text in enumerate(options):
            FlashcardOption.objects.create(
                flashcard=flashcard,
                text=option_text,
                is_correct=idx == correct_index,
                order=idx
            )

        return redirect("flashcards", course_id=course.id)
    
    context = {
        "course": course,
        "flashcard_options": [],
        **get_sidebar_context(request),
    }
    return render(request, "create_flashcard.html", context)


@login_required
def edit_flashcard(request, flashcard_id):
    """Bearbeite eine Karteikarte"""
    flashcard = get_object_or_404(Flashcard, id=flashcard_id, created_by=request.user)
    
    if request.method == "POST":
        front = request.POST.get("front", "").strip()
        back = request.POST.get("back", "").strip()

        if not front or not back:
            context = {
                "course": flashcard.course,
                "flashcard": flashcard,
                "form_error": "Bitte Frage und Antwort ausfüllen.",
                **get_sidebar_context(request),
            }
            return render(request, "create_flashcard.html", context)

        flashcard.front = front
        flashcard.back = back
        flashcard.save()

        flashcard.options.all().delete()
        options = [option.strip() for option in request.POST.getlist("options") if option.strip()]
        correct_index = int(request.POST.get("correct_option", 0) or 0)
        for idx, option_text in enumerate(options):
            FlashcardOption.objects.create(
                flashcard=flashcard,
                text=option_text,
                is_correct=idx == correct_index,
                order=idx
            )

        return redirect("flashcards", course_id=flashcard.course.id)
    
    context = {
        "course": flashcard.course,
        "flashcard": flashcard,
        "flashcard_options": [
            {
                "text": option.text,
                "is_correct": option.is_correct,
            }
            for option in flashcard.options.all()
        ],
        **get_sidebar_context(request),
    }
    return render(request, "create_flashcard.html", context)


@login_required
def delete_flashcard(request, flashcard_id):
    """Lösche eine Karteikarte"""
    flashcard = get_object_or_404(Flashcard, id=flashcard_id, created_by=request.user)
    course_id = flashcard.course.id
    
    if request.method == "POST":
        flashcard.delete()
        return redirect("flashcards", course_id=course_id)
    
    context = {
        "flashcard": flashcard,
    }
    return render(request, "confirm_delete.html", context)


@login_required
@require_POST
def toggle_flashcard_favorite(request, flashcard_id):
    flashcard = get_object_or_404(Flashcard, id=flashcard_id, created_by=request.user)
    state, _created = FlashcardUserState.objects.get_or_create(user=request.user, flashcard=flashcard)
    state.is_favorite = not state.is_favorite
    state.save(update_fields=["is_favorite", "updated_at"])

    return JsonResponse({
        "success": True,
        "is_favorite": state.is_favorite,
    })


@login_required
@require_POST
def record_flashcard_review(request, flashcard_id):
    flashcard = get_object_or_404(Flashcard, id=flashcard_id, created_by=request.user)
    payload = json.loads(request.body or "{}")
    was_known = bool(payload.get("known"))

    state, _created = FlashcardUserState.objects.get_or_create(user=request.user, flashcard=flashcard)
    apply_spaced_repetition_result(state, was_known)

    return JsonResponse({
        "success": True,
        "next_review_label": describe_next_review(state),
        "is_favorite": state.is_favorite,
        "last_result": state.last_result,
    })

