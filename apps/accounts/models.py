from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrateur SIG'
        OBSERVATEUR = 'observateur', 'Observateur'
        VISITEUR = 'visiteur', 'Visiteur'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VISITEUR,
        verbose_name='Role',
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin_sig(self):
        return self.role == self.Role.ADMIN or self.is_superuser
