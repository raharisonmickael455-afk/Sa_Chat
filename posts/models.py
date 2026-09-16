from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.
from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("friends", "Amis"),
        ("private", "Privé"),
    ]
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    content = models.TextField()

    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True
    )
    video = models.FileField(
        upload_to="videos/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["mp4", "webm", "mov"])],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="public",
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.username} - {self.created_at}"


class Like(models.Model):
    REACTION_CHOICES = [
        ("like", "👍 J'aime"),
        ("love", "❤️ J'adore"),
        ("haha", "😂 Haha"),
        ("wow", "😮 Waouh"),
        ("sad", "😢 Triste"),
        ("angry", "😡 En colère"),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_likes")
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES, default="like")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_post_like")
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.reaction_type} on {self.post_id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="replies",
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]


class Share(models.Model):
    VISIBILITY_CHOICES = Post.VISIBILITY_CHOICES
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shares")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="friends")
    created_at = models.DateTimeField(auto_now_add=True)