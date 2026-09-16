"""
URL configuration for sa_chat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from ai_assistant import views as ai_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path("", include("accounts.urls")),
    path("posts/", include("posts.urls")),
    path("friends/", include("friends.urls")),
    path("notifications/", include("notifications.urls")),
    path("messages/", include("chat.urls")),
    path("social/", include("social.urls")),
    path("ai/", include("ai_assistant.urls")),
    path("api/ai/chat/", ai_views.ai_chat_api, name="api_ai_chat"),
    path("api/ai/clear/", ai_views.clear_ai_chat, name="api_clear_ai_chat"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)