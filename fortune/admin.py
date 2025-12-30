from django.contrib import admin
from .models import FortuneMessage, LuckyOption


@admin.register(FortuneMessage)
class FortuneMessageAdmin(admin.ModelAdmin):
    list_display = ("tone", "text", "is_active", "created_at")
    list_filter = ("tone", "is_active")
    search_fields = ("text",)
    list_editable = ("is_active",)


@admin.register(LuckyOption)
class LuckyOptionAdmin(admin.ModelAdmin):
    list_display = ("type", "value", "label", "is_active", "created_at")
    list_filter = ("type", "is_active")
    search_fields = ("value", "label")
    list_editable = ("is_active",)
