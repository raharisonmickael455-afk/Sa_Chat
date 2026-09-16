from django.contrib.auth.models import User
from django.db import models


class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_conversations")
    title = models.CharField(max_length=120, default="Nouvelle conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class AIMessage(models.Model):
    ROLE_CHOICES = [("user", "Utilisateur"), ("assistant", "Assistant")]
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]