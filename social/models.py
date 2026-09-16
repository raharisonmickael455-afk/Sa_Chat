import re

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from posts.models import Post


class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
    text = models.CharField(max_length=280, blank=True)
    image = models.ImageField(upload_to="stories/", blank=True, null=True)
    video = models.FileField(upload_to="stories/videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_active(self):
        return self.expires_at > timezone.now()

    @property
    def rich_text(self):
        if not self.text:
            return ""

        def replace_mention(match):
            username = match.group(1)
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return f"@{username}"
            url = reverse("user_profile", kwargs={"username": user.username})
            return f'<a href="{url}" class="story-mention" data-user="{escape(user.username)}">@{escape(user.username)}</a>'

        pattern = r"(?<!\w)@([A-Za-z0-9_.-]+)"
        rendered = re.sub(pattern, replace_mention, escape(self.text))
        return rendered


class Reaction(models.Model):
    TYPES = [("like", "J'aime"), ("useful", "Utile"), ("interesting", "Intéressant"), ("support", "Soutien")]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    reaction_type = models.CharField(max_length=20, choices=TYPES, default="like")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["post", "user"], name="unique_post_reaction")]


class Collection(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class SavedPost(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="saved_posts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saved_in_collections")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["collection", "post"], name="unique_saved_post")]


class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_groups")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, through="GroupMembership", related_name="social_groups")
    created_at = models.DateTimeField(auto_now_add=True)


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["group", "user"], name="unique_group_member")]


class Event(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_events")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    starts_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    attendees = models.ManyToManyField(User, through="EventParticipant", related_name="events")


class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_participations")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="unique_event_participant")]


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=20, default="★")


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="users")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge")]
