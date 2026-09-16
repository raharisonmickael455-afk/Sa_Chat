from django.db import models
from django.urls import reverse

from django.contrib.auth.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ("friend_request", "Demande d'ami"),
        ("friend_accepted", "Demande acceptée"),
        ("new_post", "Nouvelle publication"),
        ("comment", "Commentaire"),
        ("like", "J'aime"),
        ("share", "Partage"),
        ("message_request", "Demande de message"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="triggered_notifications",
        blank=True,
        null=True,
    )
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    related_post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )
    related_story = models.ForeignKey(
        "social.Story",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )
    friend_request = models.ForeignKey(
        "friends.FriendRequest",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )
    message_request = models.ForeignKey(
        "chat.MessageRequest",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def get_target_url(self):
        if self.related_post:
            return reverse("post_detail", args=[self.related_post.id])
        if self.related_story:
            return f"{reverse('story_list')}#story-{self.related_story.id}"
        if self.friend_request:
            return reverse("friend_requests")
        if self.message_request:
            return reverse("conversation_list")
        return reverse("notification_list")

    def __str__(self):
        return f"{self.user.username} - {self.message}"