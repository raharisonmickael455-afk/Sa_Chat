from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from friends.models import FriendRequest
from notifications.models import Notification
from social.models import Story
from .models import Comment, Like, Post, Share

VALID_VISIBILITIES = {"public", "friends", "private"}


def friend_ids(user):
    relations = FriendRequest.objects.filter(
        Q(sender=user, status="accepted") | Q(receiver=user, status="accepted")
    )
    return list(set(relations.values_list("sender_id", flat=True)) | set(
        relations.values_list("receiver_id", flat=True)
    ))


def visible_posts(user):
    return Post.objects.filter(
        Q(is_archived=False),
    ).filter(
        Q(author=user)
        | Q(visibility="public")
        | Q(visibility="friends", author_id__in=friend_ids(user))
    ).select_related("author").prefetch_related("likes", "comments__author")


def validate_upload(upload, max_size):
    return upload is None or upload.size <= max_size


@login_required
def post_list(request):
    posts = visible_posts(request.user)
    liked_post_ids = set(Like.objects.filter(
        user=request.user, post__in=posts
    ).values_list("post_id", flat=True))
    user_reactions = {
        like.post_id: like.reaction_type
        for like in Like.objects.filter(user=request.user, post__in=posts)
    }
    active_story_groups = []
    active_stories = Story.objects.filter(expires_at__gt=timezone.now()).select_related("author", "author__profile").order_by("author_id", "created_at")
    grouped = {}
    for story in active_stories:
        grouped.setdefault(story.author_id, []).append(story)
    for author_id, stories in grouped.items():
        author = stories[0].author
        active_story_groups.append({
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

    return render(
        request,
        "posts/post_list.html",
        {
            "posts": posts,
            "liked_post_ids": liked_post_ids,
            "user_reactions": user_reactions,
            "story_user_ids": list(Story.objects.filter(expires_at__gt=timezone.now()).values_list("author_id", flat=True)),
            "story_groups": active_story_groups,
            "shares": Share.objects.filter(
                Q(author=request.user) | Q(visibility="public") |
                Q(visibility="friends", author_id__in=friend_ids(request.user)),
                original_post__is_archived=False,
            ).select_related("author", "original_post__author")
        }
    )


@login_required
def archived_posts(request):
    posts = Post.objects.filter(author=request.user, is_archived=True).select_related("author")
    return render(request, "posts/archived_posts.html", {"posts": posts})


@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        image = request.FILES.get("image")
        video = request.FILES.get("video")

        if not content and not image and not video:
            messages.error(
                request,
                "Votre publication ne peut pas être vide."
            )
            return redirect("create_post")
        if video and not validate_upload(video, 50 * 1024 * 1024):
            messages.error(request, "La vidéo ne doit pas dépasser 50 Mo.")
            return redirect("create_post")

        visibility = request.POST.get("visibility", "public")
        if visibility not in VALID_VISIBILITIES:
            visibility = "public"
        Post.objects.create(
            author=request.user,
            content=content,
            image=image,
            video=video,
            visibility=visibility,
        )

        messages.success(
            request,
            "Publication créée avec succès."
        )

        return redirect("post_list")

    return render(
        request,
        "posts/create_post.html"
    )


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(
        visible_posts(request.user),
        id=post_id
    )

    return render(
        request,
        "posts/post_detail.html",
        {
            "post": post,
            "comments": post.comments.filter(parent__isnull=True).select_related("author").prefetch_related("replies__author"),
            "user_liked": post.likes.filter(user=request.user).exists(),
        }
    )


@login_required
def video_list(request):
    videos = visible_posts(request.user).exclude(video__isnull=True).exclude(video="")
    return render(request, "posts/video_list.html", {"videos": videos})


@login_required
def video_detail(request, post_id):
    video = get_object_or_404(
        visible_posts(request.user).exclude(video__isnull=True).exclude(video=""),
        id=post_id,
    )
    return render(request, "posts/video_detail.html", {"video": video})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        author=request.user
    )

    if request.method == "POST":
        content = request.POST.get("content", "").strip()

        if not content and not post.image:
            messages.error(
                request,
                "La publication ne peut pas être vide."
            )
            return redirect("edit_post", post_id=post.id)

        post.content = content
        visibility = request.POST.get("visibility", post.visibility)
        post.visibility = visibility if visibility in VALID_VISIBILITIES else post.visibility

        if request.FILES.get("image"):
            post.image = request.FILES.get("image")
        if request.FILES.get("video"):
            video = request.FILES["video"]
            if not validate_upload(video, 50 * 1024 * 1024):
                messages.error(request, "La vidéo ne doit pas dépasser 50 Mo.")
                return redirect("edit_post", post_id=post.id)
            post.video = video

        post.save()

        messages.success(
            request,
            "Publication modifiée avec succès."
        )

        return redirect(
            "post_detail",
            post_id=post.id
        )

    return render(
        request,
        "posts/edit_post.html",
        {"post": post}
    )


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        author=request.user
    )

    if request.method == "POST":
        post.delete()

        messages.success(
            request,
            "Publication supprimée."
        )

        return redirect("post_list")

    return render(
        request,
        "posts/delete_post.html",
        {"post": post}
    )


@login_required
@require_POST
def change_post_visibility(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    visibility = request.POST.get("visibility", "")
    if visibility in VALID_VISIBILITIES:
        post.visibility = visibility
        post.save(update_fields=["visibility", "updated_at"])
        messages.success(request, "Confidentialité de la publication mise à jour.")
    else:
        messages.error(request, "Confidentialité invalide.")
    return redirect(request.POST.get("next") or "post_list")


@login_required
@require_POST
def toggle_archive(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.is_archived = not post.is_archived
    post.save(update_fields=["is_archived", "updated_at"])
    messages.success(
        request,
        "Publication archivée." if post.is_archived else "Publication restaurée.",
    )
    return redirect(request.POST.get("next") or "post_list")


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(visible_posts(request.user), id=post_id)
    reaction_type = request.POST.get("reaction_type", "like")
    if reaction_type not in dict(Like.REACTION_CHOICES):
        reaction_type = "like"

    current_like = Like.objects.filter(post=post, user=request.user).first()
    liked = False
    response_reaction = None
    notify = False

    if current_like is None:
        Like.objects.create(post=post, user=request.user, reaction_type=reaction_type)
        liked = True
        response_reaction = reaction_type
        notify = post.author != request.user
    elif current_like.reaction_type == reaction_type:
        current_like.delete()
        liked = False
        response_reaction = None
    else:
        current_like.reaction_type = reaction_type
        current_like.save(update_fields=["reaction_type"])
        liked = True
        response_reaction = reaction_type
        notify = post.author != request.user

    if notify and liked:
        Notification.objects.create(
            user=post.author,
            actor=request.user,
            notification_type="like",
            message=f"{request.user.username} a aimé votre publication.",
            related_post=post,
        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "liked": liked,
            "reaction": response_reaction,
            "count": Like.objects.filter(post=post).count(),
        })
    return redirect(request.POST.get("next") or "post_list")


@login_required
@require_POST
def create_comment(request, post_id):
    post = get_object_or_404(visible_posts(request.user), id=post_id)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            parent = None
            parent_id = request.POST.get("parent_id", "")
            if parent_id.isdigit():
                parent = post.comments.filter(id=parent_id, parent__isnull=True).first()
            Comment.objects.create(post=post, author=request.user, content=content, parent=parent)
            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    actor=request.user,
                    notification_type="comment",
                    message=f"{request.user.username} a commenté votre publication.",
                    related_post=post,
                )

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("post_detail", post_id=post.id)


@login_required
@require_POST
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            comment.content = content
            comment.save(update_fields=["content", "updated_at"])
    return redirect("post_detail", post_id=comment.post_id)


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    post_id = comment.post_id
    if request.method == "POST":
        comment.delete()
    return redirect("post_detail", post_id=post_id)


@login_required
@require_POST
def share_post(request, post_id):
    post = get_object_or_404(visible_posts(request.user), id=post_id)
    if request.method == "POST":
        visibility = request.POST.get("visibility", "friends")
        if visibility not in VALID_VISIBILITIES:
            visibility = "friends"
        if post.visibility == "private":
            visibility = "private"
        elif post.visibility == "friends" and visibility == "public":
            visibility = "friends"
        share = Share.objects.create(
            original_post=post,
            author=request.user,
            visibility=visibility,
        )
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                actor=request.user,
                notification_type="share",
                message=f"{request.user.username} a partagé votre publication.",
                related_post=post,
            )
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"shared": True, "count": post.shares.count(), "visibility": visibility, "share_id": share.id})
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"shared": False, "count": post.shares.count()})
    return redirect(request.POST.get("next") or "post_list")