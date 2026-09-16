from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("accepted", "Acceptée"),
        ("rejected", "Refusée"),
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_friend_requests"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_friend_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                name="unique_friend_request"
            )
        ]

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.status})"