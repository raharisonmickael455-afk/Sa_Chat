from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from social.models import Story
from posts.models import Post


class StoryFeatureTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice", password="pass123")
        self.friend = get_user_model().objects.create_user(username="bob", password="pass123")
        self.client.force_login(self.user)

    def test_story_can_be_deleted_by_owner(self):
        story = Story.objects.create(
            author=self.user,
            text="Bonjour @bob",
            expires_at=self.user.date_joined,
        )

        response = self.client.post(reverse("delete_story", args=[story.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Story.objects.filter(id=story.id).exists())

    def test_story_mentions_render_as_profile_links(self):
        story = Story.objects.create(
            author=self.user,
            text="Salut @bob, regarde ça.",
            expires_at=self.user.date_joined,
        )

        html = story.rich_text

        self.assertIn("@bob", html)
        self.assertIn(reverse("user_profile", args=[self.friend.username]), html)

    def test_saving_post_requires_post_request(self):
        post = Post.objects.create(author=self.user, content="À archiver")

        response = self.client.get(reverse("save_post", args=[post.id]))

        self.assertEqual(response.status_code, 405)
