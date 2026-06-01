from django.db import models
from django.conf import settings


class NonConformite(models.Model):
    TYPE_CHOICES = [
        ('processus', 'Processus'),
        ('produit', 'Produit'),
        ('service', 'Service'),
        ('documentation', 'Documentation'),
        ('ressources', 'Ressources'),
        ('autre', 'Autre'),
    ]
    GRAVITE_CHOICES = [
        ('mineure', 'Mineure'),
        ('majeure', 'Majeure'),
        ('critique', 'Critique'),
    ]
    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('en_traitement', 'En traitement'),
        ('cloturee', 'Clôturée'),
        ('verifiee', 'Vérifiée'),
    ]

    reference = models.CharField(max_length=30, unique=True, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField()
    type_nc = models.CharField(max_length=20, choices=TYPE_CHOICES)
    gravite = models.CharField(max_length=10, choices=GRAVITE_CHOICES, default='mineure')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='ouverte')

    detecte_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='nc_detectees'
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='nc_responsable'
    )

    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True
    )

    date_detection = models.DateField()
    date_echeance = models.DateField(null=True, blank=True)
    date_cloture = models.DateField(null=True, blank=True)

    cause_racine = models.TextField(blank=True)
    impact = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Non-conformité'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from django.utils import timezone
            count = NonConformite.objects.count() + 1
            self.reference = f"NC-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class ActionQualite(models.Model):
    TYPE_CHOICES = [
        ('corrective', 'Action Corrective'),
        ('preventive', 'Action Préventive'),
        ('amelioration', "Action d'Amélioration"),
    ]
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('realisee', 'Réalisée'),
        ('verifiee', 'Vérifiée'),
        ('cloturee', 'Clôturée'),
    ]

    non_conformite = models.ForeignKey(
        NonConformite, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='actions'
    )
    type_action = models.CharField(max_length=15, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=300)
    description = models.TextField()
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='actions_qualite'
    )
    date_prevue = models.DateField(null=True, blank=True)
    date_realisation = models.DateField(null=True, blank=True)
    resultat = models.TextField(blank=True)
    efficace = models.BooleanField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='actions_qualite_creees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Action qualité'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_action_display()}] {self.titre}"


class AuditInterne(models.Model):
    TYPE_CHOICES = [
        ('processus', 'Audit processus'),
        ('systeme', 'Audit système'),
        ('produit', 'Audit produit'),
        ('conformite', 'Audit conformité'),
    ]
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('cloture', 'Clôturé'),
    ]

    reference = models.CharField(max_length=30, unique=True, blank=True)
    titre = models.CharField(max_length=300)
    type_audit = models.CharField(max_length=15, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='planifie')

    auditeur_principal = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='audits_conduits'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True
    )

    date_planifiee = models.DateField()
    date_realisation = models.DateField(null=True, blank=True)
    perimetre = models.TextField(blank=True)
    criteres = models.TextField(blank=True)
    nb_nc_majeures = models.IntegerField(default=0)
    nb_nc_mineures = models.IntegerField(default=0)
    nb_observations = models.IntegerField(default=0)
    rapport = models.TextField(blank=True)
    conclusions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Audit interne'
        ordering = ['-date_planifiee']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from django.utils import timezone
            count = AuditInterne.objects.count() + 1
            self.reference = f"AUD-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class IndicateurQualite(models.Model):
    FREQUENCE_CHOICES = [
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'),
        ('annuelle', 'Annuelle'),
    ]

    code = models.CharField(max_length=20, unique=True)
    intitule = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    unite = models.CharField(max_length=50)
    valeur_cible = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    valeur_actuelle = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    frequence_mesure = models.CharField(max_length=15, choices=FREQUENCE_CHOICES, default='mensuelle')
    actif = models.BooleanField(default=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Indicateur qualité'
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.intitule}"
