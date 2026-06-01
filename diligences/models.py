from django.db import models
from django.conf import settings


class Diligence(models.Model):
    TYPE_CHOICES = [
        ('courrier', 'Courrier'),
        ('reunion', 'Réunion'),
        ('decision', 'Décision'),
        ('note', 'Note'),
        ('instruction_dg', 'Instruction DG'),
        ('rapport', 'Rapport'),
        ('autre', 'Autre'),
    ]
    PRIORITE_CHOICES = [
        ('urgente', 'Urgente'),
        ('haute', 'Haute'),
        ('normale', 'Normale'),
        ('faible', 'Faible'),
    ]
    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('affectee', 'Affectée'),
        ('en_cours', 'En cours'),
        ('en_attente_controle', 'En attente de contrôle'),
        ('cloturee', 'Clôturée'),
        ('annulee', 'Annulée'),
    ]

    reference = models.CharField(max_length=30, unique=True, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_source = models.CharField(max_length=20, choices=TYPE_CHOICES, default='instruction_dg')
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='ouverte')

    emetteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='diligences_emises'
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dlg_assignees'
    )

    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diligences'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diligences'
    )

    date_echeance = models.DateField(null=True, blank=True)
    date_cloture = models.DateField(null=True, blank=True)
    taux_avancement = models.IntegerField(default=0)

    source_reference = models.CharField(max_length=200, blank=True)
    instructions = models.TextField(blank=True)
    resultat = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='diligences_creees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diligence'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from django.utils import timezone
            count = Diligence.objects.count() + 1
            self.reference = f"DLG-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class SuiviDiligence(models.Model):
    diligence = models.ForeignKey(Diligence, on_delete=models.CASCADE, related_name='suivis')
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='suivis_diligences'
    )
    date_suivi = models.DateField()
    avancement = models.IntegerField(default=0)
    observations = models.TextField()
    actions_realisees = models.TextField(blank=True)
    prochaines_etapes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suivi diligence'
        ordering = ['-date_suivi']

    def __str__(self):
        return f"Suivi {self.diligence.reference} — {self.date_suivi}"


class RelanceDiligence(models.Model):
    diligence = models.ForeignKey(Diligence, on_delete=models.CASCADE, related_name='relances')
    emetteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    message = models.TextField()
    date_relance = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Relance diligence'
        ordering = ['-date_relance']
