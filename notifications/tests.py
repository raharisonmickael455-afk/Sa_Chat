from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from posts.models import Post


class NotificationTargetAndDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="password123")
        self.actor = User.objects.create_user(username="bob", password="password123")
        self.post = Post.objects.create(author=self.actor, content="Publication de test")

    def test_notification_has_target_url_for_post_activity(self):
        notification = Notification.objects.create(
            user=self.user,
            actor=self.actor,
            notification_type="like",
            message="Bob a aimé votre publication.",
            related_post=self.post,
        )

        self.assertEqual(notification.get_target_url(), reverse("post_detail", args=[self.post.id]))

    def test_user_can_delete_notification(self):
        notification = Notification.objects.create(
            user=self.user,
            actor=self.actor,
            notification_type="comment",
            message="Bob a commenté votre publication.",
            related_post=self.post,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("delete_notification", args=[notification.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())
