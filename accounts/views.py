from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from friends.models import FriendRequest
from notifications.models import Notification
from posts.models import Post
from posts.views import visible_posts
from social.models import Story
from .models import Profile


@login_required
def home(request):
    context = {}
    if request.user.is_authenticated:
        story_groups = []
        active_stories = Story.objects.filter(expires_at__gt=timezone.now()).select_related("author", "author__profile").order_by("author_id", "created_at")
        grouped = {}
        for story in active_stories:
            grouped.setdefault(story.author_id, []).append(story)
        for author_id, stories in grouped.items():
            author = stories[0].author
            story_groups.append({
                "author_id": author.id,
                "author_name": author.username,
                "avatar_url": getattr(getattr(author, "profile", None), "avatar", None).url if getattr(getattr(author, "profile", None), "avatar", None) else "",
                "stories": [{
                    "id": story.id,
                    "text": story.text,
                    "image": story.image.url if story.image else "",
                    "video": story.video.url if story.video else "",
                    "created_at": story.created_at.isoformat(),
                    "expires_at": story.expires_at.isoformat(),
                } for story in stories],
            })
        context = {
            "post_count": Post.objects.filter(author=request.user).count(),
            "friend_count": FriendRequest.objects.filter(
                Q(sender=request.user) | Q(receiver=request.user),
                status="accepted",
            ).count(),
            "unread_notification_count": Notification.objects.filter(
                user=request.user, is_read=False
            ).count(),
            "feed_posts": visible_posts(request.user)[:10],
            "story_groups": story_groups,
        }
        related_ids = FriendRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).values_list("sender_id", "receiver_id")
        excluded_ids = {request.user.id}
        for sender_id, receiver_id in related_ids:
            excluded_ids.update((sender_id, receiver_id))
        context["suggestions"] = User.objects.exclude(id__in=excluded_ids)[:5]
    return render(request, "accounts/home.html", context)


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if not username or not email or not password:
            messages.error(request, "Tous les champs sont obligatoires.")
            return render(request, "accounts/register.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Saisissez une adresse e-mail valide.")
            return render(request, "accounts/register.html")

        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, "accounts/register.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        Profile.objects.create(user=user)

        messages.success(request, "Compte créé avec succès.")
        return redirect("login")

    return render(request, "accounts/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(
            request,
            "Nom d'utilisateur ou mot de passe incorrect."
        )

    return render(request, "accounts/login.html")


@login_required
def profile(request, username=None):
    profile_user = request.user if username is None else get_object_or_404(User, username=username)
    profile_data, _ = Profile.objects.get_or_create(user=profile_user)
    is_owner = profile_user == request.user
    relationship = "self" if is_owner else "not_friends"
    if not is_owner:
        relation = FriendRequest.objects.filter(
            Q(sender=request.user, receiver=profile_user)
            | Q(sender=profile_user, receiver=request.user)
        ).first()
        if relation:
            relationship = "friends" if relation.status == "accepted" else (
                "pending_sent" if relation.sender == request.user else "pending_received"
            )
    can_view_details = is_owner or not profile_data.is_private or relationship == "friends"
    if not can_view_details:
        posts = Post.objects.none()
        friend_users = []
        profile_stories = Story.objects.none()
    else:
        posts = Post.objects.filter(author=profile_user).select_related("author")
        profile_stories = Story.objects.filter(
            author=profile_user,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at")
        friends = FriendRequest.objects.filter(
            Q(sender=profile_user) | Q(receiver=profile_user),
            status="accepted",
        ).select_related("sender", "receiver")
        friend_users = [
            item.receiver if item.sender == profile_user else item.sender
            for item in friends
        ]
    return render(request, "accounts/profile.html", {
        "profile_user": profile_user,
        "profile_data": profile_data,
        "is_owner": is_owner,
        "relationship": relationship,
        "can_view_details": can_view_details,
        "posts": posts,
        "friends": friend_users,
        "profile_stories": profile_stories,
    })


@login_required
def settings_view(request):
    profile_data, _ = Profile.objects.get_or_create(user=request.user)
    password_form = PasswordChangeForm(request.user)
    if request.method == "POST" and request.POST.get("form_type") == "profile":
        username = request.POST.get("username", "").strip()
        if username and User.objects.exclude(id=request.user.id).filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return redirect("settings")
        if username:
            request.user.username = username
        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.email = request.POST.get("email", "").strip()
        request.user.save(update_fields=["username", "first_name", "last_name", "email"])
        profile_data.bio = request.POST.get("bio", "").strip()
        profile_data.presentation = request.POST.get("presentation", "").strip()
        profile_data.interests = request.POST.get("interests", "").strip()
        profile_data.theme = request.POST.get("theme", "light") if request.POST.get("theme") in {"light", "dark"} else "light"
        profile_data.is_private = request.POST.get("is_private") == "on"
        if request.FILES.get("avatar"):
            profile_data.avatar = request.FILES["avatar"]
        profile_data.save()
        messages.success(request, "Vos informations ont été mises à jour.")
        return redirect("profile")
    if request.method == "POST" and request.POST.get("form_type") == "password":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a été modifié.")
            return redirect("settings")
    return render(request, "accounts/settings.html", {
        "profile_data": profile_data,
        "password_form": password_form,
    })


@login_required
def user_search(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.none()
    if query:
        users = User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        ).exclude(id=request.user.id)
    results_with_status = []
    for result in users:
        profile_data, _ = Profile.objects.get_or_create(user=result)
        relation = FriendRequest.objects.filter(
            Q(sender=request.user, receiver=result)
            | Q(sender=result, receiver=request.user)
        ).first()
        status = "not_friends"
        request_id = None
        if relation:
            request_id = relation.id
            status = "friends" if relation.status == "accepted" else (
                "pending_sent" if relation.sender == request.user else "pending_received"
            )
        results_with_status.append({"user": result, "profile": profile_data, "status": status, "request_id": request_id})
    return render(request, "accounts/search.html", {
        "query": query,
        "results": results_with_status,
    })


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")
