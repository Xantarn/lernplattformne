from django.urls import path
from . import views
from courses.views import (
    create_flashcard,
    delete_flashcard,
    edit_flashcard,
    flashcard_view,
    record_flashcard_review,
    toggle_flashcard_favorite,
)

urlpatterns = [
    path("quiz/<int:course_id>/", views.quiz_view, name="quiz"),
    path("quiz/lesson/<int:lesson_id>/", views.lesson_quiz_view, name="lesson_quiz"),
    path("quiz/topic/<int:topic_id>/", views.topic_quiz_view, name="topic_quiz"),
    path("flashcards/<int:course_id>/", flashcard_view, name="flashcards"),
    path("flashcards/<int:course_id>/create/", create_flashcard, name="create_flashcard"),
    path("flashcards/<int:flashcard_id>/edit/", edit_flashcard, name="edit_flashcard"),
    path("flashcards/<int:flashcard_id>/delete/", delete_flashcard, name="delete_flashcard"),
    path("flashcards/<int:flashcard_id>/favorite/", toggle_flashcard_favorite, name="toggle_flashcard_favorite"),
    path("flashcards/<int:flashcard_id>/review/", record_flashcard_review, name="record_flashcard_review"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("course/<int:course_id>/", views.course_page, name="course"),
    path("lesson/<int:lesson_id>/", views.lesson_view, name="lesson"),
    path("topic/<int:topic_id>/", views.topic_view, name="topic"),
    path("topic/<int:topic_id>/favorite/", views.toggle_topic_favorite, name="toggle_topic_favorite"),
    path("search/", views.search_view, name="search"),
]