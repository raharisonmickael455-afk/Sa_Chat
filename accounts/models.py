from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
	bio = models.TextField(blank=True)
	presentation = models.CharField(max_length=180, blank=True)
	interests = models.CharField(max_length=500, blank=True)
	theme = models.CharField(max_length=20, choices=[("light", "Clair"), ("dark", "Sombre")], default="light")
	avatar = models.ImageField(upload_to="profiles/", blank=True, null=True)
	is_private = models.BooleanField(default=False)

	def __str__(self):
		return f"Profil de {self.user.username}"
