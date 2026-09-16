from django.urls import path
from . import views

urlpatterns = [
    path("", views.conversation_list, name="conversation_list"),
    path("start/<int:user_id>/", views.start_conversation, name="start_conversation"),
    path("requests/<int:request_id>/accept/", views.accept_message_request, name="accept_message_request"),
    path("requests/<int:request_id>/reject/", views.reject_message_request, name="reject_message_request"),
    path(
        "share-post/<int:post_id>/",
        views.share_post_to_conversation,
        name="share_post_to_conversation",
    ),
    path("<int:conversation_id>/", views.conversation, name="conversation"),
]
