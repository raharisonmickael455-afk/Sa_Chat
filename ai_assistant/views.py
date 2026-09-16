import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import AIConversation, AIMessage
from .services.ai_service import AIServiceError, generate_reply


logger = logging.getLogger(__name__)


MAX_MESSAGE_LENGTH = 4000
CONTEXT_MESSAGE_LIMIT = 12


def _conversation_for_user(request, conversation_id=None):
    if conversation_id:
        try:
            conversation_id = int(conversation_id)
        except (TypeError, ValueError):
            return None
        return get_object_or_404(AIConversation, pk=conversation_id, user=request.user)
    return AIConversation.objects.filter(user=request.user).first()


def _history_payload(conversation):
    if not conversation:
        return []
    return [{"role": message.role, "text": message.content} for message in conversation.messages.all()]


@login_required
def ai_chat(request):
    conversation = _conversation_for_user(request)
    return render(request, "ai_assistant/chat.html", {
        "ai_conversation": conversation,
        "ai_history": _history_payload(conversation),
    })


@login_required
@require_POST
def ai_chat_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"success": False, "error": "Le corps doit etre un JSON valide."}, status=400)

    prompt = str(payload.get("message", "")).strip()
    if not prompt:
        return JsonResponse({"success": False, "error": "Le message ne peut pas etre vide."}, status=400)
    if len(prompt) > MAX_MESSAGE_LENGTH:
        return JsonResponse({"success": False, "error": "Le message est trop long (4000 caracteres maximum)."}, status=400)

    conversation_id = payload.get("conversation_id")
    if conversation_id not in (None, "") and not str(conversation_id).isdigit():
        return JsonResponse({"success": False, "error": "Identifiant de conversation invalide."}, status=400)

    conversation = _conversation_for_user(request, conversation_id)
    created_conversation = conversation is None
    if not conversation:
        conversation = AIConversation.objects.create(user=request.user, title=prompt[:120])

    recent_messages = list(conversation.messages.order_by("-created_at")[:CONTEXT_MESSAGE_LIMIT - 1])
    recent_messages.reverse()
    user_message = AIMessage.objects.create(conversation=conversation, role="user", content=prompt)
    try:
        answer = generate_reply(recent_messages + [user_message])
    except AIServiceError as error:
        user_message.delete()
        if created_conversation:
            conversation.delete()
        return JsonResponse({"success": False, "error": str(error)}, status=503)
    except Exception:
        logger.exception("Unexpected Sacha AI provider error")
        user_message.delete()
        if created_conversation:
            conversation.delete()
        return JsonResponse({"success": False, "error": "Le service Sacha AI est temporairement indisponible."}, status=503)

    AIMessage.objects.create(conversation=conversation, role="assistant", content=answer)
    conversation.save(update_fields=["updated_at"])
    return JsonResponse({
        "success": True,
        "conversation_id": conversation.id,
        "response": answer,
        "history": _history_payload(conversation),
    })


@login_required
@require_POST
def clear_ai_chat(request):
    conversation_id = request.POST.get("conversation_id")
    if conversation_id:
        AIConversation.objects.filter(pk=conversation_id, user=request.user).delete()
    else:
        AIConversation.objects.filter(user=request.user).delete()
    return JsonResponse({"success": True})