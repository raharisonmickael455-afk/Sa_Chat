from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from friends.models import FriendRequest
from posts.models import Post
from .models import Badge, Collection, Event, EventParticipant, Group, GroupMembership, Reaction, SavedPost, Story, UserBadge


def friend_ids(user):
    rows = FriendRequest.objects.filter(Q(sender=user) | Q(receiver=user), status="accepted").values_list("sender_id", "receiver_id")
    ids = set()
    for sender_id, receiver_id in rows:
        ids.update((sender_id, receiver_id))
    return ids - {user.id}


@login_required
def dashboard(request):
    posts = Post.objects.filter(Q(author=request.user) | Q(author_id__in=friend_ids(request.user)) | Q(visibility="public")).annotate(activity=Count("likes") + Count("comments")).order_by("-activity", "-created_at")[:10]
    stats = {"posts": request.user.posts.count(), "friends": FriendRequest.objects.filter(Q(sender=request.user) | Q(receiver=request.user), status="accepted").count(), "likes": request.user.post_likes.count(), "comments": request.user.comments.count()}
    return render(request, "social/dashboard.html", {"posts": posts, "stats": stats, "badges": request.user.badges.select_related("badge")})


@login_required
def story_list(request):
    now = timezone.now()
    stories = Story.objects.filter(expires_at__gt=now).select_related("author")
    return render(request, "social/stories.html", {"stories": stories})


@login_required
def create_story(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        video = request.FILES.get("video")
        text = request.POST.get("text", "").strip()
        if not image and not video and not text:
            messages.error(request, "Une story doit contenir un texte ou un média.")
            return redirect("story_list")
        Story.objects.create(author=request.user, text=text, image=image, video=video, expires_at=timezone.now() + timedelta(hours=24))
        messages.success(request, "Story publiée pour 24 heures.")
    return redirect("story_list")


@login_required
@require_POST
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id, author=request.user)
    story.delete()
    messages.success(request, "La story a été supprimée.")
    return redirect("story_list")


@login_required
def react(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        reaction_type = request.POST.get("reaction_type", "like")
        if reaction_type not in dict(Reaction.TYPES):
            reaction_type = "like"
        reaction, created = Reaction.objects.get_or_create(post=post, user=request.user, defaults={"reaction_type": reaction_type})
        if not created:
            if reaction.reaction_type == reaction_type:
                reaction.delete()
            else:
                reaction.reaction_type = reaction_type
                reaction.save(update_fields=["reaction_type"])
    return redirect(request.POST.get("next") or "post_list")


@login_required
def collections(request):
    items = request.user.collections.prefetch_related("saved_posts__post__author")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Collection.objects.create(owner=request.user, name=name)
    return render(request, "social/collections.html", {"collections": items})


@login_required
@require_POST
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    collection, _ = Collection.objects.get_or_create(owner=request.user, name="À lire")
    saved_post = SavedPost.objects.filter(collection=collection, post=post).first()
    if saved_post:
        saved_post.delete()
        status = "removed"
        message = "Publication retirée de vos sauvegardes."
    else:
        SavedPost.objects.create(collection=collection, post=post)
        status = "saved"
        message = "Publication enregistrée dans votre collection."
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"saved": status == "saved", "count": SavedPost.objects.filter(collection=collection).count()})
    messages.success(request, message)
    return redirect(request.POST.get("next") or "post_list")


@login_required
def group_list(request):
    groups = Group.objects.annotate(member_count=Count("members")).order_by("-created_at")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if name:
            group = Group.objects.create(owner=request.user, name=name, description=description)
            GroupMembership.objects.create(group=group, user=request.user, is_admin=True)
            return redirect("group_list")
    return render(request, "social/groups.html", {"groups": groups})


@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    GroupMembership.objects.get_or_create(group=group, user=request.user)
    return redirect("group_list")


@login_required
def event_list(request):
    events = Event.objects.select_related("creator").annotate(attendee_count=Count("attendees")).order_by("starts_at")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        starts_at = request.POST.get("starts_at")
        starts_at_value = parse_datetime(starts_at or "")
        if starts_at_value and timezone.is_naive(starts_at_value):
            starts_at_value = timezone.make_aware(starts_at_value)
        if title and starts_at_value:
            Event.objects.create(creator=request.user, title=title, description=request.POST.get("description", ""), location=request.POST.get("location", ""), starts_at=starts_at_value)
            return redirect("event_list")
    return render(request, "social/events.html", {"events": events})


@login_required
def join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    EventParticipant.objects.get_or_create(event=event, user=request.user)
    return redirect("event_list")


@login_required
def award_badges(request):
    badge, _ = Badge.objects.get_or_create(name="Membre actif", defaults={"description": "A publié sur Sa Chat", "icon": "★"})
    if request.user.posts.exists():
        UserBadge.objects.get_or_create(user=request.user, badge=badge)
    return redirect("dashboard")


@login_required
def search_api(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10] if query else User.objects.none()
    return JsonResponse({"results": [{"username": user.username, "url": f"/profile/{user.username}/"} for user in users]})
