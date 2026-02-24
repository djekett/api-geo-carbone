from django.db import models
from django.conf import settings


class ImportSession(models.Model):
    """Suivi des sessions d'import de Shapefiles."""

    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours'),
        ('COMPLETED', 'Termine'),
        ('FAILED', 'Echoue'),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Utilisateur',
    )
    fichier_nom = models.CharField(max_length=255, verbose_name='Nom du fichier')
    fichier = models.FileField(
        upload_to='imports/shapefiles/',
        verbose_name='Fichier ZIP',
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Statut',
    )
    mapping_colonnes = models.JSONField(
        default=dict, blank=True,
        verbose_name='Mapping des colonnes',
    )
    colonnes_detectees = models.JSONField(
        default=list, blank=True,
        verbose_name='Colonnes detectees',
    )
    nombre_features = models.IntegerField(default=0, verbose_name='Nombre de features')
    nombre_importees = models.IntegerField(default=0, verbose_name='Features importees')
    nombre_erreurs = models.IntegerField(default=0, verbose_name='Erreurs')
    rapport = models.TextField(blank=True, default='', verbose_name='Rapport')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Session d'import"
        verbose_name_plural = "Sessions d'import"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.fichier_nom} - {self.get_statut_display()} ({self.created_at:%Y-%m-%d})"
