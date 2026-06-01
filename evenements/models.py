from django.db import models
from django.conf import settings


class Evenement(models.Model):
    TYPE_CHOICES = [
        ('atelier', 'Atelier'),
        ('seminaire', 'Séminaire'),
        ('formation', 'Formation'),
        ('conference', 'Conférence'),
        ('forum', 'Forum'),
        ('mission', 'Mission'),
        ('reunion', 'Réunion'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('confirme', 'Confirmé'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]

    titre = models.CharField(max_length=300)
    type_evenement = models.CharField(max_length=15, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifie')
    description = models.TextField(blank=True)

    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    lieu = models.CharField(max_length=300, blank=True)
    lieu_details = models.TextField(blank=True)

    organisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='evv_organises'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evv_evenements'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evv_evenements'
    )

    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    nombre_participants_prevu = models.IntegerField(default=0)

    objectifs = models.TextField(blank=True)
    ordre_du_jour = models.TextField(blank=True)
    resultats_attendus = models.TextField(blank=True)
    compte_rendu = models.TextField(blank=True)

    avec_inscription = models.BooleanField(default=False)
    avec_presence_qr = models.BooleanField(default=False)
    avec_evaluation = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='evv_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Événement'
        ordering = ['-date_debut']

    def __str__(self):
        return f"[{self.get_type_evenement_display()}] {self.titre}"

    @property
    def nb_participants(self):
        return self.participants.filter(statut='confirme').count()


class ParticipantEvenement(models.Model):
    STATUT_CHOICES = [
        ('invite', 'Invité'),
        ('confirme', 'Confirmé'),
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('annule', 'Annulé'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='participants')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evv_participations'
    )
    nom = models.CharField(max_length=200, blank=True)
    prenom = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    organisation = models.CharField(max_length=200, blank=True)
    fonction = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=20, blank=True)

    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='invite')
    date_confirmation = models.DateTimeField(null=True, blank=True)
    date_presence = models.DateTimeField(null=True, blank=True)
    qr_code = models.CharField(max_length=100, blank=True)

    note_evaluation = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    commentaire_evaluation = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Participant'
        unique_together = ['evenement', 'email']
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} — {self.evenement.titre}"


class DepenseEvenement(models.Model):
    CATEGORIE_CHOICES = [
        ('location_salle', 'Location salle'),
        ('restauration', 'Restauration'),
        ('transport', 'Transport'),
        ('materiel', 'Matériel'),
        ('communication', 'Communication'),
        ('honoraires', 'Honoraires'),
        ('autre', 'Autre'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='depenses')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    description = models.CharField(max_length=300)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    fournisseur = models.CharField(max_length=200, blank=True)
    date_depense = models.DateField()
    facture_ref = models.CharField(max_length=100, blank=True)

    saisi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dépense événement'
        ordering = ['-date_depense']

    def __str__(self):
        return f"{self.evenement.titre} — {self.description}: {self.montant}"
