from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html", email_template_name="accounts/password_reset_email.txt", subject_template_name="accounts/password_reset_subject.txt", success_url="/password-reset/done/"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html", success_url="/reset/done/"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/<str:username>/", views.profile, name="user_profile"),
    path("settings/", views.settings_view, name="settings"),
    path("search/", views.user_search, name="user_search"),
]