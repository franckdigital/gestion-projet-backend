from django.db import models
from django.conf import settings
from django.utils import timezone


class PlanPassationMarche(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'), ('valide', 'Validé'),
        ('publie', 'Publié'), ('archive', 'Archivé'),
    ]
    annee = models.IntegerField()
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='plans_passation')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='plans_passation')
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    budget_total_prevu = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='plans_passation_crees')
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='plans_passation_valides')
    date_validation = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plan de passation des marchés'
        ordering = ['-annee', 'titre']

    def __str__(self):
        return f"PPM {self.annee} — {self.titre}"


class DemandeAchat(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'), ('soumise', 'Soumise'),
        ('en_validation', 'En validation'), ('validee', 'Validée'),
        ('rejetee', 'Rejetée'), ('traitee', 'Traitée'),
    ]
    PRIORITE_CHOICES = [
        ('normale', 'Normale'), ('urgente', 'Urgente'), ('tres_urgente', 'Très urgente'),
    ]
    TYPE_MARCHE_CHOICES = [
        ('fournitures', 'Fournitures'), ('services', 'Services'),
        ('travaux', 'Travaux'), ('consultance', 'Consultance'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField()
    type_marche = models.CharField(max_length=15, choices=TYPE_MARCHE_CHOICES, default='fournitures')
    priorite = models.CharField(max_length=15, choices=PRIORITE_CHOICES, default='normale')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='demandes_achat')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='demandes_achat')
    plan_passation = models.ForeignKey(PlanPassationMarche, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='demandes')
    budget_estime = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_besoin = models.DateField(null=True, blank=True)
    justification = models.TextField(blank=True)
    specifications_techniques = models.TextField(blank=True)
    demandeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='demandes_achat')
    valideur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='demandes_achat_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demande d'achat"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = DemandeAchat.objects.count() + 1
            self.reference = f"DA-{timezone.now().year}-{count:05d}"
        super().save(*args, **kwargs)


class AppelOffre(models.Model):
    TYPE_CHOICES = [
        ('appel_offres_ouvert', "Appel d'offres ouvert"),
        ('appel_offres_restreint', "Appel d'offres restreint"),
        ('consultation_restreinte', 'Consultation restreinte'),
        ('entente_directe', 'Entente directe'),
        ('gre_a_gre', 'Gré à gré'),
    ]
    STATUT_CHOICES = [
        ('preparation', 'En préparation'), ('publie', 'Publié'),
        ('ouvert', 'Ouvert aux offres'), ('evaluation', 'En évaluation'),
        ('attribue', 'Attribué'), ('annule', 'Annulé'), ('infructueux', 'Infructueux'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField()
    type_marche = models.CharField(max_length=25, choices=TYPE_CHOICES, default='appel_offres_ouvert')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='preparation')
    demande_achat = models.OneToOneField(DemandeAchat, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='appel_offre')
    plan_passation = models.ForeignKey(PlanPassationMarche, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='appels_offre')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='appels_offre')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='appels_offre')
    budget_estime = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_publication = models.DateField(null=True, blank=True)
    date_limite_soumission = models.DateField(null=True, blank=True)
    date_ouverture_plis = models.DateField(null=True, blank=True)
    lieu_depot = models.CharField(max_length=300, blank=True)
    criteres_evaluation = models.TextField(blank=True)
    documents_requis = models.JSONField(default=list, blank=True)
    fichier_dao = models.FileField(upload_to='marches/dao/%Y/', null=True, blank=True)
    nb_lots = models.IntegerField(default=1)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     related_name='appels_offre_responsable')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Appel d'offres"
        ordering = ['-date_publication', '-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = AppelOffre.objects.count() + 1
            self.reference = f"AO-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class SoumissionnaireOffre(models.Model):
    STATUT_CHOICES = [
        ('soumis', 'Soumis'), ('conforme', 'Conforme'),
        ('non_conforme', 'Non conforme'), ('qualifie', 'Qualifié'),
        ('selectionne', 'Sélectionné'), ('rejete', 'Rejeté'),
    ]

    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.CASCADE, related_name='soumissionnaires')
    nom_entreprise = models.CharField(max_length=300)
    pays = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    montant_offre = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    date_soumission = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='soumis')
    note_technique = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    note_financiere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    note_globale = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    poids_technique = models.DecimalField(max_digits=4, decimal_places=2, default=70)
    poids_financier = models.DecimalField(max_digits=4, decimal_places=2, default=30)
    observations = models.TextField(blank=True)
    fichier_offre = models.FileField(upload_to='marches/offres/%Y/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Soumissionnaire"
        ordering = ['-note_globale']

    def __str__(self):
        return f"{self.nom_entreprise} — {self.appel_offre.reference}"

    def calculer_note_globale(self):
        if self.note_technique is not None and self.note_financiere is not None:
            pt = float(self.poids_technique) / 100
            pf = float(self.poids_financier) / 100
            self.note_globale = float(self.note_technique) * pt + float(self.note_financiere) * pf
            self.save(update_fields=['note_globale'])
        return self.note_globale


class ContratMarche(models.Model):
    STATUT_CHOICES = [
        ('en_preparation', 'En préparation'), ('signe', 'Signé'),
        ('en_cours', 'En cours'), ('suspendu', 'Suspendu'),
        ('resilie', 'Résilié'), ('solde', 'Soldé'), ('archive', 'Archivé'),
    ]
    TYPE_CHOICES = [
        ('fournitures', 'Fournitures'), ('services', 'Services'),
        ('travaux', 'Travaux'), ('consultance', 'Consultance'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    type_contrat = models.CharField(max_length=15, choices=TYPE_CHOICES, default='services')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_preparation')
    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='contrats')
    soumissionnaire = models.ForeignKey(SoumissionnaireOffre, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='contrats')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='contrats_marche')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='contrats_marche')
    prestataire_nom = models.CharField(max_length=300)
    prestataire_contact = models.CharField(max_length=200, blank=True)
    prestataire_email = models.EmailField(blank=True)
    montant_ttc = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    devise = models.CharField(max_length=5, default='XOF')
    montant_realise = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_signature = models.DateField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    objet = models.TextField()
    conditions_paiement = models.TextField(blank=True)
    garanties = models.TextField(blank=True)
    penalites = models.TextField(blank=True)
    fichier_contrat = models.FileField(upload_to='marches/contrats/%Y/', null=True, blank=True)
    notes = models.TextField(blank=True)
    gestionnaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                      related_name='contrats_geres')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contrat marché'
        ordering = ['-date_signature', '-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre} — {self.prestataire_nom}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = ContratMarche.objects.count() + 1
            self.reference = f"CTR-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def taux_execution(self):
        if not self.montant_ttc:
            return 0
        return round(float(self.montant_realise) / float(self.montant_ttc) * 100, 1)

    @property
    def est_en_retard(self):
        return (
            self.date_fin_prevue and
            self.date_fin_prevue < timezone.now().date() and
            self.statut in ('signe', 'en_cours')
        )


class AvenantContrat(models.Model):
    MOTIF_CHOICES = [
        ('extension_delai', 'Extension de délai'),
        ('augmentation_montant', 'Augmentation de montant'),
        ('modification_scope', 'Modification du périmètre'),
        ('autre', 'Autre'),
    ]

    contrat = models.ForeignKey(ContratMarche, on_delete=models.CASCADE, related_name='avenants')
    numero_avenant = models.IntegerField()
    motif = models.CharField(max_length=25, choices=MOTIF_CHOICES, default='autre')
    description = models.TextField()
    montant_supplementaire = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    nouveau_montant_ttc = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    extension_jours = models.IntegerField(default=0)
    nouvelle_date_fin = models.DateField(null=True, blank=True)
    date_signature = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=15,
        choices=[('en_preparation', 'En préparation'), ('signe', 'Signé')],
        default='en_preparation'
    )
    fichier = models.FileField(upload_to='marches/avenants/%Y/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avenant contrat'
        unique_together = ['contrat', 'numero_avenant']
        ordering = ['numero_avenant']

    def __str__(self):
        return f"Avenant n°{self.numero_avenant} — {self.contrat.reference}"
