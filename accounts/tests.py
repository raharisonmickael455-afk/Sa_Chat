from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from social.models import Story


class ProfileStoryTests(TestCase):
	def setUp(self):
		self.viewer = get_user_model().objects.create_user(username="viewer", password="pass123")
		self.author = get_user_model().objects.create_user(username="author", password="pass123")
		self.client.force_login(self.viewer)

	def test_active_story_is_displayed_on_public_profile(self):
		Story.objects.create(
			author=self.author,
			text="Story active",
			expires_at=timezone.now() + timedelta(hours=1),
		)

		response = self.client.get(reverse("user_profile", args=[self.author.username]))

		self.assertContains(response, "Stories de author")
		self.assertContains(response, "Story active")

	def test_expired_story_is_not_displayed_on_profile(self):
		Story.objects.create(
			author=self.author,
			text="Story expirée",
			expires_at=timezone.now() - timedelta(minutes=1),
		)

		response = self.client.get(reverse("user_profile", args=[self.author.username]))

		self.assertNotContains(response, "Stories de author")
		self.assertNotContains(response, "Story expirée")
