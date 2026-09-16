from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import FriendRequest
from notifications.models import Notification


@login_required
def friend_list(request):
    accepted_requests = FriendRequest.objects.filter(
        Q(sender=request.user, status="accepted") |
        Q(receiver=request.user, status="accepted")
    ).select_related("sender", "receiver")

    friends = []

    for friend_request in accepted_requests:
        if friend_request.sender == request.user:
            friends.append(friend_request.receiver)
        else:
            friends.append(friend_request.sender)

    return render(
        request,
        "friends/friend_list.html",
        {"friends": friends, "sent_requests": FriendRequest.objects.filter(sender=request.user, status="pending").select_related("receiver")}
    )


@login_required
def friend_requests(request):
    requests = FriendRequest.objects.filter(
        receiver=request.user,
        status="pending"
    ).select_related("sender")

    return render(
        request,
        "friends/friend_requests.html",
        {"requests": requests}
    )


@login_required
def add_friend(request, user_id):
    if request.method != "POST":
        return redirect("user_search")
    receiver = get_object_or_404(User, id=user_id)

    if receiver == request.user:
        messages.error(
            request,
            "Vous ne pouvez pas vous envoyer une demande."
        )
        return redirect("friend_list")

    existing_request = FriendRequest.objects.filter(
        sender=request.user,
        receiver=receiver
    ).first()

    if existing_request:
        messages.info(
            request,
            "Une demande existe déjà."
        )
        return redirect("friend_list")

    reverse_request = FriendRequest.objects.filter(
        sender=receiver,
        receiver=request.user
    ).first()

    if reverse_request:
        messages.info(
            request,
            "Cette personne vous a déjà envoyé une demande."
        )
        return redirect("friend_list")

    friend_request = FriendRequest.objects.create(
        sender=request.user,
        receiver=receiver
    )
    Notification.objects.create(
        user=receiver,
        actor=request.user,
        notification_type="friend_request",
        message=f"{request.user.username} vous a envoyé une demande d'ami.",
        friend_request=friend_request,
    )

    messages.success(
        request,
        f"Demande d'ami envoyée à {receiver.username}."
    )

    return redirect("friend_list")


@login_required
def accept_friend(request, request_id):
    if request.method != "POST":
        return redirect("friend_requests")
    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=request.user,
        status="pending"
    )

    friend_request.status = "accepted"
    friend_request.save(update_fields=["status"])
    Notification.objects.create(
        user=friend_request.sender,
        actor=request.user,
        notification_type="friend_accepted",
        message=f"{request.user.username} a accepté votre demande d'ami.",
    )

    messages.success(
        request,
        f"Vous êtes maintenant ami avec {friend_request.sender.username}."
    )

    return redirect("friend_requests")


@login_required
def reject_friend(request, request_id):
    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=request.user,
        status="pending",
    )
    if request.method == "POST":
        friend_request.status = "rejected"
        friend_request.save(update_fields=["status"])
        messages.info(request, "La demande d'ami a été refusée.")
    return redirect("friend_requests")


@login_required
def remove_friend(request, user_id):
    if request.method != "POST":
        return redirect("friend_list")
    other_user = get_object_or_404(User, id=user_id)

    friendship = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user),
        status="accepted"
    ).first()

    if friendship:
        friendship.delete()
        messages.success(
            request,
            f"{other_user.username} a été retiré de vos amis."
        )

    return redirect("friend_list")


@login_required
def cancel_friend(request, request_id):
    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        sender=request.user,
        status="pending",
    )
    if request.method == "POST":
        friend_request.delete()
        messages.success(request, "La demande d'ami a été annulée.")
    return redirect("friend_list")