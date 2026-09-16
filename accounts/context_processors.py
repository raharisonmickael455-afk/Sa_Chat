from notifications.models import Notification
from chat.models import Message
from social.models import Story
from .models import Profile
from django.utils import timezone


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notification_count": 0, "profile_theme": "light", "story_user_ids": []}
    profile, _ = Profile.objects.get_or_create(user=request.user)
    story_user_ids = list(Story.objects.filter(expires_at__gt=timezone.now()).values_list("author_id", flat=True))
    return {
        "unread_notification_count": Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count(),
        "unread_message_count": Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count(),
        "profile_theme": profile.theme,
        "story_user_ids": story_user_ids,
    }
