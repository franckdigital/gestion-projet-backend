from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M27 : Courrier entrant ───────────────────────────────────────────────────

class CourrierEntrant(models.Model):
    URGENCE_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('tres_urgent', 'Très urgent'),
    ]
    CANAL_CHOICES = [
        ('papier', 'Papier / Dépôt physique'),
        ('email', 'Email'),
        ('portail', 'Portail'),
        ('fax', 'Fax'),
    ]
    STATUT_CHOICES = [
        ('recu', 'Reçu'),
        ('affecte', 'Affecté'),
        ('en_cours', 'En cours de traitement'),
        ('traite', 'Traité'),
        ('cloture', 'Clôturé'),
        ('archive', 'Archivé'),
    ]

    numero = models.CharField(max_length=30, blank=True)
    date_reception = models.DateField()
    expediteur = models.CharField(max_length=300)
    organisation_expediteur = models.CharField(max_length=300, blank=True)
    email_expediteur = models.EmailField(blank=True)
    objet = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    urgence = models.CharField(max_length=15, choices=URGENCE_CHOICES, default='normal')
    canal = models.CharField(max_length=10, choices=CANAL_CHOICES, default='papier')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='recu')

    # Liaison ERP
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_entrants'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_entrants'
    )

    # Fichier / scan
    fichier_scan = models.FileField(upload_to='courriers/entrants/%Y/%m/', null=True, blank=True)
    ocr_effectue = models.BooleanField(default=False)
    texte_ocr = models.TextField(blank=True)
    document_ged = models.ForeignKey(
        'ged.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_entrants'
    )

    # Affectation
    affecte_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_affectes'
    )
    date_affectation = models.DateTimeField(null=True, blank=True)
    instruction_affectation = models.TextField(blank=True)

    # Clôture
    date_traitement = models.DateField(null=True, blank=True)
    reponse_donnee = models.TextField(blank=True)

    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='courriers_enregistres'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Courrier entrant'
        ordering = ['-date_reception']

    def __str__(self):
        return f"[{self.numero}] {self.objet} — {self.expediteur}"

    def save(self, *args, **kwargs):
        if not self.numero:
            count = CourrierEntrant.objects.count() + 1
            self.numero = f"CE-{timezone.now().year}-{count:05d}"
        super().save(*args, **kwargs)

    def affecter(self, user, instruction=''):
        self.affecte_a = user
        self.date_affectation = timezone.now()
        self.instruction_affectation = instruction
        self.statut = 'affecte'
        self.save(update_fields=['affecte_a', 'date_affectation',
                                  'instruction_affectation', 'statut'])

    def cloturer(self, reponse=''):
        self.statut = 'cloture'
        self.date_traitement = timezone.now().date()
        self.reponse_donnee = reponse
        self.save(update_fields=['statut', 'date_traitement', 'reponse_donnee'])


# ─── M27 : Courrier sortant ───────────────────────────────────────────────────

class CourrierSortant(models.Model):
    TYPE_CHOICES = [
        ('lettre', 'Lettre'),
        ('note_service', 'Note de service'),
        ('decision', 'Décision'),
        ('circulaire', 'Circulaire'),
        ('correspondance', 'Correspondance partenaire'),
        ('rapport', 'Rapport'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_validation', 'En validation'),
        ('valide', 'Validé'),
        ('signe', 'Signé'),
        ('expedie', 'Expédié'),
        ('archive', 'Archivé'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    type_courrier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='lettre')
    objet = models.CharField(max_length=500)
    corps = models.TextField(blank=True)
    destinataire = models.CharField(max_length=300)
    organisation_destinataire = models.CharField(max_length=300, blank=True)
    email_destinataire = models.EmailField(blank=True)
    date_courrier = models.DateField(default=timezone.now)
    date_expedition = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    # Liaison ERP
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_sortants'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_sortants'
    )
    en_reponse_a = models.ForeignKey(
        CourrierEntrant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reponses'
    )

    # Fichier
    fichier = models.FileField(upload_to='courriers/sortants/%Y/%m/', null=True, blank=True)
    document_ged = models.ForeignKey(
        'ged.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_sortants'
    )
    modele_utilise = models.CharField(max_length=50, blank=True)

    # Workflow
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='courriers_rediges'
    )
    signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courriers_signes'
    )
    date_signature = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Courrier sortant'
        ordering = ['-date_courrier']

    def __str__(self):
        return f"[{self.reference}] {self.objet} → {self.destinataire}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = CourrierSortant.objects.count() + 1
            self.reference = f"CS-{timezone.now().year}-{count:05d}"
        super().save(*args, **kwargs)

    def signer(self, user):
        self.statut = 'signe'
        self.signataire = user
        self.date_signature = timezone.now()
        self.save(update_fields=['statut', 'signataire', 'date_signature'])

    def expedier(self):
        self.statut = 'expedie'
        self.date_expedition = timezone.now().date()
        self.save(update_fields=['statut', 'date_expedition'])


# ─── Parapheur électronique ───────────────────────────────────────────────────

class CircuitValidation(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Circuit de validation'

    def __str__(self):
        return self.nom


class EtapeCircuit(models.Model):
    circuit = models.ForeignKey(CircuitValidation, on_delete=models.CASCADE, related_name='etapes')
    ordre = models.IntegerField()
    nom_etape = models.CharField(max_length=100)
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='etapes_validation'
    )
    role = models.CharField(max_length=100, blank=True)
    obligatoire = models.BooleanField(default=True)
    delai_jours = models.IntegerField(default=2)

    class Meta:
        verbose_name = "Étape circuit"
        ordering = ['ordre']

    def __str__(self):
        return f"{self.circuit.nom} — Étape {self.ordre}: {self.nom_etape}"


class Parapheur(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
        ('signe', 'Signé'),
        ('archive', 'Archivé'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    intitule = models.CharField(max_length=300)
    circuit = models.ForeignKey(
        CircuitValidation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='parapheurs'
    )
    courrier_sortant = models.OneToOneField(
        CourrierSortant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='parapheur'
    )
    document_ged = models.ForeignKey(
        'ged.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='parapheurs'
    )
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_cours')
    etape_courante = models.IntegerField(default=1)
    soumis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='parapheurs_soumis'
    )
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_cloture = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Parapheur'
        ordering = ['-date_soumission']

    def __str__(self):
        return f"[{self.reference}] {self.intitule}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Parapheur.objects.count() + 1
            self.reference = f"PAR-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class VisaParapheur(models.Model):
    DECISION_CHOICES = [
        ('valide', 'Validé / Visé'),
        ('rejete', 'Rejeté'),
        ('commente', 'Commenté'),
        ('signe', 'Signé'),
        ('en_attente', 'En attente'),
    ]

    parapheur = models.ForeignKey(Parapheur, on_delete=models.CASCADE, related_name='visas')
    etape = models.ForeignKey(
        EtapeCircuit, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='visas'
    )
    ordre = models.IntegerField(default=0)
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='visas_donnes'
    )
    decision = models.CharField(max_length=15, choices=DECISION_CHOICES, default='en_attente')
    commentaire = models.TextField(blank=True)
    date_visa = models.DateTimeField(null=True, blank=True)
    delai_prevu = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Visa parapheur'
        ordering = ['ordre']

    def __str__(self):
        return f"Visa {self.ordre} — {self.parapheur.reference} — {self.get_decision_display()}"

    def viser(self, user, decision, commentaire=''):
        self.validateur = user
        self.decision = decision
        self.commentaire = commentaire
        self.date_visa = timezone.now()
        self.save()
        if decision == 'rejete':
            self.parapheur.statut = 'rejete'
            self.parapheur.save(update_fields=['statut'])
        elif not self.parapheur.visas.filter(decision='en_attente').exists():
            self.parapheur.statut = 'valide'
            self.parapheur.date_cloture = timezone.now()
            self.parapheur.save(update_fields=['statut', 'date_cloture'])


# ─── Diligences ───────────────────────────────────────────────────────────────

class Diligence(models.Model):
    TYPE_CHOICES = [
        ('tache', 'Tâche'),
        ('activite', 'Activité'),
        ('action', 'Action'),
        ('decision', 'Décision'),
    ]
    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('en_cours', 'En cours'),
        ('realisee', 'Réalisée'),
        ('cloturee', 'Clôturée'),
        ('annulee', 'Annulée'),
    ]

    courrier = models.ForeignKey(
        CourrierEntrant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diligences'
    )
    type_diligence = models.CharField(max_length=15, choices=TYPE_CHOICES, default='action')
    description = models.TextField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='diligences_responsable'
    )
    echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='ouverte')
    resultat = models.TextField(blank=True)
    assigne_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diligences_assignees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diligence'
        ordering = ['echeance']

    def __str__(self):
        return f"[{self.get_type_diligence_display()}] {self.description[:80]}"


# ─── Modèles de courriers sortants ───────────────────────────────────────────

class ModeleCourrierSortant(models.Model):
    TYPE_CHOICES = [
        ('lettre',         'Lettre'),
        ('note_service',   'Note de service'),
        ('decision',       'Décision'),
        ('circulaire',     'Circulaire'),
        ('correspondance', 'Correspondance partenaire'),
        ('rapport',        'Rapport'),
        ('autre',          'Autre'),
    ]

    nom = models.CharField(max_length=200)
    type_courrier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='lettre')
    description = models.TextField(blank=True)
    objet = models.CharField(max_length=300, blank=True)
    corps = models.TextField(blank=True, help_text='Corps du modèle avec variables {{nom_destinataire}}, {{date}}, etc.')
    actif = models.BooleanField(default=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='modeles_courrier_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Modèle de courrier'
        ordering = ['type_courrier', 'nom']

    def __str__(self):
        return f"[{self.get_type_courrier_display()}] {self.nom}"
