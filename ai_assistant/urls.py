from django.urls import path

from . import views

urlpatterns = [
    path("", views.ai_chat, name="ai_chat"),
    path("api/", views.ai_chat_api, name="ai_chat_api"),
    path("clear/", views.clear_ai_chat, name="clear_ai_chat"),
]