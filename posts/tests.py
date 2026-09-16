from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Like, Post


class PostInteractionTests(TestCase):
	def setUp(self):
		self.author = User.objects.create_user(username="author", password="password123")
		self.reader = User.objects.create_user(username="reader", password="password123")
		self.post = Post.objects.create(author=self.author, content="Publication publique")

	def test_user_can_create_reply_to_visible_comment(self):
		comment = Comment.objects.create(post=self.post, author=self.author, content="Commentaire")
		self.client.force_login(self.reader)

		response = self.client.post(reverse("create_comment", args=[self.post.id]), {
			"content": "Réponse",
			"parent_id": comment.id,
		})

		self.assertRedirects(response, reverse("post_detail", args=[self.post.id]))
		reply = Comment.objects.get(content="Réponse")
		self.assertEqual(reply.parent_id, comment.id)

	def test_user_cannot_edit_another_users_comment(self):
		comment = Comment.objects.create(post=self.post, author=self.author, content="Original")
		self.client.force_login(self.reader)

		response = self.client.post(reverse("edit_comment", args=[comment.id]), {"content": "Modifié"})

		self.assertEqual(response.status_code, 404)
		comment.refresh_from_db()
		self.assertEqual(comment.content, "Original")

	def test_comment_creation_respects_next_url_from_feed(self):
		self.client.force_login(self.reader)
		next_url = reverse("post_list")

		response = self.client.post(reverse("create_comment", args=[self.post.id]), {
			"content": "Commentaire depuis le feed",
			"next": next_url,
		})

		self.assertRedirects(response, next_url)
		self.assertTrue(Comment.objects.filter(post=self.post, author=self.reader, content="Commentaire depuis le feed").exists())

	def test_like_ajax_response_tracks_state_and_count(self):
		self.client.force_login(self.reader)
		url = reverse("toggle_like", args=[self.post.id])
		headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

		response = self.client.post(url, **headers)
		self.assertJSONEqual(response.content, {"liked": True, "reaction": "like", "count": 1})
		self.assertTrue(Like.objects.filter(post=self.post, user=self.reader).exists())

		response = self.client.post(url, **headers)
		self.assertJSONEqual(response.content, {"liked": False, "reaction": None, "count": 0})

	def test_private_post_cannot_be_liked_by_another_user(self):
		self.post.visibility = "private"
		self.post.save(update_fields=["visibility"])
		self.client.force_login(self.reader)

		response = self.client.post(reverse("toggle_like", args=[self.post.id]))

		self.assertEqual(response.status_code, 404)
		self.assertFalse(Like.objects.filter(post=self.post, user=self.reader).exists())

	def test_reaction_can_be_swapped_and_toggled_off(self):
		self.client.force_login(self.reader)
		url = reverse("toggle_like", args=[self.post.id])

		response = self.client.post(url, {"reaction_type": "love"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
		self.assertJSONEqual(response.content, {"liked": True, "reaction": "love", "count": 1})
		self.assertEqual(Like.objects.get(post=self.post, user=self.reader).reaction_type, "love")

		response = self.client.post(url, {"reaction_type": "haha"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
		self.assertJSONEqual(response.content, {"liked": True, "reaction": "haha", "count": 1})
		self.assertEqual(Like.objects.get(post=self.post, user=self.reader).reaction_type, "haha")

		response = self.client.post(url, {"reaction_type": "haha"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
		self.assertJSONEqual(response.content, {"liked": False, "reaction": None, "count": 0})
		self.assertFalse(Like.objects.filter(post=self.post, user=self.reader).exists())

	def test_author_can_delete_own_post(self):
		self.client.force_login(self.author)

		response = self.client.post(reverse("delete_post", args=[self.post.id]))

		self.assertRedirects(response, reverse("post_list"))
		self.assertFalse(Post.objects.filter(id=self.post.id).exists())

	def test_user_cannot_delete_another_users_post(self):
		self.client.force_login(self.reader)

		response = self.client.post(reverse("delete_post", args=[self.post.id]))

		self.assertEqual(response.status_code, 404)
		self.assertTrue(Post.objects.filter(id=self.post.id).exists())

	def test_author_can_archive_and_restore_post(self):
		self.client.force_login(self.author)

		response = self.client.post(reverse("toggle_archive", args=[self.post.id]))

		self.assertRedirects(response, reverse("post_list"))
		self.post.refresh_from_db()
		self.assertTrue(self.post.is_archived)
		self.assertNotContains(self.client.get(reverse("post_list")), self.post.content)

		response = self.client.post(
			reverse("toggle_archive", args=[self.post.id]),
			{"next": reverse("archived_posts")},
		)
		self.assertRedirects(response, reverse("archived_posts"))
		self.post.refresh_from_db()
		self.assertFalse(self.post.is_archived)

	def test_only_author_can_change_post_visibility(self):
		self.client.force_login(self.reader)

		response = self.client.post(
			reverse("change_post_visibility", args=[self.post.id]),
			{"visibility": "private"},
		)

		self.assertEqual(response.status_code, 404)
		self.post.refresh_from_db()
		self.assertEqual(self.post.visibility, "public")

		self.client.force_login(self.author)
		response = self.client.post(
			reverse("change_post_visibility", args=[self.post.id]),
			{"visibility": "friends"},
		)
		self.assertRedirects(response, reverse("post_list"))
		self.post.refresh_from_db()
		self.assertEqual(self.post.visibility, "friends")
