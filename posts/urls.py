from django.urls import path

from . import views


urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("archived/", views.archived_posts, name="archived_posts"),

    path(
        "create/",
        views.create_post,
        name="create_post"
    ),

    path(
        "<int:post_id>/",
        views.post_detail,
        name="post_detail"
    ),

    path(
        "<int:post_id>/edit/",
        views.edit_post,
        name="edit_post"
    ),

    path(
        "<int:post_id>/delete/",
        views.delete_post,
        name="delete_post"
    ),
    path(
        "<int:post_id>/visibility/",
        views.change_post_visibility,
        name="change_post_visibility",
    ),
    path(
        "<int:post_id>/archive/",
        views.toggle_archive,
        name="toggle_archive",
    ),
    path("<int:post_id>/like/", views.toggle_like, name="toggle_like"),
    path("videos/", views.video_list, name="video_list"),
    path("videos/<int:post_id>/", views.video_detail, name="video_detail"),
    path("<int:post_id>/comment/", views.create_comment, name="create_comment"),
    path("comments/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path("comments/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("<int:post_id>/share/", views.share_post, name="share_post"),
]