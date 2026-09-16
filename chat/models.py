from django.contrib.auth.models import User
from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(max_length=2000)
    shared_post = models.ForeignKey(
        "posts.Post",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="chat_messages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]


class MessageRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("accepted", "Acceptée"),
        ("rejected", "Refusée"),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_message_requests")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_message_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["sender", "receiver"], name="unique_message_request")
        ]
