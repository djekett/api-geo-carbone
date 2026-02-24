from django.db import models
from django.conf import settings


class RequeteNLP(models.Model):
    """Journal des requetes en langage naturel."""

    texte_requete = models.TextField(verbose_name='Requete utilisateur')
    entites_extraites = models.JSONField(
        default=dict, blank=True,
        verbose_name='Entites extraites',
    )
    filtre_orm = models.TextField(
        blank=True, default='',
        verbose_name='Filtre ORM genere',
    )
    nombre_resultats = models.IntegerField(
        default=0,
        verbose_name='Nombre de resultats',
    )
    temps_traitement_ms = models.IntegerField(
        null=True, blank=True,
        verbose_name='Temps de traitement (ms)',
    )
    session_id = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='ID de session',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Requete NLP'
        verbose_name_plural = 'Requetes NLP'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.texte_requete[:50]}... ({self.created_at:%Y-%m-%d %H:%M})"
