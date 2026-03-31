import random
import shutil
import subprocess
import sys
import tempfile
import os
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from courses.models import Category, Course, FlashcardUserState, Lesson, Topic, TopicFavorite, TopicViewState
from exams.models import Result

from .models import Question
from exams.gamification import award_xp, calculate_quiz_xp, get_user_stats, get_leaderboard


def resolve_correct_key(question):
    correct_answer = (question.correct_answer or "").strip().upper()
    if correct_answer in {"A", "B", "C", "D"}:
        return correct_answer

    option_map = {
        "A": question.answer_a,
        "B": question.answer_b,
        "C": question.answer_c,
        "D": question.answer_d,
    }
    normalized_correct_text = (question.correct_answer or "").strip().lower()
    for key, text in option_map.items():
        if (text or "").strip().lower() == normalized_correct_text:
            return key
    return ""


def normalize_text(value):
    return " ".join((value or "").strip().lower().split())


def normalize_output(value):
    return "\n".join((value or "").replace("\r\n", "\n").strip().splitlines())


def get_code_setting(name, default):
    return getattr(settings, name, default)


def truncate_with_notice(value, max_chars):
    text = value or ""
    if max_chars <= 0:
        return "", bool(text)
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n...[Ausgabe gekuerzt]...", True


def run_guarded_subprocess(command, stdin_text="", timeout_seconds=3, cwd=None):
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "SystemRoot": os.environ.get("SystemRoot", ""),
        "WINDIR": os.environ.get("WINDIR", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
    }

    try:
        completed = subprocess.run(
            command,
            input=stdin_text or "",
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            cwd=cwd,
            env=safe_env,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "",
            "error": f"Zeitlimit ueberschritten ({timeout_seconds}s).",
            "stdout_truncated": False,
            "stderr_truncated": False,
        }

    max_stdout = int(get_code_setting("CODE_EXECUTION_MAX_STDOUT_CHARS", 6000))
    max_stderr = int(get_code_setting("CODE_EXECUTION_MAX_STDERR_CHARS", 6000))
    stdout_text, stdout_truncated = truncate_with_notice(completed.stdout or "", max_stdout)
    stderr_text, stderr_truncated = truncate_with_notice(completed.stderr or "", max_stderr)

    return {
        "ok": completed.returncode == 0,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "error": "" if completed.returncode == 0 else f"Ausfuehrung fehlgeschlagen (Exit-Code {completed.returncode}).",
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }


def validate_code_submission(question, source_code):
    if not bool(get_code_setting("CODE_EXECUTION_ENABLED", True)):
        return "Code-Aufgaben sind derzeit deaktiviert."

    source = source_code or ""
    max_source_chars = int(get_code_setting("CODE_EXECUTION_MAX_SOURCE_CHARS", 8000))
    if len(source) > max_source_chars:
        return f"Code zu lang (max {max_source_chars} Zeichen)."

    max_stdin_chars = int(get_code_setting("CODE_EXECUTION_MAX_STDIN_CHARS", 4000))
    if len(question.code_test_input or "") > max_stdin_chars:
        return f"Test-Eingabe zu lang (max {max_stdin_chars} Zeichen)."

    max_expected_chars = int(get_code_setting("CODE_EXECUTION_MAX_EXPECTED_OUTPUT_CHARS", 6000))
    if len(question.code_expected_output or "") > max_expected_chars:
        return f"Erwartete Ausgabe zu lang (max {max_expected_chars} Zeichen)."

    blocked_patterns = get_code_setting("CODE_EXECUTION_BLOCKED_PATTERNS", {})
    language = "cpp" if question.code_language == "cpp" else "python"
    source_lc = source.lower()
    for pattern in blocked_patterns.get(language, []):
        if pattern.lower() in source_lc:
            return f"Unsicheres Muster erkannt: {pattern}"

    return ""


def run_python_submission(source_code, stdin_text="", syntax_only=False):
    if syntax_only:
        try:
            compile(source_code, "<user_code>", "exec")
            return {"ok": True, "stdout": "", "stderr": "", "error": ""}
        except SyntaxError as exc:
            return {"ok": False, "stdout": "", "stderr": "", "error": f"SyntaxError: {exc}"}

    timeout_seconds = int(get_code_setting("CODE_EXECUTION_PYTHON_TIMEOUT_SECONDS", 3))
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "submission.py")
        with open(script_path, "w", encoding="utf-8") as handle:
            handle.write(source_code)

        # -I isolates from user site/customization, -S skips site import.
        command = [sys.executable, "-I", "-B", "-S", script_path]
        return run_guarded_subprocess(command, stdin_text=stdin_text, timeout_seconds=timeout_seconds, cwd=tmpdir)


def run_cpp_submission(source_code, stdin_text="", syntax_only=False):
    compiler = shutil.which("g++")
    if not compiler:
        return {"ok": False, "stdout": "", "stderr": "", "error": "Kein C++ Compiler (g++) gefunden."}

    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = f"{tmpdir}\\main.cpp"
        exe_path = f"{tmpdir}\\main.exe"
        with open(source_path, "w", encoding="utf-8") as handle:
            handle.write(source_code)

        compile_cmd = [compiler, source_path, "-std=c++17", "-O2", "-o", exe_path]
        if syntax_only:
            compile_cmd = [compiler, "-fsyntax-only", source_path, "-std=c++17"]

        compile_timeout = int(get_code_setting("CODE_EXECUTION_CPP_COMPILE_TIMEOUT_SECONDS", 8))
        compile_result = run_guarded_subprocess(compile_cmd, timeout_seconds=compile_timeout, cwd=tmpdir)
        if not compile_result["ok"] and "Zeitlimit" in (compile_result["error"] or ""):
            compile_result["error"] = f"Compiler-Timeout ({compile_timeout}s)."

        if not compile_result["ok"]:
            return {
                "ok": False,
                "stdout": compile_result.get("stdout") or "",
                "stderr": compile_result.get("stderr") or "",
                "error": "Compilerfehler.",
                "stdout_truncated": compile_result.get("stdout_truncated", False),
                "stderr_truncated": compile_result.get("stderr_truncated", False),
            }

        if syntax_only:
            return {"ok": True, "stdout": "", "stderr": "", "error": ""}

        run_timeout = int(get_code_setting("CODE_EXECUTION_CPP_RUN_TIMEOUT_SECONDS", 3))
        run_result = run_guarded_subprocess([exe_path], stdin_text=stdin_text, timeout_seconds=run_timeout, cwd=tmpdir)
        if not run_result["ok"] and "Zeitlimit" in (run_result["error"] or ""):
            run_result["error"] = f"Zeitlimit ueberschritten ({run_timeout}s)."
        return run_result


def evaluate_code_answer(question, source_code):
    if not (source_code or "").strip():
        return {
            "is_correct": False,
            "feedback_lines": [{
                "label": "Code",
                "value": "Kein Code eingegeben.",
                "is_correct": False,
            }],
        }

    validation_error = validate_code_submission(question, source_code)
    if validation_error:
        return {
            "is_correct": False,
            "feedback_lines": [{
                "label": "Sicherheits-Check",
                "value": validation_error,
                "is_correct": False,
            }],
        }

    runner = run_cpp_submission if question.code_language == "cpp" else run_python_submission
    if question.code_validation_mode == "syntax":
        result = runner(source_code, syntax_only=True)
        return {
            "is_correct": result["ok"],
            "feedback_lines": [{
                "label": "Syntax-Check",
                "value": "OK" if result["ok"] else (result["error"] or result["stderr"] or "Fehler"),
                "is_correct": result["ok"],
            }],
        }

    result = runner(source_code, stdin_text=question.code_test_input or "", syntax_only=False)
    expected = normalize_output(question.code_expected_output or "")
    actual = normalize_output(result["stdout"])
    is_correct = result["ok"] and actual == expected

    feedback = []
    if result["error"]:
        feedback.append({
            "label": "Ausführung",
            "value": result["error"],
            "is_correct": False,
        })
    if result["stderr"]:
        feedback.append({
            "label": "STDERR",
            "value": normalize_output(result["stderr"]),
            "is_correct": False,
        })

    feedback.append({
        "label": "Erwartete Ausgabe",
        "value": expected or "[leer]",
        "is_correct": True,
    })
    feedback.append({
        "label": "Deine Ausgabe",
        "value": actual or "[leer]",
        "is_correct": is_correct,
    })

    if result.get("stdout_truncated") or result.get("stderr_truncated"):
        feedback.append({
            "label": "Hinweis",
            "value": "Ausgabe wurde aus Sicherheitsgruenden gekuerzt.",
            "is_correct": True,
        })

    return {
        "is_correct": is_correct,
        "feedback_lines": feedback,
    }


def get_common_mistakes_feedback(question):
    """Hole häufige Fehler für eine Frage"""
    if not question.common_mistakes:
        return []
    
    mistakes = [m.strip() for m in question.common_mistakes.split(",")]
    return mistakes


def get_matching_pairs(question):
    pairs = []
    for item in question.matching_pairs_json or []:
        if isinstance(item, dict):
            left = (item.get("left") or "").strip()
            right = (item.get("right") or "").strip()
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            left = str(item[0]).strip()
            right = str(item[1]).strip()
        else:
            continue
        if left and right:
            pairs.append({"left": left, "right": right})
    return pairs


def get_order_items(question):
    items = [str(item).strip() for item in (question.order_items_json or []) if str(item).strip()]
    if items:
        return items
    return [str(item).strip() for item in (question.options_json or []) if str(item).strip()]


def get_blanks(question):
    return [str(item).strip() for item in (question.blanks_json or []) if str(item).strip()]


def get_single_options(question):
    qtype = question.question_type
    if qtype == "true_false":
        return [("TRUE", "Wahr"), ("FALSE", "Falsch")]

    if question.options_json:
        return [(str(index), str(text)) for index, text in enumerate(question.options_json)]

    options = []
    if question.answer_a:
        options.append(("A", question.answer_a))
    if question.answer_b:
        options.append(("B", question.answer_b))
    if question.answer_c:
        options.append(("C", question.answer_c))
    if question.answer_d:
        options.append(("D", question.answer_d))
    return options


def get_correct_single_key(question, options):
    if question.question_type == "true_false":
        if question.correct_answers_json:
            return str(question.correct_answers_json[0]).strip().upper()
        value = (question.correct_answer or "").strip().upper()
        if value in {"TRUE", "FALSE"}:
            return value
        if value == "A":
            return "TRUE"
        if value == "B":
            return "FALSE"
        return ""

    if question.correct_answers_json:
        return str(question.correct_answers_json[0]).strip()

    legacy = resolve_correct_key(question)
    if legacy:
        return legacy

    # Fallback by matching free text against available options.
    normalized = normalize_text(question.correct_answer)
    for key, text in options:
        if normalize_text(text) == normalized:
            return key
    return ""


def parse_answer_from_request(request, question):
    qid = str(question.id)
    qtype = question.question_type

    if qtype == "code_single":
        return {"code": (request.POST.get(f"q_{qid}_code") or "").rstrip()}

    if qtype in {"mc_single", "true_false", "image_single", "scenario_single"}:
        return {"selected": (request.POST.get(f"q_{qid}_single") or "").strip()}

    if qtype == "multi_select":
        selected = [value.strip() for value in request.POST.getlist(f"q_{qid}_multi") if value.strip()]
        return {"selected": selected}

    if qtype == "short_text":
        return {"text": (request.POST.get(f"q_{qid}_text") or "").strip()}

    if qtype == "matching":
        pairs = get_matching_pairs(question)
        selected = []
        for index, _pair in enumerate(pairs):
            selected.append((request.POST.get(f"q_{qid}_match_{index}") or "").strip())
        return {"selected": selected}

    if qtype == "ordering":
        items = get_order_items(question)
        ranks = []
        for index, _item in enumerate(items):
            ranks.append((request.POST.get(f"q_{qid}_order_{index}") or "").strip())
        return {"ranks": ranks}

    if qtype == "cloze":
        blanks = get_blanks(question)
        answers = []
        for index, _blank in enumerate(blanks):
            answers.append((request.POST.get(f"q_{qid}_blank_{index}") or "").strip())
        return {"answers": answers}

    if qtype == "self_assessment":
        return {
            "rating": (request.POST.get(f"q_{qid}_rating") or "").strip(),
            "reason": (request.POST.get(f"q_{qid}_reason") or "").strip(),
        }

    return {}


def evaluate_question(question, user_answer):
    qtype = question.question_type
    feedback_lines = []

    if qtype == "code_single":
        code_result = evaluate_code_answer(question, (user_answer or {}).get("code", ""))
        return {
            "is_correct": code_result["is_correct"],
            "option_items": [],
            "feedback_lines": code_result["feedback_lines"],
        }

    if qtype in {"mc_single", "true_false", "image_single", "scenario_single"}:
        options = get_single_options(question)
        correct_key = get_correct_single_key(question, options)
        selected = (user_answer or {}).get("selected", "")
        
        is_correct = selected == correct_key

        option_items = []
        for key, text in options:
            is_selected = selected == key
            is_correct_option = correct_key == key
            option_items.append({
                "key": key,
                "text": text,
                "is_selected": is_selected,
                "is_correct": is_correct_option,
                "is_wrong_selected": is_selected and not is_correct_option,
            })
        
        # Besseres Feedback: Häufige Fehler wenn falsch
        if not is_correct:
            mistakes = get_common_mistakes_feedback(question)
            if mistakes:
                feedback_lines.append({
                    "label": "⚠️ Häufige Fehler",
                    "value": " • ".join(mistakes),
                    "is_correct": False,
                })
            
            if question.review_note:
                feedback_lines.append({
                    "label": "💡 Erklärung",
                    "value": question.review_note,
                    "is_correct": False,
                })
        else:
            if question.review_note:
                feedback_lines.append({
                    "label": "✓ Erklärung",
                    "value": question.review_note,
                    "is_correct": True,
                })

        return {
            "is_correct": is_correct,
            "option_items": option_items,
            "feedback_lines": feedback_lines,
        }

    if qtype == "multi_select":
        options = get_single_options(question)
        selected_set = set((user_answer or {}).get("selected", []))
        correct_set = set(str(value).strip() for value in (question.correct_answers_json or []))

        option_items = []
        for key, text in options:
            is_selected = key in selected_set
            is_correct = key in correct_set
            option_items.append({
                "key": key,
                "text": text,
                "is_selected": is_selected,
                "is_correct": is_correct,
                "is_wrong_selected": is_selected and not is_correct,
            })

        return {
            "is_correct": selected_set == correct_set and len(correct_set) > 0,
            "option_items": option_items,
            "feedback_lines": feedback_lines,
        }

    if qtype == "short_text":
        user_text = normalize_text((user_answer or {}).get("text", ""))
        accepted = [normalize_text(value) for value in (question.correct_answers_json or []) if normalize_text(value)]
        if not accepted and question.correct_answer:
            accepted = [normalize_text(question.correct_answer)]

        is_correct = user_text in accepted if accepted else False
        feedback_lines.append({
            "label": "Deine Antwort",
            "value": (user_answer or {}).get("text", "-") or "-",
            "is_correct": is_correct,
        })
        if accepted:
            feedback_lines.append({
                "label": "Erwartet",
                "value": ", ".join(question.correct_answers_json or [question.correct_answer]),
                "is_correct": True,
            })

        return {"is_correct": is_correct, "option_items": [], "feedback_lines": feedback_lines}

    if qtype == "matching":
        pairs = get_matching_pairs(question)
        selected = (user_answer or {}).get("selected", [])
        is_correct = True
        for index, pair in enumerate(pairs):
            chosen = selected[index] if index < len(selected) else ""
            line_correct = normalize_text(chosen) == normalize_text(pair["right"])
            if not line_correct:
                is_correct = False
            feedback_lines.append({
                "label": pair["left"],
                "value": f"{chosen or '-'} (richtig: {pair['right']})",
                "is_correct": line_correct,
            })

        return {"is_correct": is_correct and len(pairs) > 0, "option_items": [], "feedback_lines": feedback_lines}

    if qtype == "ordering":
        items = get_order_items(question)
        ranks = (user_answer or {}).get("ranks", [])
        ranked = []
        for index, item in enumerate(items):
            rank_value = ranks[index] if index < len(ranks) else ""
            try:
                rank = int(rank_value)
            except (TypeError, ValueError):
                rank = 10_000 + index
            ranked.append((rank, item))

        user_order = [item for _rank, item in sorted(ranked, key=lambda entry: entry[0])]
        is_correct = user_order == items and len(items) > 0
        feedback_lines.append({
            "label": "Deine Reihenfolge",
            "value": " -> ".join(user_order) if user_order else "-",
            "is_correct": is_correct,
        })
        feedback_lines.append({
            "label": "Richtige Reihenfolge",
            "value": " -> ".join(items) if items else "-",
            "is_correct": True,
        })
        return {"is_correct": is_correct, "option_items": [], "feedback_lines": feedback_lines}

    if qtype == "cloze":
        expected = get_blanks(question)
        answers = (user_answer or {}).get("answers", [])
        is_correct = True
        for index, blank in enumerate(expected):
            given = answers[index] if index < len(answers) else ""
            line_correct = normalize_text(given) == normalize_text(blank)
            if not line_correct:
                is_correct = False
            feedback_lines.append({
                "label": f"Luecke {index + 1}",
                "value": f"{given or '-'} (richtig: {blank})",
                "is_correct": line_correct,
            })
        return {"is_correct": is_correct and len(expected) > 0, "option_items": [], "feedback_lines": feedback_lines}

    if qtype == "self_assessment":
        rating = (user_answer or {}).get("rating", "")
        reason = (user_answer or {}).get("reason", "")
        accepted = [str(value).strip() for value in (question.correct_answers_json or []) if str(value).strip()]
        if accepted:
            is_correct = rating in accepted and len(reason.strip()) > 0
            feedback_lines.append({
                "label": "Dein Rating",
                "value": f"{rating or '-'} (erwartet: {', '.join(accepted)})",
                "is_correct": rating in accepted,
            })
        else:
            is_correct = bool(rating and reason.strip())
            feedback_lines.append({
                "label": "Dein Rating",
                "value": rating or "-",
                "is_correct": bool(rating),
            })

        feedback_lines.append({
            "label": "Begruendung",
            "value": reason or "-",
            "is_correct": bool(reason.strip()),
        })
        return {"is_correct": is_correct, "option_items": [], "feedback_lines": feedback_lines}

    return {"is_correct": False, "option_items": [], "feedback_lines": []}


def course_is_completed(course, best_scores):
    total_questions = course.questions.count()
    best_score = best_scores.get(course.id)
    if total_questions <= 0 or best_score is None:
        return False
    return best_score >= total_questions


def get_course_progress(course, best_scores):
    """Calculate course progress based on best score vs total questions."""
    total_questions = course.questions.count()
    best_score = best_scores.get(course.id, 0)
    if total_questions <= 0:
        return 0
    return int((best_score / total_questions) * 100)


def get_lesson_progress(lesson, user):
    """Berechne Lesson-Fortschritt basierend auf beste Quiz-Score"""
    if not user.is_authenticated:
        return 0
    
    total_questions = lesson.questions.count()
    if total_questions <= 0:
        return 0
    
    # Hole beste Ergebnis für diese Lesson
    best_result = Result.objects.filter(user=user, lesson=lesson).order_by("-score").first()
    if not best_result:
        return 0
    
    return int((best_result.score / total_questions) * 100)


def get_topic_progress(topic, user):
    """Berechne Topic-Fortschritt basierend auf beste Quiz-Score"""
    if not user.is_authenticated:
        return 0
    
    total_questions = topic.questions.count()
    if total_questions <= 0:
        return 0
    
    # Hole beste Ergebnis für dieses Topic
    best_result = Result.objects.filter(user=user, topic=topic).order_by("-score").first()
    if not best_result:
        return 0
    
    return int((best_result.score / total_questions) * 100)


def get_sidebar_context(request):
    categories = Category.objects.prefetch_related("courses__lessons__topics", "courses__questions").all()
    uncategorized_courses = Course.objects.filter(category__isnull=True).prefetch_related("lessons__topics", "questions")
    favorite_topics = []
    favorited_topic_ids = set()

    best_scores = {}
    if request.user.is_authenticated:
        # Get the latest result for each course (ordered by date, newest first)
        last_scores = {}
        for result in Result.objects.filter(user=request.user).order_by('-date'):
            # For each course, keep only the first (newest) result
            if result.course_id not in last_scores:
                last_scores[result.course_id] = result.score
        best_scores = last_scores

        favorites = (
            TopicFavorite.objects.filter(user=request.user)
            .select_related("topic", "topic__lesson", "topic__lesson__course")
            .order_by("-created_at")
        )
        favorite_topics = list(favorites[:8])
        favorited_topic_ids = {item.topic_id for item in favorites}

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
        "favorite_topics": favorite_topics,
        "favorited_topic_ids": favorited_topic_ids,
    }


def quiz_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = list(Question.objects.filter(course=course))
    if not questions:
        return render(request, "quiz.html", {
            "question": None,
            "course": course,
            "current_number": 0,
            "total_questions": 0,
            "progress_percent": 0,
            **get_sidebar_context(request),
        })

    session_key = f"quiz_attempt_{course.id}"
    attempt = request.session.get(session_key)
    if not attempt:
        attempt = {
            "current_index": 0,
            "answers": {},
        }

    if request.method == "POST":
        current_index = int(attempt.get("current_index", 0))
        answers = attempt.get("answers", {})

        if current_index < len(questions):
            current_question = questions[current_index]
            answers[str(current_question.id)] = parse_answer_from_request(request, current_question)

        attempt["answers"] = answers
        attempt["current_index"] = current_index + 1
        request.session[session_key] = attempt
        request.session.modified = True

    current_index = int(attempt.get("current_index", 0))
    answers = attempt.get("answers", {})

    if current_index >= len(questions):
        score = 0
        review_items = []

        for question in questions:
            evaluation = evaluate_question(question, answers.get(str(question.id), {}))
            if evaluation["is_correct"]:
                score += 1

            review_items.append({
                "question": question,
                "option_items": evaluation["option_items"],
                "feedback_lines": evaluation["feedback_lines"],
                "is_correct": evaluation["is_correct"],
                "review_note": question.review_note,
            })

        if request.user.is_authenticated:
            # Berechne XP basierend auf Score und Schwierigkeit
            xp_earned = calculate_quiz_xp(score, len(questions), questions)
            
            result = Result.objects.create(
                user=request.user,
                course=course,
                score=score,
                total_questions=len(questions),
                xp_earned=xp_earned
            )
            
            # Vergebe XP an Benutzer
            award_xp(request.user, xp_earned)

        request.session.pop(session_key, None)
        request.session.modified = True

        wrong_items = [item for item in review_items if not item["is_correct"]]

        return render(request, "result.html", {
            "score": score,
            "total": len(questions),
            "wrong_items": wrong_items,
            **get_sidebar_context(request),
        })

    question = questions[current_index]
    qtype = question.question_type

    options = []
    if qtype in {"mc_single", "true_false", "image_single", "scenario_single", "multi_select"}:
        options = get_single_options(question)
        random.shuffle(options)

    matching_pairs = get_matching_pairs(question) if qtype == "matching" else []
    matching_right_items = [pair["right"] for pair in matching_pairs]
    if matching_right_items:
        random.shuffle(matching_right_items)

    ordering_items = get_order_items(question) if qtype == "ordering" else []
    ordering_items_shuffled = ordering_items[:]
    if ordering_items_shuffled:
        random.shuffle(ordering_items_shuffled)

    blanks = get_blanks(question) if qtype == "cloze" else []

    current_number = current_index + 1
    total_questions = len(questions)
    progress_percent = int((current_number / total_questions) * 100)

    return render(request, "quiz.html", {
        "question": question,
        "options": options,
        "matching_pairs": matching_pairs,
        "matching_right_items": matching_right_items,
        "ordering_items": ordering_items_shuffled,
        "blanks": blanks,
        "course": course,
        "current_number": current_number,
        "total_questions": total_questions,
        "progress_percent": progress_percent,
        **get_sidebar_context(request),
    })


def lesson_quiz_view(request, lesson_id):
    """Quiz-View für einzelne Lektionen"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Finde alle Fragen für diese Lektion
    questions = list(Question.objects.filter(lesson=lesson))
    if not questions:
        return render(request, "quiz.html", {
            "question": None,
            "lesson": lesson,
            "course": course,
            "current_number": 0,
            "total_questions": 0,
            "progress_percent": 0,
            **get_sidebar_context(request),
        })

    session_key = f"lesson_quiz_attempt_{lesson.id}"
    attempt = request.session.get(session_key)
    if not attempt:
        attempt = {
            "current_index": 0,
            "answers": {},
        }

    if request.method == "POST":
        current_index = int(attempt.get("current_index", 0))
        answers = attempt.get("answers", {})

        if current_index < len(questions):
            current_question = questions[current_index]
            answers[str(current_question.id)] = parse_answer_from_request(request, current_question)

        attempt["answers"] = answers
        attempt["current_index"] = current_index + 1
        request.session[session_key] = attempt
        request.session.modified = True

    current_index = int(attempt.get("current_index", 0))
    answers = attempt.get("answers", {})

    if current_index >= len(questions):
        score = 0
        review_items = []

        for question in questions:
            evaluation = evaluate_question(question, answers.get(str(question.id), {}))
            if evaluation["is_correct"]:
                score += 1

            review_items.append({
                "question": question,
                "option_items": evaluation["option_items"],
                "feedback_lines": evaluation["feedback_lines"],
                "is_correct": evaluation["is_correct"],
                "review_note": question.review_note,
            })

        if request.user.is_authenticated:
            # Berechne XP basierend auf Score und Schwierigkeit
            xp_earned = calculate_quiz_xp(score, len(questions), questions)
            
            result = Result.objects.create(
                user=request.user,
                course=course,
                lesson=lesson,
                score=score,
                total_questions=len(questions),
                xp_earned=xp_earned
            )
            
            # Vergebe XP an Benutzer
            award_xp(request.user, xp_earned)

        request.session.pop(session_key, None)
        request.session.modified = True

        wrong_items = [item for item in review_items if not item["is_correct"]]

        return render(request, "result.html", {
            "score": score,
            "total": len(questions),
            "wrong_items": wrong_items,
            "lesson": lesson,
            "course": course,
            **get_sidebar_context(request),
        })

    question = questions[current_index]
    qtype = question.question_type

    options = []
    if qtype in {"mc_single", "true_false", "image_single", "scenario_single", "multi_select"}:
        options = get_single_options(question)
        random.shuffle(options)

    matching_pairs = get_matching_pairs(question) if qtype == "matching" else []
    matching_right_items = [pair["right"] for pair in matching_pairs]
    if matching_right_items:
        random.shuffle(matching_right_items)

    ordering_items = get_order_items(question) if qtype == "ordering" else []
    ordering_items_shuffled = ordering_items[:]
    if ordering_items_shuffled:
        random.shuffle(ordering_items_shuffled)

    blanks = get_blanks(question) if qtype == "cloze" else []

    current_number = current_index + 1
    total_questions = len(questions)
    progress_percent = int((current_number / total_questions) * 100)

    return render(request, "quiz.html", {
        "question": question,
        "options": options,
        "matching_pairs": matching_pairs,
        "matching_right_items": matching_right_items,
        "ordering_items": ordering_items_shuffled,
        "blanks": blanks,
        "lesson": lesson,
        "course": course,
        "current_number": current_number,
        "total_questions": total_questions,
        "progress_percent": progress_percent,
        **get_sidebar_context(request),
    })


def topic_quiz_view(request, topic_id):
    """Quiz-View für einzelne Topics"""
    topic = get_object_or_404(Topic, id=topic_id)
    lesson = topic.lesson
    course = lesson.course
    
    # Finde alle Fragen für dieses Topic
    questions = list(Question.objects.filter(topic=topic))
    if not questions:
        return render(request, "quiz.html", {
            "question": None,
            "topic": topic,
            "lesson": lesson,
            "course": course,
            "current_number": 0,
            "total_questions": 0,
            "progress_percent": 0,
            **get_sidebar_context(request),
        })

    session_key = f"topic_quiz_attempt_{topic.id}"
    attempt = request.session.get(session_key)
    if not attempt:
        attempt = {
            "current_index": 0,
            "answers": {},
        }

    if request.method == "POST":
        current_index = int(attempt.get("current_index", 0))
        answers = attempt.get("answers", {})

        if current_index < len(questions):
            current_question = questions[current_index]
            answers[str(current_question.id)] = parse_answer_from_request(request, current_question)

        attempt["answers"] = answers
        attempt["current_index"] = current_index + 1
        request.session[session_key] = attempt
        request.session.modified = True

    current_index = int(attempt.get("current_index", 0))
    answers = attempt.get("answers", {})

    if current_index >= len(questions):
        score = 0
        review_items = []

        for question in questions:
            evaluation = evaluate_question(question, answers.get(str(question.id), {}))
            if evaluation["is_correct"]:
                score += 1

            review_items.append({
                "question": question,
                "option_items": evaluation["option_items"],
                "feedback_lines": evaluation["feedback_lines"],
                "is_correct": evaluation["is_correct"],
                "review_note": question.review_note,
            })

        if request.user.is_authenticated:
            # Berechne XP basierend auf Score und Schwierigkeit
            xp_earned = calculate_quiz_xp(score, len(questions), questions)
            
            result = Result.objects.create(
                user=request.user,
                course=course,
                lesson=lesson,
                topic=topic,
                score=score,
                total_questions=len(questions),
                xp_earned=xp_earned
            )
            
            # Vergebe XP an Benutzer
            award_xp(request.user, xp_earned)

        request.session.pop(session_key, None)
        request.session.modified = True

        wrong_items = [item for item in review_items if not item["is_correct"]]

        return render(request, "result.html", {
            "score": score,
            "total": len(questions),
            "wrong_items": wrong_items,
            "topic": topic,
            "lesson": lesson,
            "course": course,
            **get_sidebar_context(request),
        })

    question = questions[current_index]
    qtype = question.question_type

    options = []
    if qtype in {"mc_single", "true_false", "image_single", "scenario_single", "multi_select"}:
        options = get_single_options(question)
        random.shuffle(options)

    matching_pairs = get_matching_pairs(question) if qtype == "matching" else []
    matching_right_items = [pair["right"] for pair in matching_pairs]
    if matching_right_items:
        random.shuffle(matching_right_items)

    ordering_items = get_order_items(question) if qtype == "ordering" else []
    ordering_items_shuffled = ordering_items[:]
    if ordering_items_shuffled:
        random.shuffle(ordering_items_shuffled)

    blanks = get_blanks(question) if qtype == "cloze" else []

    current_number = current_index + 1
    total_questions = len(questions)
    progress_percent = int((current_number / total_questions) * 100)

    return render(request, "quiz.html", {
        "question": question,
        "options": options,
        "matching_pairs": matching_pairs,
        "matching_right_items": matching_right_items,
        "ordering_items": ordering_items_shuffled,
        "blanks": blanks,
        "topic": topic,
        "lesson": lesson,
        "course": course,
        "current_number": current_number,
        "total_questions": total_questions,
        "progress_percent": progress_percent,
        **get_sidebar_context(request),
    })


@ensure_csrf_cookie
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/accounts/login/")
    else:
        form = UserCreationForm()

    return render(request, "signup.html", {"form": form})


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    next_url = request.GET.get("next") or request.POST.get("next")
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            auth_login(request, form.get_user())
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("dashboard")

        messages.error(request, "Benutzername oder Passwort ist falsch.")

    return render(request, "registration/login.html", {"form": form, "next": next_url})


def csrf_failure(request, reason=""):
    messages.error(request, "Deine Sitzung ist abgelaufen. Bitte Formular neu laden und erneut absenden.")

    path = (request.path or "").rstrip("/")
    if path == "/signup":
        return redirect("signup")
    if path == "/accounts/login":
        return redirect("login")

    return redirect("login")

@login_required
def dashboard(request):
    user = request.user
    now = timezone.now()
    courses = Course.objects.select_related("category").prefetch_related("lessons__topics", "flashcards").all()
    results = Result.objects.filter(user=user)
    flashcard_states = FlashcardUserState.objects.filter(user=user).select_related("flashcard", "flashcard__course")
    topic_view_states = (
        TopicViewState.objects.filter(user=user)
        .select_related("topic", "topic__lesson", "topic__lesson__course")
        .order_by("-last_viewed_at")
    )
    courses_with_progress = []

    states_by_course = {}
    for state in flashcard_states:
        states_by_course.setdefault(state.flashcard.course_id, []).append(state)

    for course in courses:
        total_questions = course.questions.count()
        last_result = results.filter(course=course).order_by("-date").first()
        best_result = results.filter(course=course).order_by("-score", "-date").first()
        lesson_count = course.lessons.count()
        topic_count = sum(lesson.topics.count() for lesson in course.lessons.all())
        flashcards_count = course.flashcards.count()
        course_states = states_by_course.get(course.id, [])
        reviewed_flashcards = len(course_states)
        due_flashcards = sum(
            1
            for state in course_states
            if not state.next_review_at or state.next_review_at <= now
        ) + max(0, flashcards_count - reviewed_flashcards)
        favorite_flashcards = sum(1 for state in course_states if state.is_favorite)

        if total_questions > 0 and last_result:
            progress = int((last_result.score / total_questions) * 100)
        else:
            progress = 0

        if due_flashcards > 0:
            next_step = f"{due_flashcards} Karteikarten zur Wiederholung"
        elif progress < 100 and total_questions > 0:
            next_step = "Quiz weiter verbessern"
        elif flashcards_count > 0:
            next_step = "Karteikarten vertiefen"
        else:
            next_step = "Lernmaterial durcharbeiten"

        courses_with_progress.append({
            "course": course,
            "progress": progress,
            "lesson_count": lesson_count,
            "topic_count": topic_count,
            "flashcards_count": flashcards_count,
            "due_flashcards": due_flashcards,
            "favorite_flashcards": favorite_flashcards,
            "last_activity": last_result.date if last_result else None,
            "best_score": best_result.score if best_result else None,
            "best_score_percent": int((best_result.score / total_questions) * 100) if best_result and total_questions else 0,
            "next_step": next_step,
        })

    user_stats = get_user_stats(user)
    leaderboard = get_leaderboard(limit=10)
    total_due_flashcards = sum(item["due_flashcards"] for item in courses_with_progress)
    total_favorite_flashcards = sum(item["favorite_flashcards"] for item in courses_with_progress)

    # 1) Trefferquote je Lernbereich (Kategorie)
    category_totals = defaultdict(lambda: {"correct": 0, "total": 0})
    for result in results.select_related("course__category"):
        category_name = result.course.category.name if result.course.category else "Ohne Kategorie"
        total_q = result.total_questions or result.course.questions.count()
        if total_q <= 0:
            continue
        category_totals[category_name]["correct"] += result.score
        category_totals[category_name]["total"] += total_q

    learning_area_accuracy = []
    for area_name, values in category_totals.items():
        if values["total"] <= 0:
            continue
        accuracy = int((values["correct"] / values["total"]) * 100)
        learning_area_accuracy.append({
            "name": area_name,
            "accuracy": accuracy,
            "correct": values["correct"],
            "total": values["total"],
        })
    learning_area_accuracy.sort(key=lambda item: item["accuracy"])

    # 2) Behaltensrate über 1/3/7 Tage (auf Basis letzter Wiederholung)
    retention_windows = [1, 3, 7]
    retention_stats = []
    for days in retention_windows:
        eligible_states = [
            state
            for state in flashcard_states
            if state.last_reviewed_at and (now - state.last_reviewed_at).days >= days
        ]
        remembered_count = sum(1 for state in eligible_states if state.last_result == "known")
        eligible_count = len(eligible_states)
        rate = int((remembered_count / eligible_count) * 100) if eligible_count else 0
        retention_stats.append({
            "days": days,
            "remembered": remembered_count,
            "total": eligible_count,
            "rate": rate,
        })

    context = {
        "courses_with_progress": courses_with_progress,
        "results": results,
        "user_stats": user_stats,
        "leaderboard": leaderboard,
        "total_due_flashcards": total_due_flashcards,
        "total_favorite_flashcards": total_favorite_flashcards,
        "learning_area_accuracy": learning_area_accuracy,
        "retention_stats": retention_stats,
        "resume_learning": get_resume_learning_context(topic_view_states),
        "recent_topic_states": list(topic_view_states[:5]),
        **get_sidebar_context(request),
    }

    return render(request, "dashboard.html", context)

@login_required
def leaderboard_view(request):
    """Zeige Leaderboard mit UserStats"""
    leaderboard = get_leaderboard(limit=50)
    user_position = None
    
    # Finde Position des aktuellen Users
    if request.user.is_authenticated:
        from exams.models import UserProfile
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            position = list(leaderboard.values_list('user_id', flat=True)).index(request.user.id) + 1
            user_position = position
        except (UserProfile.DoesNotExist, ValueError):
            user_position = None
    
    context = {
        "leaderboard": leaderboard,
        "user_position": user_position,
        **get_sidebar_context(request),
    }
    return render(request, "leaderboard.html", context)

def course_page(request, course_id):

    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.prefetch_related("topics").order_by("order", "id")
    
    # Berechne Fortschritt für jede Lektion und füge als Attribut hinzu
    for lesson in lessons:
        lesson.quiz_progress = get_lesson_progress(lesson, request.user)

    context = {
        "course": course,
        "lessons": lessons,
        **get_sidebar_context(request),
    }

    return render(request, "course.html", context)

def lesson_view(request, lesson_id):

    lesson = get_object_or_404(Lesson, id=lesson_id)

    context = {
        "lesson": lesson,
        "topics": lesson.topics.all(),
        **get_sidebar_context(request),
    }

    return render(request, "lesson.html", context)


def topic_view(request, topic_id):

    topic = get_object_or_404(Topic, id=topic_id)

    if request.user.is_authenticated:
        state, _created = TopicViewState.objects.get_or_create(user=request.user, topic=topic)
        state.visit_count += 1
        state.save(update_fields=["visit_count", "last_viewed_at"])

    topic_progress = get_topic_progress(topic, request.user)

    context = {
        "topic": topic,
        "topic_progress": topic_progress,
        "is_topic_favorite": request.user.is_authenticated and TopicFavorite.objects.filter(user=request.user, topic=topic).exists(),
        **get_sidebar_context(request),
    }

    return render(request, "topic.html", context)


@login_required
def toggle_topic_favorite(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    favorite = TopicFavorite.objects.filter(user=request.user, topic=topic).first()
    if favorite:
        favorite.delete()
    else:
        TopicFavorite.objects.create(user=request.user, topic=topic)

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(next_url)
    return redirect("topic", topic_id=topic.id)


@login_required
def search_view(request):
    query = (request.GET.get("q") or "").strip()
    courses = []
    lessons = []
    topics = []

    if query:
        courses = list(
            Course.objects.filter(title__icontains=query)
            .select_related("category")
            .order_by("title")[:20]
        )
        lessons = list(
            Lesson.objects.filter(title__icontains=query)
            .select_related("course")
            .order_by("course__title", "order", "id")[:30]
        )
        topics = list(
            Topic.objects.filter(title__icontains=query)
            .select_related("lesson", "lesson__course")
            .order_by("lesson__course__title", "lesson__order", "order", "id")[:50]
        )

    context = {
        "search_query": query,
        "courses_found": courses,
        "lessons_found": lessons,
        "topics_found": topics,
        "result_count": len(courses) + len(lessons) + len(topics),
        **get_sidebar_context(request),
    }
    return render(request, "search.html", context)


def get_resume_learning_context(topic_view_states):
    current_state = topic_view_states.first()
    if not current_state:
        return None

    current_topic = current_state.topic
    lesson_topics = list(current_topic.lesson.topics.order_by("order", "id"))
    next_topic = None

    for index, topic in enumerate(lesson_topics):
        if topic.id == current_topic.id and index + 1 < len(lesson_topics):
            next_topic = lesson_topics[index + 1]
            break

    return {
        "current_topic": current_topic,
        "current_lesson": current_topic.lesson,
        "current_course": current_topic.lesson.course,
        "next_topic": next_topic,
        "last_viewed_at": current_state.last_viewed_at,
    }