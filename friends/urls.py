from django.urls import path
from . import views

urlpatterns = [
    path("", views.friend_list, name="friend_list"),
    path("requests/", views.friend_requests, name="friend_requests"),
    path("add/<int:user_id>/", views.add_friend, name="add_friend"),
    path(
        "accept/<int:request_id>/",
        views.accept_friend,
        name="accept_friend"
    ),
    path(
        "reject/<int:request_id>/",
        views.reject_friend,
        name="reject_friend"
    ),
    path(
        "remove/<int:user_id>/",
        views.remove_friend,
        name="remove_friend"
    ),
    path("cancel/<int:request_id>/", views.cancel_friend, name="cancel_friend"),
]