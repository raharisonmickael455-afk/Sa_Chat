from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from friends.models import FriendRequest
from notifications.models import Notification
from posts.views import visible_posts
from .models import Conversation, Message, MessageRequest


def are_friends(user_a, user_b):
    return FriendRequest.objects.filter(
        Q(sender=user_a, receiver=user_b) | Q(sender=user_b, receiver=user_a),
        status="accepted",
    ).exists()


@login_required
def conversation_list(request):
    query = request.GET.get("q", "").strip()
    conversations = request.user.conversations.prefetch_related("participants", "messages").annotate(
        unread_count=Count("messages", filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )
    if query:
        conversations = conversations.filter(participants__username__icontains=query).distinct()
    requests = MessageRequest.objects.filter(receiver=request.user, status="pending").select_related("sender")
    return render(request, "chat/conversation_list.html", {
        "conversations": conversations,
        "message_requests": requests,
        "conversation_query": query,
    })


@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        return redirect("user_search")
    if not are_friends(request.user, other_user):
        if request.method == "POST":
            reverse_pending = MessageRequest.objects.filter(
                sender=other_user,
                receiver=request.user,
                status="pending",
            ).exists()
            if reverse_pending:
                return redirect("user_profile", username=other_user.username)
            message_request, created = MessageRequest.objects.get_or_create(
                sender=request.user,
                receiver=other_user,
                defaults={"status": "pending"},
            )
            was_pending = message_request.status == "pending"
            if not created and not was_pending:
                message_request.status = "pending"
                message_request.save(update_fields=["status"])
            if created or not was_pending:
                Notification.objects.create(
                    user=other_user,
                    actor=request.user,
                    notification_type="message_request",
                    message=f"{request.user.username} vous a envoyé une demande de message.",
                    message_request=message_request,
                )
        return redirect("user_profile", username=other_user.username)
    conversation = next(
        (
            item for item in request.user.conversations.all()
            if item.participants.count() == 2 and item.participants.filter(id=other_user.id).exists()
        ),
        None,
    )
    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.set([request.user, other_user])
    return redirect("conversation", conversation_id=conversation.id)


@login_required
def accept_message_request(request, request_id):
    message_request = get_object_or_404(
        MessageRequest,
        id=request_id,
        receiver=request.user,
        status="pending",
    )
    if request.method == "POST":
        message_request.status = "accepted"
        message_request.save(update_fields=["status"])
        conversation = Conversation.objects.create()
        conversation.participants.set([message_request.sender, message_request.receiver])
        return redirect("conversation", conversation_id=conversation.id)
    return redirect("conversation_list")


@login_required
def reject_message_request(request, request_id):
    message_request = get_object_or_404(
        MessageRequest,
        id=request_id,
        receiver=request.user,
        status="pending",
    )
    if request.method == "POST":
        message_request.status = "rejected"
        message_request.save(update_fields=["status"])
    return redirect("conversation_list")


@login_required
def conversation(request, conversation_id):
    conversation_obj = get_object_or_404(
        Conversation.objects.prefetch_related(
            "participants",
            "messages__sender",
            "messages__shared_post__author",
        ),
        id=conversation_id,
        participants=request.user,
    )
    other_user = conversation_obj.participants.exclude(id=request.user.id).first()
    if request.method == "GET":
        conversation_obj.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Message.objects.create(conversation=conversation_obj, sender=request.user, content=content)
            conversation_obj.save(update_fields=["updated_at"])
        return redirect("conversation", conversation_id=conversation_obj.id)
    return render(request, "chat/conversation.html", {
        "conversation": conversation_obj,
        "other_user": other_user,
    })


@login_required
def share_post_to_conversation(request, post_id):
    conversation_id = request.POST.get("conversation_id")
    conversation_obj = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
    )
    post = get_object_or_404(visible_posts(request.user), id=post_id)

    if request.method == "POST":
        Message.objects.create(
            conversation=conversation_obj,
            sender=request.user,
            content="Publication partagée",
            shared_post=post,
        )
        conversation_obj.save(update_fields=["updated_at"])
        return redirect("conversation", conversation_id=conversation_obj.id)

    return redirect("post_detail", post_id=post.id)
