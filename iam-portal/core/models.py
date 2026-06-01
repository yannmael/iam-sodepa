"""Modèles locaux du portail IAM — complément aux logs Keycloak."""
from django.db import models


class AuditLog(models.Model):
    """Trace locale des actions administratives effectuées via le portail."""

    ACTION_CHOICES = [
        ('USER_CREATE', 'Création utilisateur'),
        ('USER_UPDATE', 'Modification utilisateur'),
        ('USER_DELETE', 'Suppression utilisateur'),
        ('ROLE_ASSIGN', 'Attribution de rôle'),
        ('ROLE_REMOVE', 'Retrait de rôle'),
        ('APP_ACCESS', 'Accès application'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    operator = models.CharField(max_length=150, help_text="Username de l'admin ayant effectué l'action")
    target = models.CharField(max_length=150, blank=True, help_text="Username ou ID de la cible")
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log d\'audit'
        verbose_name_plural = 'Logs d\'audit'

    def __str__(self):
        return f"{self.timestamp:%d/%m/%Y %H:%M} — {self.action} par {self.operator}"
