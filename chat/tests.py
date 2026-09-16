from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from friends.models import FriendRequest
from notifications.models import Notification
from posts.models import Post
from .models import Conversation, Message, MessageRequest


class MessagingWorkflowTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="password123")
        self.user_b = User.objects.create_user(username="bob", password="password123")
        self.user_c = User.objects.create_user(username="charlie", password="password123")

    def login(self, user):
        self.client.force_login(user)

    def test_friend_request_acceptance_and_rejection(self):
        self.login(self.user_a)
        response = self.client.post(reverse("add_friend", args=[self.user_b.id]))
        self.assertEqual(response.status_code, 302)
        friend_request = FriendRequest.objects.get(sender=self.user_a, receiver=self.user_b)

        self.login(self.user_b)
        self.client.post(reverse("accept_friend", args=[friend_request.id]))
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, "accepted")

        self.login(self.user_a)
        self.client.post(reverse("add_friend", args=[self.user_c.id]))
        rejected_request = FriendRequest.objects.get(sender=self.user_a, receiver=self.user_c)
        self.login(self.user_c)
        self.client.post(reverse("reject_friend", args=[rejected_request.id]))
        rejected_request.refresh_from_db()
        self.assertEqual(rejected_request.status, "rejected")

    def test_message_request_acceptance_creates_conversation_and_unread_message(self):
        self.login(self.user_a)
        response = self.client.post(reverse("start_conversation", args=[self.user_b.id]))
        self.assertEqual(response.status_code, 302)
        message_request = MessageRequest.objects.get(sender=self.user_a, receiver=self.user_b)
        self.assertTrue(Notification.objects.filter(user=self.user_b, notification_type="message_request").exists())

        self.login(self.user_b)
        response = self.client.post(reverse("accept_message_request", args=[message_request.id]))
        conversation = Conversation.objects.get()
        self.assertRedirects(response, reverse("conversation", args=[conversation.id]))
        message_request.refresh_from_db()
        self.assertEqual(message_request.status, "accepted")

        self.login(self.user_a)
        self.client.post(reverse("conversation", args=[conversation.id]), {"content": "Bonjour"})
        message = Message.objects.get(conversation=conversation)
        self.assertFalse(message.is_read)

        self.login(self.user_b)
        response = self.client.get(reverse("conversation", args=[conversation.id]))
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_message_request_rejection_and_conversation_permission(self):
        self.login(self.user_a)
        self.client.post(reverse("start_conversation", args=[self.user_b.id]))
        message_request = MessageRequest.objects.get(sender=self.user_a, receiver=self.user_b)

        self.login(self.user_b)
        self.client.post(reverse("reject_message_request", args=[message_request.id]))
        message_request.refresh_from_db()
        self.assertEqual(message_request.status, "rejected")
        self.assertFalse(Conversation.objects.exists())

        conversation = Conversation.objects.create()
        conversation.participants.set([self.user_a, self.user_b])
        self.login(self.user_c)
        response = self.client.get(reverse("conversation", args=[conversation.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_accept_someone_elses_message_request(self):
        message_request = MessageRequest.objects.create(sender=self.user_a, receiver=self.user_b)
        self.login(self.user_c)
        response = self.client.post(reverse("accept_message_request", args=[message_request.id]))
        self.assertEqual(response.status_code, 404)
        message_request.refresh_from_db()
        self.assertEqual(message_request.status, "pending")

    def test_user_can_share_visible_post_in_conversation(self):
        conversation = Conversation.objects.create()
        conversation.participants.set([self.user_a, self.user_b])
        post = Post.objects.create(author=self.user_a, content="Publication à partager")
        self.login(self.user_b)

        response = self.client.post(
            reverse("share_post_to_conversation", args=[post.id]),
            {"conversation_id": conversation.id},
        )

        self.assertRedirects(response, reverse("conversation", args=[conversation.id]))
        message = Message.objects.get(conversation=conversation)
        self.assertEqual(message.sender, self.user_b)
        self.assertEqual(message.shared_post, post)

    def test_user_cannot_share_post_in_conversation_they_do_not_join(self):
        conversation = Conversation.objects.create()
        conversation.participants.set([self.user_a, self.user_b])
        post = Post.objects.create(author=self.user_a, content="Publication privée")
        self.login(self.user_c)

        response = self.client.post(
            reverse("share_post_to_conversation", args=[post.id]),
            {"conversation_id": conversation.id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Message.objects.filter(shared_post=post).exists())
