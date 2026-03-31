from django.conf import settings
from django.db import models


class Category(models.Model):

    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Course(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="courses",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    def __str__(self):
        return self.title



class Lesson(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons"
    )

    title = models.CharField(max_length=200)

    content = models.TextField()

    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Topic(models.Model):

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="topics"
    )

    title = models.CharField(max_length=200)

    learning_material = models.TextField()

    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Flashcard(models.Model):
    """Karteikarten für Kurse"""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_flashcards",
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="flashcards"
    )
    
    front = models.TextField(help_text="Vorderseite der Karte (Frage)")
    back = models.TextField(help_text="Rückseite der Karte (Antwort/Erklärung)")
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["order", "id"]
    
    def __str__(self):
        return f"{self.course.title} - {self.front[:50]}"
    
    @property
    def has_multiple_choice(self):
        """Prüfe ob diese Karte Multiple-Choice-Optionen hat"""
        return self.options.exists()


class FlashcardOption(models.Model):
    """Multiple-Choice-Optionen für Karteikarten"""
    flashcard = models.ForeignKey(
        Flashcard,
        on_delete=models.CASCADE,
        related_name="options"
    )
    
    text = models.CharField(max_length=500, help_text="Optionstext")
    is_correct = models.BooleanField(default=False, help_text="Dies ist die richtige Antwort")
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["order", "id"]
    
    def __str__(self):
        return f"{self.flashcard.front[:30]} - {self.text[:30]}"


class FlashcardUserState(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flashcard_states",
    )
    flashcard = models.ForeignKey(
        Flashcard,
        on_delete=models.CASCADE,
        related_name="user_states",
    )
    is_favorite = models.BooleanField(default=False)
    last_result = models.CharField(max_length=20, blank=True)
    consecutive_correct = models.IntegerField(default=0)
    review_count = models.IntegerField(default=0)
    interval_days = models.IntegerField(default=0)
    next_review_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_review_at", "id"]
        unique_together = ("user", "flashcard")

    def __str__(self):
        return f"{self.user} - {self.flashcard}"


class TopicViewState(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_view_states",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="view_states",
    )
    last_viewed_at = models.DateTimeField(auto_now=True)
    visit_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-last_viewed_at", "id"]
        unique_together = ("user", "topic")

    def __str__(self):
        return f"{self.user} - {self.topic}"


class TopicFavorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_favorites",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        unique_together = ("user", "topic")

    def __str__(self):
        return f"{self.user} - {self.topic}"