from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("stories/", views.story_list, name="story_list"),
    path("stories/create/", views.create_story, name="create_story"),
    path("stories/<int:story_id>/delete/", views.delete_story, name="delete_story"),
    path("react/<int:post_id>/", views.react, name="react_post"),
    path("collections/", views.collections, name="collections"),
    path("save/<int:post_id>/", views.save_post, name="save_post"),
    path("groups/", views.group_list, name="group_list"),
    path("groups/<int:group_id>/join/", views.join_group, name="join_group"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:event_id>/join/", views.join_event, name="join_event"),
    path("badges/award/", views.award_badges, name="award_badges"),
    path("search-api/", views.search_api, name="search_api"),
]
