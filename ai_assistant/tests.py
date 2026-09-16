import importlib
import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ai_assistant.models import AIConversation, AIMessage


class AiChatApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="assistant-test",
            password="test-password-123",
        )
        self.client.force_login(self.user)

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False)
    def test_api_returns_configuration_message_without_key(self):
        response = self.client.post(
            "/ai/api/",
            data='{"message":"Bonjour"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.json()["error"])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "runtime-secret"}, clear=False)
    def test_settings_reads_gemini_key_from_environment(self):
        import sa_chat.settings as settings_module
        importlib.reload(settings_module)
        self.assertEqual(settings_module.GEMINI_API_KEY, "runtime-secret")

    def test_api_rejects_empty_message(self):
        response = self.client.post(
            "/ai/api/",
            data='{"message":"  "}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("vide", response.json()["error"])

    @patch("ai_assistant.views.generate_reply", return_value="Django est un framework Python.")
    def test_api_persists_conversation_and_context(self, generate_reply):
        response = self.client.post(
            "/api/ai/chat/",
            data='{"message":"Explique Django"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        conversation = AIConversation.objects.get(user=self.user)
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(conversation.messages.last().role, "assistant")
        generate_reply.assert_called_once()

    def test_cannot_access_another_users_conversation(self):
        other_user = get_user_model().objects.create_user(username="other", password="test-password-123")
        conversation = AIConversation.objects.create(user=other_user)
        response = self.client.post(
            "/api/ai/chat/",
            data='{"conversation_id":%d,"message":"test"}' % conversation.id,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(AIMessage.objects.filter(conversation=conversation).exists())

    def test_api_rejects_invalid_conversation_id(self):
        response = self.client.post(
            "/api/ai/chat/",
            data='{"conversation_id":"abc","message":"test"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalide", response.json()["error"])

    @patch("ai_assistant.views.generate_reply", side_effect=Exception("provider failure"))
    def test_provider_failure_does_not_leave_empty_conversation(self, generate_reply):
        response = self.client.post(
            "/api/ai/chat/",
            data='{"message":"Bonjour"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(AIConversation.objects.filter(user=self.user).exists())
