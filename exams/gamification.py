"""
XP und Badge Management für Gamification
"""
from django.db import models
from django.db.models import F
from exams.models import UserProfile, UserBadge, Badge, Result
from django.contrib.auth.models import User


def award_xp(user, amount):
    """Vergebe XP an einen Benutzer und aktualisiere sein Profil"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.total_xp += amount
    profile.save()
    check_badge_conditions(user)
    return profile.total_xp


def get_user_xp(user):
    """Hole die Gesamt-XP eines Benutzers"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile.total_xp


def calculate_quiz_xp(score, total_questions, questions):
    """
    Berechne gesamt XP basierend auf:
    - Richtigkeit (Prozentsatz)
    - Schwierigkeit der Fragen
    """
    if total_questions == 0:
        return 0
    
    accuracy = score / total_questions
    total_xp_value = sum(q.get_xp_value() for q in questions)
    
    # XP = (Basis-XP × Genauigkeit) + Bonus für perfekten Score
    xp = int(total_xp_value * accuracy)
    
    if accuracy == 1.0:
        xp = int(xp * 1.5)  # 50% Bonus für perfekten Score
    
    return max(xp, 1)  # Mindestens 1 XP


def check_badge_conditions(user):
    """Prüfe alle Badge-Bedingungen und vergebe ggf. Badges"""
    all_badges = Badge.objects.all()
    
    for badge in all_badges:
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            continue  # Benutzer hat Badge bereits
        
        condition = badge.condition
        
        # Überprüfe verschiedene Bedingungen
        if condition == "first_quiz_complete":
            if Result.objects.filter(user=user).exists():
                UserBadge.objects.create(user=user, badge=badge)
        
        elif condition.startswith("courses_completed_"):
            count = int(condition.split("_")[-1])
            completed = Result.objects.filter(user=user).values("course").distinct().count()
            if completed >= count:
                UserBadge.objects.create(user=user, badge=badge)
        
        elif condition.startswith("xp_threshold_"):
            threshold = int(condition.split("_")[-1])
            if get_user_xp(user) >= threshold:
                UserBadge.objects.create(user=user, badge=badge)
        
        elif condition == "perfect_score":
            perfect_results = Result.objects.filter(
                user=user,
            ).exclude(
                score=0,
                total_questions=0,
            )
            # Perfekter Score: Score == total_questions
            perfect = [r for r in perfect_results if r.score == r.total_questions]
            if perfect:
                UserBadge.objects.create(user=user, badge=badge)
        
        elif condition == "streak_3_days":
            # Vereinfachter Check: 3+ Tage hintereinander aktiv
            from django.utils import timezone
            from datetime import timedelta
            
            today = timezone.now().date()
            three_days_ago = today - timedelta(days=2)
            
            dates = set(
                Result.objects.filter(
                    user=user,
                    date__date__gte=three_days_ago
                ).values_list('date__date', flat=True)
            )
            
            if len(dates) >= 3:
                UserBadge.objects.create(user=user, badge=badge)


def get_user_stats(user):
    """Hole wichtige Statistiken eines Benutzers"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    results = Result.objects.filter(user=user)
    
    total_quizzes = results.count()
    courses_completed = results.filter(
        score=models.F('total_questions')
    ).values("course").distinct().count()
    
    avg_score = 0
    if total_quizzes > 0:
        total_correct = sum(r.score for r in results)
        total_questions = sum(r.total_questions for r in results) or 1
        avg_score = int((total_correct / total_questions) * 100)
    
    badges = UserBadge.objects.filter(user=user).select_related("badge")
    
    return {
        "level": profile.get_level(),
        "xp": profile.total_xp,
        "xp_for_next_level": profile.get_xp_for_next_level(),
        "total_quizzes": total_quizzes,
        "courses_completed": courses_completed,
        "accuracy": avg_score,
        "badges": badges,
    }


def get_leaderboard(limit=20):
    """Hole Top-Benutzer nach XP"""
    return UserProfile.objects.all().order_by("-total_xp")[:limit]
