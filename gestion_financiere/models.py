from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator


# ─── Constantes partagées ─────────────────────────────────────────────────────

DEVISE_CHOICES = [
    ('XOF', 'Franc CFA (XOF)'),
    ('EUR', 'Euro (EUR)'),
    ('USD', 'Dollar US (USD)'),
    ('GBP', 'Livre Sterling (GBP)'),
    ('CHF', 'Franc Suisse (CHF)'),
]


# ─── M21 : Gestion Budgétaire ────────────────────────────────────────────────

class Budget(models.Model):
    TYPE_CHOICES = [
        ('programme', 'Budget Programme'),
        ('projet', 'Budget Projet'),
        ('activite', 'Budget Activité'),
        ('mission', 'Budget Mission'),
        ('formation', 'Budget Formation'),
    ]
    STATUT_CHOICES = [
        ('preparation', 'En préparation'),
        ('soumis', 'Soumis'),
        ('validation_finance', 'Validation Finance'),
        ('validation_direction', 'Validation Direction'),
        ('approuve', 'Approuvé'),
        ('en_execution', 'En exécution'),
        ('revise', 'Révisé'),
        ('cloture', 'Clôturé'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    type_budget = models.CharField(max_length=15, choices=TYPE_CHOICES, default='projet')
    exercice = models.IntegerField()
    intitule = models.CharField(max_length=300, blank=True)

    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets_v2',
    )

    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    montant_initial = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    montant_revise = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    montant_engage = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    montant_depense = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='preparation')

    soumis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets_soumis',
    )
    date_soumission = models.DateTimeField(null=True, blank=True)
    valide_finance_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets_valides_finance',
    )
    date_validation_finance = models.DateTimeField(null=True, blank=True)
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets_approuves',
    )
    date_approbation = models.DateField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='budgets_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Budget'
        ordering = ['-exercice', '-created_at']

    def __str__(self):
        return f"[{self.reference}] Budget {self.get_type_budget_display()} — {self.exercice}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Budget.objects.count() + 1
            self.reference = f"BUD-{self.exercice}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def montant_actuel(self):
        return self.montant_revise if self.montant_revise else self.montant_initial

    @property
    def solde_disponible(self):
        return self.montant_actuel - self.montant_engage

    @property
    def taux_execution(self):
        if not self.montant_actuel:
            return 0
        return round(float(self.montant_depense) / float(self.montant_actuel) * 100, 2)

    @property
    def taux_engagement(self):
        if not self.montant_actuel:
            return 0
        return round(float(self.montant_engage) / float(self.montant_actuel) * 100, 2)

    def soumettre(self, user):
        self.statut = 'soumis'
        self.soumis_par = user
        self.date_soumission = timezone.now()
        self.save(update_fields=['statut', 'soumis_par', 'date_soumission'])

    def valider_finance(self, user):
        self.statut = 'validation_finance'
        self.valide_finance_par = user
        self.date_validation_finance = timezone.now()
        self.save(update_fields=['statut', 'valide_finance_par', 'date_validation_finance'])

    def approuver(self, user):
        self.statut = 'approuve'
        self.approuve_par = user
        self.date_approbation = timezone.now().date()
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation'])

    def activer(self):
        self.statut = 'en_execution'
        self.save(update_fields=['statut'])

    def dupliquer(self, exercice_cible, user):
        nouveau = Budget.objects.create(
            type_budget=self.type_budget,
            exercice=exercice_cible,
            programme=self.programme,
            projet=self.projet,
            devise=self.devise,
            montant_initial=self.montant_initial,
            notes=f"Dupliqué depuis {self.reference}",
            created_by=user,
        )
        for ligne in self.lignes.all():
            LigneBudgetaire.objects.create(
                budget=nouveau,
                code=ligne.code,
                libelle=ligne.libelle,
                categorie=ligne.categorie,
                montant_prevu=ligne.montant_prevu,
            )
        return nouveau


class RevisionBudgetaire(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='revisions')
    numero_revision = models.IntegerField()
    date_revision = models.DateField(auto_now_add=True)
    motif = models.TextField()
    montant_avant = models.DecimalField(max_digits=20, decimal_places=2)
    montant_apres = models.DecimalField(max_digits=20, decimal_places=2)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='revisions_validees',
    )
    fichier = models.FileField(upload_to='revisions_budget/%Y/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Révision budgétaire'
        ordering = ['numero_revision']
        unique_together = ['budget', 'numero_revision']

    def __str__(self):
        return f"{self.budget.reference} — Rev.{self.numero_revision}"


class LigneBudgetaire(models.Model):
    CATEGORIE_CHOICES = [
        ('personnel', 'Personnel / RH'),
        ('honoraires', 'Honoraires / Consultants'),
        ('formations', 'Formations / Ateliers'),
        ('missions', 'Missions / Déplacements'),
        ('equipements', 'Équipements'),
        ('vehicules', 'Véhicules'),
        ('logiciels', 'Logiciels / Licences'),
        ('fournitures', 'Fournitures de bureau'),
        ('communication', 'Communication'),
        ('services', 'Services externalisés'),
        ('travaux', 'Travaux / Constructions'),
        ('frais_financiers', 'Frais financiers'),
        ('imprevu', 'Imprévus'),
        ('autre', 'Autre'),
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='lignes')
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lignes_budgetaires',
    )
    composante = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=30)
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='autre')
    unite = models.CharField(max_length=50, blank=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    cout_unitaire = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_prevu = models.DecimalField(max_digits=15, decimal_places=2)
    montant_engage = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_depense = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ordre = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ligne budgétaire'
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.libelle}"

    @property
    def solde_disponible(self):
        return self.montant_prevu - self.montant_engage

    @property
    def taux_consommation(self):
        if not self.montant_prevu:
            return 0
        return round(float(self.montant_depense) / float(self.montant_prevu) * 100, 2)

    @property
    def est_depassee(self):
        return self.montant_engage > self.montant_prevu


# ─── Legacy models ────────────────────────────────────────────────────────────

class BudgetProjet(models.Model):
    STATUT_CHOICES = [
        ('draft', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('approuve', 'Approuvé'),
        ('revise', 'Révisé'),
        ('cloture', 'Clôturé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE, related_name='budgets'
    )
    exercice = models.IntegerField()
    montant_initial = models.DecimalField(max_digits=20, decimal_places=2)
    montant_revise = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='draft')
    date_approbation = models.DateField(null=True, blank=True)
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets_projets_approuves',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Budget projet (legacy)'
        unique_together = ['projet', 'exercice']

    def __str__(self):
        return f"Budget {self.projet.code} — {self.exercice}"

    @property
    def montant_actuel(self):
        return self.montant_revise if self.montant_revise else self.montant_initial


class LigneBudgetaireLegacy(models.Model):
    CATEGORIE_CHOICES = LigneBudgetaire.CATEGORIE_CHOICES

    budget = models.ForeignKey(BudgetProjet, on_delete=models.CASCADE, related_name='lignes')
    code = models.CharField(max_length=30)
    libelle = models.CharField(max_length=200)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='autre')
    montant_prevu = models.DecimalField(max_digits=15, decimal_places=2)
    montant_engage = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_depense = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ligne budgétaire (legacy)'
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.libelle}"

    @property
    def solde_disponible(self):
        return self.montant_prevu - self.montant_engage

    @property
    def taux_consommation(self):
        if not self.montant_prevu:
            return 0
        return round((self.montant_depense / self.montant_prevu) * 100, 2)


# ─── M22 : Dépenses et Décaissements ─────────────────────────────────────────

class Fournisseur(models.Model):
    TYPE_CHOICES = [
        ('entreprise', 'Entreprise'),
        ('consultant', 'Consultant / Individu'),
        ('ong', 'ONG / Association'),
        ('administration', 'Administration'),
        ('autre', 'Autre'),
    ]

    code = models.CharField(max_length=20, blank=True)
    nom = models.CharField(max_length=300)
    type_fournisseur = models.CharField(max_length=20, choices=TYPE_CHOICES, default='entreprise')
    numero_contribuable = models.CharField(max_length=50, blank=True)
    adresse = models.TextField(blank=True)
    pays = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    contact_principal = models.CharField(max_length=200, blank=True)
    rib = models.CharField(max_length=100, blank=True, verbose_name='RIB/IBAN')
    banque = models.CharField(max_length=200, blank=True)
    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fournisseur'
        ordering = ['nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            count = Fournisseur.objects.count() + 1
            self.code = f"FOUR-{count:04d}"
        super().save(*args, **kwargs)


class Depense(models.Model):
    TYPE_CHOICES = [
        ('fonctionnement', 'Fonctionnement'),
        ('projet', 'Projet'),
        ('investissement', 'Investissement'),
        ('mission', 'Mission'),
        ('formation', 'Formation'),
        ('personnel', 'Personnel'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('validation_responsable', 'Validation Responsable'),
        ('validation_finance', 'Validation Finance'),
        ('approuve', 'Approuvé'),
        ('paye', 'Payé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
        ('autre', 'Autre'),
    ]
    TYPE_PIECE_CHOICES = [
        ('facture', 'Facture'),
        ('recu', 'Reçu'),
        ('contrat', 'Contrat'),
        ('bon_commande', 'Bon de commande'),
        ('bordereau', 'Bordereau'),
        ('quittance', 'Quittance'),
        ('autre', 'Autre'),
    ]

    ligne_budgetaire = models.ForeignKey(
        LigneBudgetaire, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses_financieres',
    )
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses_financieres',
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses',
    )

    reference = models.CharField(max_length=50, blank=True)
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_depense = models.CharField(max_length=20, choices=TYPE_CHOICES, default='projet')
    montant = models.DecimalField(max_digits=15, decimal_places=2,
                                  validators=[MinValueValidator(0)])
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    taux_change = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    montant_base = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    date_depense = models.DateField()
    date_paiement = models.DateField(null=True, blank=True)
    mode_paiement = models.CharField(max_length=15, choices=MODE_PAIEMENT_CHOICES, default='virement')
    type_piece = models.CharField(max_length=15, choices=TYPE_PIECE_CHOICES, default='facture')
    numero_piece = models.CharField(max_length=100, blank=True)
    justificatif = models.FileField(upload_to='justificatifs/%Y/%m/', null=True, blank=True)

    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='brouillon')
    saisi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='depenses_saisies',
    )
    valide_responsable_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses_validees_responsable',
    )
    valide_finance_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses_validees_finance',
    )
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses_approuvees',
    )
    date_approbation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dépense'
        ordering = ['-date_depense']

    def __str__(self):
        return f"[{self.reference}] {self.libelle} — {self.montant}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Depense.objects.count() + 1
            self.reference = f"DEP-{timezone.now().year}-{count:05d}"
        self.montant_base = self.montant * self.taux_change
        super().save(*args, **kwargs)

    def soumettre(self):
        self.statut = 'soumis'
        self.save(update_fields=['statut'])

    def valider_responsable(self, user):
        self.statut = 'validation_responsable'
        self.valide_responsable_par = user
        self.save(update_fields=['statut', 'valide_responsable_par'])

    def valider_finance(self, user):
        self.statut = 'validation_finance'
        self.valide_finance_par = user
        self.save(update_fields=['statut', 'valide_finance_par'])

    def approuver(self, user):
        self.statut = 'approuve'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation'])
        if self.ligne_budgetaire:
            self.ligne_budgetaire.montant_engage += self.montant
            self.ligne_budgetaire.save(update_fields=['montant_engage'])

    def marquer_paye(self, date_paiement=None, mode=None):
        self.statut = 'paye'
        self.date_paiement = date_paiement or timezone.now().date()
        if mode:
            self.mode_paiement = mode
        self.save(update_fields=['statut', 'date_paiement', 'mode_paiement'])
        if self.ligne_budgetaire:
            self.ligne_budgetaire.montant_depense += self.montant
            self.ligne_budgetaire.save(update_fields=['montant_depense'])

    def rejeter(self, user, motif=''):
        self.statut = 'rejete'
        self.motif_rejet = motif
        self.save(update_fields=['statut', 'motif_rejet'])


class DepenseLegacy(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('approuve', 'Approuvé'),
        ('paye', 'Payé'),
        ('rejete', 'Rejeté'),
    ]

    ligne = models.ForeignKey(
        LigneBudgetaireLegacy, on_delete=models.CASCADE, related_name='depenses'
    )
    reference = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=200)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    date_depense = models.DateField()
    fournisseur = models.CharField(max_length=200, blank=True)
    numero_facture = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    justificatif = models.FileField(upload_to='justificatifs/%Y/%m/', null=True, blank=True)
    saisi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='depenses_legacy_saisies',
    )
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depenses_legacy_approuvees',
    )
    date_approbation = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dépense (legacy)'
        ordering = ['-date_depense']

    def __str__(self):
        return f"[{self.reference}] {self.libelle} — {self.montant}"


class Avance(models.Model):
    TYPE_CHOICES = [
        ('mission', 'Avance mission'),
        ('activite', 'Avance activité'),
        ('fournisseur', 'Avance fournisseur'),
    ]
    STATUT_CHOICES = [
        ('accordee', 'Accordée'),
        ('partiellement_justifiee', 'Partiellement justifiée'),
        ('justifiee', 'Justifiée'),
        ('non_justifiee', 'Non justifiée'),
        ('remboursee', 'Remboursée'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    type_avance = models.CharField(max_length=20, choices=TYPE_CHOICES, default='mission')
    beneficiaire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avances_recues',
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avances',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avances',
    )
    ligne_budgetaire = models.ForeignKey(
        LigneBudgetaire, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='avances',
    )
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    montant_justifie = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_rembourse = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_accord = models.DateField()
    date_limite_justification = models.DateField(null=True, blank=True)
    motif = models.CharField(max_length=300)
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='accordee')
    accorde_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='avances_accordees',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avance'
        ordering = ['-date_accord']

    def __str__(self):
        return f"[{self.reference}] {self.get_type_avance_display()} — {self.montant}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Avance.objects.count() + 1
            self.reference = f"AVA-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def solde_a_justifier(self):
        return self.montant - self.montant_justifie - self.montant_rembourse


# ─── Engagement budgétaire ────────────────────────────────────────────────────

class Engagement(models.Model):
    TYPE_CHOICES = [
        # Cycle d'achat
        ('requisition',    'Réquisition'),
        ('demande_achat',  "Demande d'achat"),
        ('bon_commande',   'Bon de commande'),
        ('contrat',        'Contrat'),
        ('engagement',     'Engagement budgétaire'),
        # Cycle de paiement
        ('liquidation',    'Liquidation'),
        ('ordonnancement', 'Ordonnancement'),
        ('paiement',       'Paiement'),
    ]
    STATUT_CHOICES = [
        ('brouillon',   'Brouillon'),
        ('soumis',      'Soumis'),
        ('valide',      'Validé'),
        ('approuve',    'Approuvé'),
        ('en_cours',    'En cours'),
        ('liquide',     'Liquidé'),
        ('ordonnance',  'Ordonné'),
        ('paye',        'Payé'),
        ('annule',      'Annulé'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    type_engagement = models.CharField(max_length=20, choices=TYPE_CHOICES, default='bon_commande')
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    ligne_budgetaire = models.ForeignKey(
        LigneBudgetaire, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='engagements',
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='engagements',
    )
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    montant_liquide = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_engagement = models.DateField()
    date_echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='engagements_valides',
    )
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='engagements_approuves',
    )
    date_approbation = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.TextField(blank=True)
    fichier = models.FileField(upload_to='engagements/%Y/%m/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='engagements_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Engagement budgétaire'
        ordering = ['-date_engagement']

    def __str__(self):
        return f"[{self.reference}] {self.libelle}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Engagement.objects.count() + 1
            prefix = {
                'bon_commande':   'BC',
                'contrat':        'CTR',
                'requisition':    'REQ',
                'demande_achat':  'DA',
                'engagement':     'ENG',
                'liquidation':    'LIQ',
                'ordonnancement': 'ORD',
                'paiement':       'PAY',
            }.get(self.type_engagement, 'ENG')
            self.reference = f"{prefix}-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def solde_engage(self):
        return self.montant - self.montant_liquide

    def approuver(self, user):
        self.statut = 'approuve'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation'])
        if self.ligne_budgetaire:
            self.ligne_budgetaire.montant_engage += self.montant
            self.ligne_budgetaire.save(update_fields=['montant_engage'])

    def liquider(self, montant):
        """Liquidation : constatation du service fait, validation du montant à payer."""
        self.montant_liquide += montant
        self.statut = 'liquide' if self.montant_liquide >= self.montant else 'en_cours'
        self.save(update_fields=['montant_liquide', 'statut'])

    def ordonner(self, user):
        """Ordonnancement : ordre de paiement émis à la comptabilité."""
        self.statut = 'ordonnance'
        self.save(update_fields=['statut'])

    def marquer_paye(self, user, date_paiement=None):
        """Paiement : exécution effective du virement ou règlement."""
        self.statut = 'paye'
        self.save(update_fields=['statut'])
        if self.ligne_budgetaire:
            self.ligne_budgetaire.montant_depense += self.montant_liquide or self.montant
            self.ligne_budgetaire.save(update_fields=['montant_depense'])


# ─── M23 : Financements et Bailleurs ─────────────────────────────────────────

class Convention(models.Model):
    TYPE_CHOICES = [
        ('subvention', 'Subvention'),
        ('pret', 'Prêt / Crédit'),
        ('don', 'Don'),
        ('cofinancement', 'Cofinancement'),
        ('partenariat', 'Accord de partenariat'),
    ]
    STATUT_CHOICES = [
        ('en_negociation', 'En négociation'),
        ('signee', 'Signée'),
        ('active', 'Active'),
        ('suspendue', 'Suspendue'),
        ('cloturee', 'Clôturée'),
        ('resiliee', 'Résiliée'),
    ]

    reference = models.CharField(max_length=50, blank=True)
    type_convention = models.CharField(max_length=20, choices=TYPE_CHOICES, default='subvention')
    intitule = models.CharField(max_length=300)
    bailleur = models.ForeignKey(
        'gouvernance.Bailleur', on_delete=models.PROTECT,
        related_name='conventions',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conventions',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conventions',
    )
    date_signature = models.DateField(null=True, blank=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    montant_total = models.DecimalField(max_digits=20, decimal_places=2)
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    montant_recu = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_negociation')

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='conventions_gerees',
    )
    conditions_particulieres = models.TextField(blank=True)
    rapport_exige = models.BooleanField(default=True)
    frequence_rapport = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    fichier_convention = models.FileField(upload_to='conventions/%Y/', null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='conventions_creees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Convention'
        ordering = ['-date_signature']

    def __str__(self):
        return f"[{self.reference}] {self.intitule}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Convention.objects.count() + 1
            self.reference = f"CONV-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def montant_restant(self):
        return self.montant_total - self.montant_recu

    @property
    def taux_decaissement(self):
        if not self.montant_total:
            return 0
        return round(float(self.montant_recu) / float(self.montant_total) * 100, 2)


class TrancheFinancement(models.Model):
    STATUT_CHOICES = [
        ('prevue', 'Prévue'),
        ('demandee', 'Demandée'),
        ('en_traitement', 'En traitement'),
        ('recue', 'Reçue'),
        ('partielle', 'Partiellement reçue'),
        ('annulee', 'Annulée'),
    ]

    convention = models.ForeignKey(Convention, on_delete=models.CASCADE, related_name='tranches')
    numero = models.IntegerField()
    libelle = models.CharField(max_length=200, blank=True)
    montant_prevu = models.DecimalField(max_digits=15, decimal_places=2)
    montant_recu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_prevue = models.DateField(null=True, blank=True)
    date_reception = models.DateField(null=True, blank=True)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='prevue')
    conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    fichier = models.FileField(upload_to='tranches/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tranche de financement'
        ordering = ['numero']
        unique_together = ['convention', 'numero']

    def __str__(self):
        return f"{self.convention.reference} — Tranche {self.numero}"

    def marquer_recue(self, montant, date=None):
        self.montant_recu = montant
        self.date_reception = date or timezone.now().date()
        self.statut = 'recue' if montant >= self.montant_prevu else 'partielle'
        self.save()
        self.convention.montant_recu += montant
        self.convention.save(update_fields=['montant_recu'])


class Cofinancement(models.Model):
    convention = models.ForeignKey(Convention, on_delete=models.CASCADE, related_name='cofinancements')
    bailleur = models.ForeignKey(
        'gouvernance.Bailleur', on_delete=models.PROTECT, related_name='cofinancements'
    )
    montant = models.DecimalField(max_digits=20, decimal_places=2)
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    montant_recu = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Cofinancement'
        unique_together = ['convention', 'bailleur']

    def __str__(self):
        return f"{self.convention.reference} — {self.bailleur}"


class RapportBailleur(models.Model):
    TYPE_CHOICES = [
        ('financier', 'Rapport financier'),
        ('utilisation', "Rapport d'utilisation"),
        ('decaissement', 'Rapport de décaissement'),
        ('budgetaire', 'Rapport budgétaire'),
        ('audit', "Rapport d'audit"),
        ('narratif', 'Rapport narratif'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
    ]

    convention = models.ForeignKey(Convention, on_delete=models.CASCADE, related_name='rapports_bailleur')
    reference = models.CharField(max_length=30, blank=True)
    type_rapport = models.CharField(max_length=15, choices=TYPE_CHOICES, default='financier')
    titre = models.CharField(max_length=300)
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    date_soumission_prevue = models.DateField(null=True, blank=True)
    date_soumission_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    contenu = models.TextField(blank=True)
    montant_depense_periode = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_execution = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    observations = models.TextField(blank=True)
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='rapports_bailleur_rediges',
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_bailleur_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    fichier = models.FileField(upload_to='rapports_bailleur/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rapport bailleur'
        ordering = ['-periode_fin']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = RapportBailleur.objects.count() + 1
            self.reference = f"RB-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


# ─── Plan de trésorerie ───────────────────────────────────────────────────────

class PlanTresorerie(models.Model):
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans_tresorerie',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans_tresorerie',
    )
    exercice = models.IntegerField()
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='mensuel')
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='plans_tresorerie_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plan de trésorerie'

    def __str__(self):
        return f"Trésorerie {self.exercice} — {self.get_periode_display()}"


class LigneTresorerie(models.Model):
    TYPE_FLUX_CHOICES = [
        ('entrant', 'Flux entrant'),
        ('sortant', 'Flux sortant'),
    ]
    CATEGORIE_CHOICES = [
        ('financement', 'Financement / Subvention'),
        ('recouvrement', 'Recouvrement'),
        ('remboursement_avance', "Remboursement d'avance"),
        ('depense_projet', 'Dépense projet'),
        ('salaire', 'Salaires / Personnel'),
        ('mission', 'Missions'),
        ('autre', 'Autre'),
    ]

    plan = models.ForeignKey(PlanTresorerie, on_delete=models.CASCADE, related_name='lignes')
    type_flux = models.CharField(max_length=10, choices=TYPE_FLUX_CHOICES)
    categorie = models.CharField(max_length=25, choices=CATEGORIE_CHOICES)
    libelle = models.CharField(max_length=200)
    mois = models.IntegerField(validators=[MinValueValidator(1)])
    annee = models.IntegerField()
    montant_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ligne trésorerie'
        ordering = ['annee', 'mois', 'type_flux']

    def __str__(self):
        return f"{self.libelle} — {self.mois}/{self.annee}"


# ─── Rapport financier interne ────────────────────────────────────────────────

class RapportFinancier(models.Model):
    TYPE_CHOICES = [
        ('budgetaire', 'Rapport budgétaire'),
        ('depenses', 'Rapport des dépenses'),
        ('engagements', 'Rapport des engagements'),
        ('decaissements', 'Rapport des décaissements'),
        ('tresorerie', 'Rapport de trésorerie'),
        ('audit', "Rapport d'audit"),
        ('consommation', 'Rapport de consommation budgétaire'),
        ('cofinancement', 'Rapport de cofinancement'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
    ]
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
        ('ad_hoc', 'Ad hoc'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    type_rapport = models.CharField(max_length=20, choices=TYPE_CHOICES, default='budgetaire')
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='trimestriel')
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_financiers',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_financiers',
    )
    date_debut_periode = models.DateField(null=True, blank=True)
    date_fin_periode = models.DateField(null=True, blank=True)
    date_rapport = models.DateField(default=timezone.now)
    contenu = models.TextField(blank=True)
    donnees_json = models.JSONField(default=dict, blank=True)
    montant_budget = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    montant_depense = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    montant_engage = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    taux_execution = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='rapports_financiers_rediges',
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_financiers_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    fichier = models.FileField(upload_to='rapports_financiers/%Y/%m/', null=True, blank=True)
    genere_par_ia = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapport financier'
        ordering = ['-date_rapport']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = RapportFinancier.objects.count() + 1
            self.reference = f"RF-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


# ─── Trésorerie avancée : Comptes bancaires ───────────────────────────────────

class CompteBancaire(models.Model):
    TYPE_CHOICES = [
        ('courant', 'Compte courant'),
        ('epargne', 'Compte épargne'),
        ('projet', 'Compte projet dédié'),
        ('transit', 'Compte de transit'),
    ]

    code = models.CharField(max_length=20, blank=True)
    intitule = models.CharField(max_length=200)
    type_compte = models.CharField(max_length=15, choices=TYPE_CHOICES, default='courant')
    banque = models.CharField(max_length=200)
    numero_compte = models.CharField(max_length=50, blank=True)
    rib = models.CharField(max_length=100, blank=True, verbose_name='RIB/IBAN')
    devise = models.CharField(max_length=5, choices=DEVISE_CHOICES, default='XOF')
    solde_initial = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    solde_actuel = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_ouverture = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comptes_bancaires',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comptes_bancaires',
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comptes_bancaires_geres',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compte bancaire'
        ordering = ['banque', 'intitule']

    def __str__(self):
        return f"[{self.code}] {self.intitule} — {self.banque}"

    def save(self, *args, **kwargs):
        if not self.code:
            count = CompteBancaire.objects.count() + 1
            self.code = f"CB-{count:04d}"
        super().save(*args, **kwargs)

    def recalculer_solde(self):
        """Recalcule le solde actuel à partir de solde_initial + tous les mouvements."""
        from django.db.models import Sum as DSum
        entrees = self.mouvements.filter(type_mouvement='credit').aggregate(s=DSum('montant'))['s'] or 0
        sorties = self.mouvements.filter(type_mouvement='debit').aggregate(s=DSum('montant'))['s'] or 0
        self.solde_actuel = self.solde_initial + entrees - sorties
        self.save(update_fields=['solde_actuel'])
        return self.solde_actuel


class MouvementBancaire(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Crédit (entrée)'),
        ('debit', 'Débit (sortie)'),
    ]

    compte = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name='mouvements')
    date_operation = models.DateField()
    date_valeur = models.DateField(null=True, blank=True)
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    libelle = models.CharField(max_length=300)
    montant = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    solde_apres = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    reference_externe = models.CharField(max_length=100, blank=True)
    rapproche = models.BooleanField(default=False)

    # Liaisons optionnelles avec les opérations ERP
    depense = models.ForeignKey(
        Depense, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mouvements_bancaires',
    )
    convention = models.ForeignKey(
        Convention, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mouvements_bancaires',
    )

    notes = models.TextField(blank=True)
    saisi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='mouvements_bancaires_saisis',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mouvement bancaire'
        ordering = ['-date_operation', '-created_at']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} {self.montant} — {self.date_operation}"


class RapprochementBancaire(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('cloture', 'Clôturé'),
    ]

    compte = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name='rapprochements')
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    solde_releve = models.DecimalField(
        max_digits=20, decimal_places=2,
        help_text="Solde figurant sur le relevé bancaire officiel."
    )
    solde_comptable = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        help_text="Solde calculé dans l'ERP à la date de fin de période."
    )
    ecart = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    nb_mouvements_rapproches = models.IntegerField(default=0)
    nb_mouvements_non_rapproches = models.IntegerField(default=0)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_cours')
    observations = models.TextField(blank=True)
    effectue_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='rapprochements_effectues',
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapprochements_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rapprochement bancaire'
        ordering = ['-periode_fin']

    def __str__(self):
        return f"Rapprochement {self.compte.code} — {self.periode_debut}/{self.periode_fin}"

    def calculer_ecart(self):
        self.ecart = self.solde_releve - self.solde_comptable
        self.save(update_fields=['ecart'])
