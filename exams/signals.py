"""
Signals für automatische Erstellung von Profilen bei User-Erstellung
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from exams.models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Erstelle UserProfile wenn neuer User angelegt wird"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
