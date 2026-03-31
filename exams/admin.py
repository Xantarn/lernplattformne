from django.contrib import admin
from .models import Result, UserProfile, Badge, UserBadge

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "lesson", "topic", "score", "total_questions", "xp_earned", "date")
    list_filter = ("date", "course", "lesson", "topic")
    search_fields = ("user__username", "course__title", "lesson__title", "topic__title")
    readonly_fields = ("date", "xp_earned")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "total_xp", "get_level", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username",)
    readonly_fields = ("created_at", "total_xp")

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("icon_emoji", "name", "badge_type", "condition")
    list_filter = ("badge_type",)
    search_fields = ("name", "condition")

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "earned_at")
    list_filter = ("earned_at", "badge")
    search_fields = ("user__username", "badge__name")
    readonly_fields = ("earned_at",)