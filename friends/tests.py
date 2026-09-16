from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import FriendRequest


class FriendRequestWorkflowTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="secret123")
        self.user_b = User.objects.create_user(username="bob", password="secret123")

    def test_user_can_send_and_accept_friend_request(self):
        self.client.force_login(self.user_a)

        response = self.client.post(reverse("add_friend", args=[self.user_b.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            FriendRequest.objects.filter(
                sender=self.user_a,
                receiver=self.user_b,
                status="pending",
            ).exists()
        )

        request_obj = FriendRequest.objects.get(sender=self.user_a, receiver=self.user_b)
        self.client.force_login(self.user_b)

        response = self.client.post(reverse("accept_friend", args=[request_obj.id]))
        self.assertEqual(response.status_code, 302)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, "accepted")

    def test_user_can_reject_friend_request(self):
        request_obj = FriendRequest.objects.create(
            sender=self.user_a,
            receiver=self.user_b,
            status="pending",
        )

        self.client.force_login(self.user_b)
        response = self.client.post(reverse("reject_friend", args=[request_obj.id]))
        self.assertEqual(response.status_code, 302)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, "rejected")
