from django.contrib import admin

from .models import Conversation, Message, MessageRequest


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")
    filter_horizontal = ("participants",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("content", "sender__username")


@admin.register(MessageRequest)
class MessageRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("sender__username", "receiver__username")