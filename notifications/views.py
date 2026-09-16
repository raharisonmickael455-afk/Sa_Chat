from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).select_related(
        "actor", "related_post", "friend_request", "message_request"
    )
    return render(request, "notifications/notifications_list.html", {"notifications": notifications})


@login_required
def open_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect(notification.get_target_url())


@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if request.method == "POST":
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect("notification_list")


@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if request.method == "POST":
        notification.delete()
    return redirect("notification_list")


@login_required
def mark_all_as_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notification_list")