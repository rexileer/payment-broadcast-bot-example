from django.contrib import admin
from .models import PostingMessage, StartCommandResponse, FallbackNotificationMessage
from django.utils.html import format_html
from django.forms import FileInput
from django.db import models


@admin.register(StartCommandResponse)
class StartCommandResponseAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not StartCommandResponse.objects.exists()  # Разрешаем добавлять, только если нет записей

    def has_delete_permission(self, request, obj=None):
        return False  # Запрещаем удаление

@admin.register(FallbackNotificationMessage)
class FallbackNotificationMessageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not FallbackNotificationMessage.objects.exists()  # Разрешаем добавлять, только если нет записей

    def has_delete_permission(self, request, obj=None):
        return False  # Запрещаем удаление


@admin.register(PostingMessage)
class PostingMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "send_time", "media_display")
    ordering = ("send_time",)
    readonly_fields = ("media_preview",)

    formfield_overrides = {
        models.FileField: {"widget": FileInput(attrs={"accept": "image/*,video/*"})},
    }

    def media_display(self, obj):
        """Предпросмотр медиа в списке публикаций"""
        if obj.file:
            if obj.media_type == "image":
                return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.file.url)
            elif obj.media_type == "video":
                return format_html('<video width="150" height="100" controls><source src="{}" type="video/mp4"></video>', obj.file.url)
        return "Нет медиа"

    media_display.short_description = "Медиа"

    def media_preview(self, obj):
        """Предпросмотр медиа в форме редактирования"""
        if obj.file:
            if obj.media_type == "image":
                return format_html('<img src="{}" style="max-width: 300px; max-height: 300px; margin-top: 10px;" />', obj.file.url)
            elif obj.media_type == "video":
                return format_html('<video width="300" height="200" controls style="margin-top: 10px;"><source src="{}" type="video/mp4"></video>', obj.file.url)
        return "Нет медиафайла"

    media_preview.short_description = "Предпросмотр медиа"