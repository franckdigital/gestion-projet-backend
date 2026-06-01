from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M08 : Cadre Logique ─────────────────────────────────────────────────────

class CadreLogique(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('archive', 'Archivé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='cadres_logiques', null=True, blank=True,
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='cadres_logiques', null=True, blank=True,
    )
    titre = models.CharField(max_length=200, default='Cadre Logique')
    version = models.CharField(max_length=10, default='1.0')
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadres_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='cadres_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cadre logique'
        ordering = ['-created_at']

    def __str__(self):
        ref = self.projet or self.programme
        return f"Cadre Logique v{self.version} — {ref}"


class ElementCadreLogique(models.Model):
    NIVEAU_CHOICES = [
        ('objectif_global', 'Objectif Global'),
        ('objectif_specifique', 'Objectif Spécifique'),
        ('resultat', 'Résultat'),
        ('activite', 'Activité'),
        ('sous_activite', 'Sous-activité'),
    ]

    cadre = models.ForeignKey(CadreLogique, on_delete=models.CASCADE, related_name='elements')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_elements'
    )
    niveau = models.CharField(max_length=25, choices=NIVEAU_CHOICES)
    code = models.CharField(max_length=30)
    description = models.TextField()
    indicateurs_objectifs = models.TextField(blank=True)
    sources_verification = models.TextField(blank=True)
    hypotheses = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Élément cadre logique'
        ordering = ['ordre', 'code']

    def __str__(self):
        return f"[{self.code}] {self.get_niveau_display()} — {self.description[:60]}"


# ─── M09 : SWOT ──────────────────────────────────────────────────────────────

class AnalyseSWOT(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('finalise', 'Finalisé'),
        ('archive', 'Archivé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='analyses_swot', null=True, blank=True,
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='analyses_swot', null=True, blank=True,
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contexte = models.TextField(blank=True)
    date_analyse = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='swots_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Analyse SWOT'
        ordering = ['-date_analyse']

    def __str__(self):
        ref = self.projet or self.programme
        return f"SWOT — {ref} ({self.date_analyse})"


class ElementSWOT(models.Model):
    CATEGORIE_CHOICES = [
        ('force', 'Force'),
        ('faiblesse', 'Faiblesse'),
        ('opportunite', 'Opportunité'),
        ('menace', 'Menace'),
    ]
    PONDERATION_CHOICES = [(i, str(i)) for i in range(1, 6)]

    analyse = models.ForeignKey(AnalyseSWOT, on_delete=models.CASCADE, related_name='elements')
    categorie = models.CharField(max_length=15, choices=CATEGORIE_CHOICES)
    description = models.TextField()
    ponderation = models.IntegerField(choices=PONDERATION_CHOICES, default=3)
    classement = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Élément SWOT'
        ordering = ['categorie', '-ponderation']

    def __str__(self):
        return f"{self.get_categorie_display()} — {self.description[:60]}"


class StrategieSWOT(models.Model):
    TYPE_CHOICES = [
        ('FO', 'Forces × Opportunités (Stratégie offensive)'),
        ('FM', 'Forces × Menaces (Stratégie défensive)'),
        ('FaO', 'Faiblesses × Opportunités (Stratégie de rattrapage)'),
        ('FaM', 'Faiblesses × Menaces (Stratégie de survie)'),
    ]
    PRIORITE_CHOICES = [
        ('haute', 'Haute'),
        ('moyenne', 'Moyenne'),
        ('faible', 'Faible'),
    ]

    analyse = models.ForeignKey(AnalyseSWOT, on_delete=models.CASCADE, related_name='strategies')
    type_strategie = models.CharField(max_length=5, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    description = models.TextField()
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='moyenne')
    elements_lies = models.ManyToManyField(ElementSWOT, blank=True)
    notes = models.TextField(blank=True)
    generee_par_ia = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Stratégie SWOT'
        ordering = ['type_strategie', 'priorite']

    def __str__(self):
        return f"{self.get_type_strategie_display()} — {self.titre}"


# ─── M10 : TDR ───────────────────────────────────────────────────────────────

class TDR(models.Model):
    TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('formation', 'Formation'),
        ('etude', 'Étude'),
        ('audit', 'Audit'),
        ('evaluation', 'Évaluation'),
        ('recrutement', 'Recrutement'),
        ('mission', 'Mission'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_revision', 'En révision'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='tdrs', null=True, blank=True,
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='tdrs', null=True, blank=True,
    )
    reference = models.CharField(max_length=50, unique=True, blank=True)
    titre = models.CharField(max_length=300)
    type_tdr = models.CharField(max_length=15, choices=TYPE_CHOICES, default='consultation')

    # Sections structurées
    contexte = models.TextField(blank=True)
    justification = models.TextField(blank=True)
    objectifs = models.TextField(blank=True)
    resultats_attendus = models.TextField(blank=True)
    methodologie = models.TextField(blank=True)
    livrables = models.TextField(blank=True)
    calendrier = models.TextField(blank=True)
    budget_previsionnel = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profil_consultant = models.TextField(blank=True)
    criteres_selection = models.TextField(blank=True)
    modalites_paiement = models.TextField(blank=True)

    # Workflow
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    redige_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='tdrs_rediges',
    )
    date_redaction = models.DateField(null=True, blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tdrs_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    publie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tdrs_publies',
    )
    date_publication = models.DateTimeField(null=True, blank=True)

    # Génération IA
    genere_par_ia = models.BooleanField(default=False)
    prompt_ia = models.TextField(blank=True)

    fichier_final = models.FileField(upload_to='tdrs/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'TDR'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from datetime import date
            count = TDR.objects.count() + 1
            self.reference = f"TDR-{date.today().year}-{count:04d}"
        super().save(*args, **kwargs)

    def valider(self, user):
        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])

    def publier(self, user):
        self.statut = 'publie'
        self.publie_par = user
        self.date_publication = timezone.now()
        self.save(update_fields=['statut', 'publie_par', 'date_publication'])


# ─── M11 : Plans d'Actions ───────────────────────────────────────────────────

class PlanAction(models.Model):
    PERIODE_CHOICES = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
        ('trimestriel', 'Trimestriel'),
        ('mensuel', 'Mensuel'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('en_cours', 'En cours'),
        ('cloture', 'Clôturé'),
        ('archive', 'Archivé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='plans_action', null=True, blank=True,
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='plans_action', null=True, blank=True,
    )
    titre = models.CharField(max_length=200)
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='trimestriel')
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True)
    mois = models.IntegerField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    budget_total = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans_action_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='plans_action_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan d'action"
        ordering = ['-annee', 'trimestre']

    def __str__(self):
        ref = self.projet or self.programme
        return f"Plan Action {self.periode} {self.annee} — {ref}"

    @property
    def taux_realisation(self):
        items = self.items.all()
        if not items:
            return 0
        total = sum(i.taux_avancement for i in items)
        return round(total / len(items), 2)


class ActionPlanItem(models.Model):
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
        ('en_retard', 'En retard'),
    ]

    plan = models.ForeignKey(PlanAction, on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_actions'
    )
    code = models.CharField(max_length=20, blank=True)
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='actions_responsable',
    )
    co_responsables = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='actions_co_responsable', blank=True
    )
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    indicateur_realisation = models.CharField(max_length=300, blank=True)
    livrable_attendu = models.CharField(max_length=300, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifie')
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    commentaires = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item plan d'action"
        ordering = ['ordre', 'date_debut']

    def __str__(self):
        return f"[{self.code}] {self.libelle}"

    @property
    def est_en_retard(self):
        return self.date_fin < timezone.now().date() and self.statut not in ('termine', 'annule')


# ─── M12 : Programmes d'Activités ────────────────────────────────────────────

class ProgrammeActivites(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('en_cours', 'En cours'),
        ('cloture', 'Clôturé'),
        ('archive', 'Archivé'),
    ]
    PERIODE_CHOICES = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
        ('trimestriel', 'Trimestriel'),
        ('mensuel', 'Mensuel'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='programmes_activites', null=True, blank=True,
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='programmes_activites', null=True, blank=True,
    )
    reference = models.CharField(max_length=50, blank=True)
    titre = models.CharField(max_length=200)
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='annuel')
    annee = models.IntegerField()
    semestre = models.IntegerField(null=True, blank=True)
    trimestre = models.IntegerField(null=True, blank=True)
    mois = models.IntegerField(null=True, blank=True)
    budget_total = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pa_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='pa_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Programme d'activités"
        ordering = ['-annee', 'trimestre']

    def __str__(self):
        ref = self.projet or self.programme
        return f"PA {self.annee} — {ref}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from datetime import date
            count = ProgrammeActivites.objects.count() + 1
            self.reference = f"PA-{self.annee}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def taux_realisation(self):
        activites = self.activites.all()
        if not activites:
            return 0
        total = sum(a.taux_avancement for a in activites)
        return round(total / activites.count(), 2)


class ActivitePA(models.Model):
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('reportee', 'Reportée'),
        ('en_retard', 'En retard'),
    ]

    programme_activites = models.ForeignKey(
        ProgrammeActivites, on_delete=models.CASCADE, related_name='activites'
    )
    element_cadre = models.ForeignKey(
        ElementCadreLogique, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activites_pa',
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_activites'
    )
    code = models.CharField(max_length=30)
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='activites_pa_responsable',
    )
    co_responsables = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='activites_pa_co', blank=True
    )

    # Dates
    date_debut_prevue = models.DateField()
    date_fin_prevue = models.DateField()
    date_debut_reelle = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)

    # Budget
    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Indicateurs
    indicateur = models.CharField(max_length=300, blank=True)
    cible = models.CharField(max_length=100, blank=True)
    unite_mesure = models.CharField(max_length=50, blank=True)
    valeur_realisee = models.CharField(max_length=100, blank=True)

    # Suivi
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ordre = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Activité PA"
        ordering = ['ordre', 'date_debut_prevue']

    def __str__(self):
        return f"[{self.code}] {self.libelle}"

    @property
    def est_en_retard(self):
        return (
            self.date_fin_prevue < timezone.now().date()
            and self.statut not in ('terminee', 'annulee')
        )


# ─── Plan de Travail Opérationnel (planification physique) ───────────────────

class PlanTravail(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('en_cours', 'En cours'),
        ('cloture', 'Clôturé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE, related_name='plans_travail'
    )
    nom = models.CharField(max_length=200)
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans_travail_valides',
    )
    date_validation = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan de travail'
        ordering = ['-annee', 'trimestre']

    def __str__(self):
        return f"{self.projet.code} — Plan {self.annee}"


class Activite(models.Model):
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('retardee', 'Retardée'),
    ]

    plan = models.ForeignKey(PlanTravail, on_delete=models.CASCADE, related_name='activites')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_activites'
    )
    code = models.CharField(max_length=30)
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')
    date_debut_prevue = models.DateField()
    date_fin_prevue = models.DateField()
    date_debut_reelle = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='activites_responsable',
    )
    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ordre = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Activité'
        ordering = ['ordre', 'date_debut_prevue']

    def __str__(self):
        return f"[{self.code}] {self.libelle}"


class Jalon(models.Model):
    STATUT_CHOICES = [
        ('a_venir', 'À venir'),
        ('atteint', 'Atteint'),
        ('manque', 'Manqué'),
        ('reporte', 'Reporté'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE, related_name='jalons_planif'
    )
    libelle = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_prevue = models.DateField()
    date_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='a_venir')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Jalon'
        ordering = ['date_prevue']

    def __str__(self):
        return self.libelle
