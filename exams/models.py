from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Benutzer-Profil mit XP und Erfolgen"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    total_xp = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-total_xp"]
    
    def __str__(self):
        return f"{self.user.username} - {self.total_xp} XP"
    
    def get_level(self):
        """Berechne Level basierend auf XP (1 Level = 500 XP)"""
        return max(1, self.total_xp // 500 + 1)
    
    def get_xp_for_next_level(self):
        """XP benötigt bis zum nächsten Level"""
        current_level = self.get_level()
        next_level_xp = current_level * 500
        return next_level_xp - self.total_xp


class Badge(models.Model):
    """Definiert verfügbare Badges"""
    BADGE_TYPES = [
        ("achievement", "Achievement"),
        ("milestone", "Meilenstein"),
        ("skill", "Fähigkeit"),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_emoji = models.CharField(max_length=10)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, default="achievement")
    condition = models.TextField(help_text="Bedingung für Badge (z.B. '5_courses_completed')")
    
    def __str__(self):
        return f"{self.icon_emoji} {self.name}"


class UserBadge(models.Model):
    """Tracking welche Badges Nutzer haben"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "badge")
        ordering = ["-earned_at"]
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, null=True, blank=True, related_name="quiz_results")
    topic = models.ForeignKey("courses.Topic", on_delete=models.CASCADE, null=True, blank=True, related_name="quiz_results")
    score = models.IntegerField()
    total_questions = models.IntegerField(default=0)
    xp_earned = models.IntegerField(default=0, help_text="XP die bei diesem Quiz verdient wurden")
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.topic:
            return f"{self.user.username} - {self.topic.title}: {self.score}/{self.total_questions}"
        elif self.lesson:
            return f"{self.user.username} - {self.lesson.title}: {self.score}/{self.total_questions}"
        return f"{self.user.username} - {self.course.title}: {self.score}/{self.total_questions}"