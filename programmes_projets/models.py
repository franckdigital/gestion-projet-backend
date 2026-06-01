from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class ZoneIntervention(models.Model):
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    pays = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Zone d'intervention"
        ordering = ['pays', 'nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"


class Programme(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('en_preparation', 'En préparation'),
        ('en_cours', 'En cours'),
        ('suspendu', 'Suspendu'),
        ('termine', 'Terminé'),
        ('cloture', 'Clôturé'),
        ('archive', 'Archivé'),
    ]
    DEVISE_CHOICES = [
        ('XOF', 'Franc CFA (XOF)'),
        ('EUR', 'Euro (EUR)'),
        ('USD', 'Dollar US (USD)'),
        ('GBP', 'Livre Sterling (GBP)'),
        ('CHF', 'Franc Suisse (CHF)'),
    ]

    # Identification
    code = models.CharField(max_length=30, unique=True)
    intitule = models.CharField(max_length=300)
    acronyme = models.CharField(max_length=30, blank=True)
    description = models.TextField()

    # Rattachements
    organisation = models.ForeignKey(
        'gouvernance.Organisation', on_delete=models.CASCADE, related_name='programmes'
    )
    bailleur = models.ForeignKey(
        'gouvernance.Bailleur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='programmes_finances',
    )
    bailleurs_supplementaires = models.ManyToManyField(
        'gouvernance.Bailleur', related_name='programmes_cofinances', blank=True
    )
    partenaires = models.ManyToManyField(
        'gouvernance.Partenaire', through='PartenaireProgramme', blank=True
    )
    zones_intervention = models.ManyToManyField(ZoneIntervention, blank=True)

    # Responsables
    coordonnateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='programmes_coordonnes',
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='programmes_responsables',
    )
    equipe = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='programmes_equipe', blank=True
    )

    # Période et budget
    date_debut = models.DateField()
    date_fin = models.DateField()
    budget_total = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')

    # Statut et workflow
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    soumis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='programmes_soumis',
    )
    date_soumission = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='programmes_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    date_cloture = models.DateField(null=True, blank=True)
    motif_suspension = models.TextField(blank=True)

    # Objectifs stratégiques (texte libre pour le module, structure dans ObjectifProgramme)
    contexte = models.TextField(blank=True)
    impacts_attendus = models.TextField(blank=True)

    # Suivi
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    nb_projets = models.IntegerField(default=0)

    # Meta
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    reference_externe = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='programmes_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Programme'
        ordering = ['-created_at']
        permissions = [
            ('can_validate_programme', 'Peut valider un programme'),
            ('can_close_programme', 'Peut clôturer un programme'),
        ]

    def __str__(self):
        return f"[{self.code}] {self.intitule}"

    @property
    def duree_jours(self):
        if self.date_debut and self.date_fin:
            return (self.date_fin - self.date_debut).days
        return 0

    @property
    def est_en_retard(self):
        return self.date_fin < timezone.now().date() and self.statut == 'en_cours'

    def soumettre(self, user):
        self.statut = 'soumis'
        self.soumis_par = user
        self.date_soumission = timezone.now()
        self.save(update_fields=['statut', 'soumis_par', 'date_soumission'])

    def valider(self, user):
        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])

    def activer(self):
        self.statut = 'en_cours'
        self.save(update_fields=['statut'])

    def suspendre(self, motif=''):
        self.statut = 'suspendu'
        self.motif_suspension = motif
        self.save(update_fields=['statut', 'motif_suspension'])

    def cloturer(self):
        self.statut = 'cloture'
        self.date_cloture = timezone.now().date()
        self.save(update_fields=['statut', 'date_cloture'])


class ObjectifProgramme(models.Model):
    TYPE_CHOICES = [
        ('strategique', 'Objectif stratégique'),
        ('specifique', 'Objectif spécifique'),
        ('resultat', 'Résultat attendu'),
        ('impact', 'Impact attendu'),
    ]

    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='objectifs')
    type_objectif = models.CharField(max_length=15, choices=TYPE_CHOICES)
    code = models.CharField(max_length=20, blank=True)
    libelle = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    indicateur_mesure = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Objectif programme'
        ordering = ['type_objectif', 'ordre']

    def __str__(self):
        return f"{self.get_type_objectif_display()} — {self.libelle[:60]}"


class PartenaireProgramme(models.Model):
    TYPE_PARTICIPATION_CHOICES = [
        ('technique', 'Partenaire technique'),
        ('financier', 'Partenaire financier'),
        ('prestataire', 'Prestataire'),
        ('ong', 'ONG partenaire'),
        ('mise_en_oeuvre', "Partenaire de mise en œuvre"),
    ]

    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='participations')
    partenaire = models.ForeignKey(
        'gouvernance.Partenaire', on_delete=models.CASCADE, related_name='participations_programme'
    )
    type_participation = models.CharField(max_length=20, choices=TYPE_PARTICIPATION_CHOICES)
    montant_contribution = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Partenaire programme'
        unique_together = ['programme', 'partenaire']

    def __str__(self):
        return f"{self.partenaire} — {self.programme.code}"


class DocumentProgramme(models.Model):
    TYPE_CHOICES = [
        ('tdr', 'Termes de Référence'),
        ('convention', 'Convention'),
        ('contrat', 'Contrat'),
        ('rapport', 'Rapport'),
        ('reference', 'Document de référence'),
        ('avenant', 'Avenant'),
        ('correspondance', 'Correspondance'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('final', 'Final'),
        ('archive', 'Archivé'),
    ]

    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='documents')
    titre = models.CharField(max_length=300)
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    fichier = models.FileField(upload_to='programmes/documents/%Y/%m/', null=True, blank=True)
    url_externe = models.URLField(blank=True)
    date_document = models.DateField(null=True, blank=True)
    version = models.CharField(max_length=10, default='1.0')
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Document programme'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_document_display()} — {self.titre}"


# ─── Projet ──────────────────────────────────────────────────────────────────

class Projet(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('planifie', 'Planifié'),
        ('valide', 'Validé'),
        ('en_cours', 'En cours'),
        ('suspendu', 'Suspendu'),
        ('termine', 'Terminé'),
        ('cloture', 'Clôturé'),
        ('archive', 'Archivé'),
    ]
    PRIORITE_CHOICES = [
        ('faible', 'Faible'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    DEVISE_CHOICES = Programme.DEVISE_CHOICES

    # Identification
    code = models.CharField(max_length=30, unique=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    # Rattachements
    programme = models.ForeignKey(
        Programme, on_delete=models.CASCADE, related_name='projets', null=True, blank=True
    )
    organisation = models.ForeignKey(
        'gouvernance.Organisation', on_delete=models.CASCADE, related_name='projets'
    )
    zones_intervention = models.ManyToManyField(ZoneIntervention, blank=True)

    # Responsables
    chef_projet = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='projets_geres',
    )

    # Période et budget
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    budget_initial = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    budget_revise = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')

    # Statut et priorité
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')

    # Workflow
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projets_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    date_cloture = models.DateField(null=True, blank=True)
    motif_suspension = models.TextField(blank=True)

    # Suivi
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Meta
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    reference_externe = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='projets_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Projet'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.code}] {self.titre}"

    @property
    def budget_actuel(self):
        return self.budget_revise if self.budget_revise else self.budget_initial

    @property
    def est_en_retard(self):
        return self.date_fin_prevue < timezone.now().date() and self.statut == 'en_cours'

    def valider(self, user):
        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])

    def activer(self):
        self.statut = 'en_cours'
        self.save(update_fields=['statut'])

    def suspendre(self, motif=''):
        self.statut = 'suspendu'
        self.motif_suspension = motif
        self.save(update_fields=['statut', 'motif_suspension'])

    def cloturer(self):
        self.statut = 'cloture'
        self.date_cloture = timezone.now().date()
        self.date_fin_reelle = timezone.now().date()
        self.save(update_fields=['statut', 'date_cloture', 'date_fin_reelle'])


class MembreEquipeProjet(models.Model):
    ROLE_CHOICES = [
        ('chef_projet', 'Chef de projet'),
        ('coordinateur', 'Coordinateur'),
        ('responsable_activite', "Responsable d'activité"),
        ('agent_terrain', 'Agent terrain'),
        ('consultant', 'Consultant'),
        ('partenaire', 'Partenaire'),
        ('observateur', 'Observateur'),
    ]

    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='membres_equipe')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projets_membre'
    )
    role_projet = models.CharField(max_length=25, choices=ROLE_CHOICES)
    date_affectation = models.DateField(default=timezone.now)
    date_fin_affectation = models.DateField(null=True, blank=True)
    taux_affectation = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Membre équipe projet'
        unique_together = ['projet', 'user']

    def __str__(self):
        return f"{self.user} — {self.projet.code} ({self.get_role_projet_display()})"


class RisqueProjet(models.Model):
    PROBABILITE_CHOICES = [
        ('faible', 'Faible'),
        ('moyen', 'Moyen'),
        ('eleve', 'Élevé'),
        ('tres_eleve', 'Très élevé'),
    ]
    IMPACT_CHOICES = [
        ('negligeable', 'Négligeable'),
        ('mineur', 'Mineur'),
        ('modere', 'Modéré'),
        ('majeur', 'Majeur'),
        ('critique', 'Critique'),
    ]
    CATEGORIE_CHOICES = [
        ('financier', 'Financier'),
        ('technique', 'Technique'),
        ('organisationnel', 'Organisationnel'),
        ('environnemental', 'Environnemental'),
        ('politique', 'Politique'),
        ('social', 'Social'),
        ('securite', 'Sécurité'),
    ]
    STATUT_CHOICES = [
        ('identifie', 'Identifié'),
        ('en_cours_traitement', 'En cours de traitement'),
        ('resolu', 'Résolu'),
        ('accepte', 'Accepté'),
        ('surveille', 'Surveillé'),
    ]

    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='risques')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='technique')
    probabilite = models.CharField(max_length=15, choices=PROBABILITE_CHOICES)
    impact = models.CharField(max_length=15, choices=IMPACT_CHOICES)
    niveau_risque = models.CharField(max_length=15, blank=True)
    mesures_mitigation = models.TextField(blank=True)
    mesures_contingence = models.TextField(blank=True)
    responsable_suivi = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='identifie')
    date_identification = models.DateField(auto_now_add=True)
    date_resolution = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Risque projet'
        ordering = ['-date_identification']

    def __str__(self):
        return f"{self.titre} ({self.projet.code})"

    def save(self, *args, **kwargs):
        prob_scores = {'faible': 1, 'moyen': 2, 'eleve': 3, 'tres_eleve': 4}
        imp_scores = {'negligeable': 1, 'mineur': 2, 'modere': 3, 'majeur': 4, 'critique': 5}
        score = prob_scores.get(self.probabilite, 1) * imp_scores.get(self.impact, 1)
        if score <= 2:
            self.niveau_risque = 'faible'
        elif score <= 6:
            self.niveau_risque = 'moyen'
        elif score <= 12:
            self.niveau_risque = 'eleve'
        else:
            self.niveau_risque = 'critique'
        super().save(*args, **kwargs)


class LivrableProjet(models.Model):
    TYPE_CHOICES = [
        ('rapport', 'Rapport'),
        ('document', 'Document'),
        ('produit', 'Produit/Équipement'),
        ('service', 'Service'),
        ('formation', 'Formation'),
        ('etude', 'Étude/Recherche'),
        ('infrastructure', 'Infrastructure'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('soumis', 'Soumis pour validation'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='livrables')
    code = models.CharField(max_length=20, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_livrable = models.CharField(max_length=20, choices=TYPE_CHOICES, default='rapport')
    date_prevue = models.DateField()
    date_livraison = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='planifie')
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='livrables_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    fichier = models.FileField(upload_to='projets/livrables/%Y/%m/', null=True, blank=True)
    critere_acceptation = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Livrable projet'
        ordering = ['date_prevue']

    def __str__(self):
        return f"[{self.code}] {self.titre}"

    def valider(self, user):
        self.statut = 'valide'
        self.validateur = user
        self.date_validation = timezone.now()
        self.date_livraison = self.date_livraison or timezone.now().date()
        self.save()


class JalonProjet(models.Model):
    STATUT_CHOICES = [
        ('a_venir', 'À venir'),
        ('atteint', 'Atteint'),
        ('manque', 'Manqué'),
        ('reporte', 'Reporté'),
    ]

    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='jalons')
    libelle = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_prevue = models.DateField()
    date_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='a_venir')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Jalon projet'
        ordering = ['date_prevue']

    def __str__(self):
        return f"{self.libelle} ({self.projet.code})"
