import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M24 : Plan de classement documentaire ────────────────────────────────────

class Categorie(models.Model):
    DOMAINE_CHOICES = [
        ('projet', 'Documents projets'),
        ('administratif', 'Documents administratifs'),
        ('financier', 'Documents financiers'),
        ('rh', 'Documents RH'),
        ('juridique', 'Documents juridiques'),
        ('technique', 'Documents techniques'),
        ('qualite', 'Qualité / Procédures'),
        ('bibliotheque', 'Bibliothèque / Modèles'),
    ]

    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    domaine = models.CharField(max_length=20, choices=DOMAINE_CHOICES, default='projet')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sous_categories'
    )
    icone = models.CharField(max_length=50, blank=True)
    couleur = models.CharField(max_length=7, default='#3388ff')
    ordre = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    duree_conservation_ans = models.IntegerField(
        null=True, blank=True,
        help_text="Durée de conservation en années. Null = permanent."
    )

    class Meta:
        verbose_name = 'Catégorie GED'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}" if self.code else self.nom


# ─── M24 : Document ───────────────────────────────────────────────────────────

class Document(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_revision', 'En révision'),
        ('soumis', 'Soumis pour validation'),
        ('approuve', 'Approuvé'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
        ('obsolete', 'Obsolète'),
        ('a_detruire', 'À détruire'),
        ('detruit', 'Détruit'),
    ]
    CONFIDENTIALITE_CHOICES = [
        ('public', 'Public'),
        ('interne', 'Interne'),
        ('confidentiel', 'Confidentiel'),
        ('tres_confidentiel', 'Très confidentiel'),
        ('secret', 'Secret'),
    ]
    LANGUE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'Anglais'),
        ('ar', 'Arabe'),
        ('pt', 'Portugais'),
        ('es', 'Espagnol'),
    ]
    TYPE_DOC_CHOICES = [
        ('tdr', 'Termes de référence'),
        ('rapport', 'Rapport'),
        ('livrable', 'Livrable'),
        ('cadre_logique', 'Cadre logique'),
        ('plan_action', "Plan d'action"),
        ('courrier', 'Courrier'),
        ('note_service', 'Note de service'),
        ('decision', 'Décision'),
        ('pv', 'Procès-verbal'),
        ('facture', 'Facture'),
        ('contrat', 'Contrat'),
        ('bon_commande', 'Bon de commande'),
        ('budget', 'Budget'),
        ('etat_financier', 'État financier'),
        ('contrat_rh', 'Contrat RH'),
        ('evaluation_rh', 'Évaluation RH'),
        ('procedure', 'Procédure'),
        ('modele', 'Modèle'),
        ('autre', 'Autre'),
    ]

    # Identification
    reference = models.CharField(max_length=50, blank=True, unique=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_document = models.CharField(max_length=20, choices=TYPE_DOC_CHOICES, default='rapport')
    categorie = models.ForeignKey(
        Categorie, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents'
    )

    # Rattachements ERP
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_ged'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_ged'
    )
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_ged'
    )

    # Fichier
    fichier = models.FileField(upload_to='ged/%Y/%m/', null=True, blank=True)
    type_fichier = models.CharField(max_length=20, blank=True)
    taille_fichier = models.BigIntegerField(default=0)
    empreinte_sha256 = models.CharField(max_length=64, blank=True)
    url_externe = models.URLField(blank=True)

    # Versioning
    version = models.CharField(max_length=10, default='1.0')
    document_parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='versions'
    )
    est_version_courante = models.BooleanField(default=True)

    # Métadonnées
    langue = models.CharField(max_length=5, choices=LANGUE_CHOICES, default='fr')
    mots_cles = models.TextField(blank=True)
    source = models.CharField(max_length=300, blank=True)
    auteur_externe = models.CharField(max_length=200, blank=True)

    # Accès et sécurité
    confidentialite = models.CharField(
        max_length=20, choices=CONFIDENTIALITE_CHOICES, default='interne'
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')

    # OCR
    texte_ocr = models.TextField(blank=True, help_text="Texte extrait par OCR")
    ocr_effectue = models.BooleanField(default=False)
    date_ocr = models.DateTimeField(null=True, blank=True)

    # IA
    resume_auto = models.TextField(blank=True)
    mots_cles_auto = models.TextField(blank=True)
    categorie_suggeree = models.CharField(max_length=200, blank=True)
    score_doublon = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Archivage
    date_expiration = models.DateField(null=True, blank=True)
    date_archivage = models.DateField(null=True, blank=True)
    date_destruction_prevue = models.DateField(null=True, blank=True)
    horodatage = models.DateTimeField(null=True, blank=True)

    # Workflow
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='documents_ged_crees'
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents_ged_valides'
    )
    date_validation = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document GED'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre} v{self.version}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Document.objects.count() + 1
            self.reference = f"DOC-{timezone.now().year}-{count:05d}"
        super().save(*args, **kwargs)

    @property
    def est_en_retard(self):
        return (
            self.date_expiration
            and self.date_expiration < timezone.now().date()
            and self.statut not in ('archive', 'detruit')
        )

    def soumettre(self):
        self.statut = 'soumis'
        self.save(update_fields=['statut'])

    def approuver(self, user):
        self.statut = 'approuve'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])

    def publier(self):
        if self.statut not in ('approuve',):
            raise ValueError("Seul un document approuvé peut être publié.")
        self.statut = 'publie'
        self.horodatage = timezone.now()
        self.save(update_fields=['statut', 'horodatage'])

    def archiver(self):
        self.statut = 'archive'
        self.date_archivage = timezone.now().date()
        self.save(update_fields=['statut', 'date_archivage'])

    def creer_nouvelle_version(self, user, fichier=None):
        parts = self.version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        nouvelle_version = '.'.join(parts)
        Document.objects.filter(id=self.id).update(est_version_courante=False)
        nouveau = Document.objects.create(
            titre=self.titre,
            description=self.description,
            type_document=self.type_document,
            categorie=self.categorie,
            programme=self.programme,
            projet=self.projet,
            activite=self.activite,
            fichier=fichier or self.fichier,
            type_fichier=self.type_fichier,
            version=nouvelle_version,
            document_parent=self.document_parent or self,
            est_version_courante=True,
            confidentialite=self.confidentialite,
            langue=self.langue,
            mots_cles=self.mots_cles,
            auteur=user,
            statut='brouillon',
        )
        return nouveau


class VersionDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='historique_versions')
    numero_version = models.CharField(max_length=10)
    fichier = models.FileField(upload_to='ged/versions/%Y/%m/', null=True, blank=True)
    commentaire = models.TextField(blank=True)
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='versions_document_creees'
    )
    taille_fichier = models.BigIntegerField(default=0)
    empreinte_sha256 = models.CharField(max_length=64, blank=True)
    date_version = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Version document'
        ordering = ['-date_version']

    def __str__(self):
        return f"{self.document.reference} v{self.numero_version}"


class DossierDocument(models.Model):
    """Dossier / Répertoire virtuel pour organiser les documents."""
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sous_dossiers'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dossiers_ged'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dossiers_ged'
    )
    documents = models.ManyToManyField(Document, related_name='dossiers', blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='dossiers_responsable'
    )
    confidentiel = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    icone = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='dossiers_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dossier document'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom


# ─── Workflow de validation ───────────────────────────────────────────────────

class WorkflowValidation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('commente', 'Commenté'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='workflow_validations')
    ordre = models.IntegerField(default=0)
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='validations_ged'
    )
    role_validateur = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    commentaire = models.TextField(blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Validation workflow GED'
        ordering = ['ordre']

    def approuver(self, user, commentaire=''):
        self.statut = 'approuve'
        self.validateur = user
        self.commentaire = commentaire
        self.date_validation = timezone.now()
        self.save()

    def rejeter(self, user, commentaire=''):
        self.statut = 'rejete'
        self.validateur = user
        self.commentaire = commentaire
        self.date_validation = timezone.now()
        self.save()
        self.document.statut = 'en_revision'
        self.document.save(update_fields=['statut'])


# ─── Signature électronique ───────────────────────────────────────────────────

class SignatureElectronique(models.Model):
    TYPE_CHOICES = [
        ('simple', 'Signature simple'),
        ('avancee', 'Signature avancée'),
        ('multiple', 'Signature multiple'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('signe', 'Signé'),
        ('refuse', 'Refusé'),
        ('expire', 'Expiré'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signatures')
    type_signature = models.CharField(max_length=15, choices=TYPE_CHOICES, default='simple')
    signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='signatures_effectuees'
    )
    ordre = models.IntegerField(default=0)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    date_signature = models.DateTimeField(null=True, blank=True)
    date_expiration = models.DateField(null=True, blank=True)
    empreinte = models.CharField(max_length=128, blank=True)
    commentaire = models.TextField(blank=True)
    ip_signataire = models.GenericIPAddressField(null=True, blank=True)
    certificat = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Signature électronique'
        ordering = ['ordre']

    def __str__(self):
        return f"Signature {self.document.reference} — {self.signataire}"

    def signer(self, user, ip=None):
        import hashlib
        contenu = f"{self.document.reference}-{user.id}-{timezone.now().isoformat()}"
        self.empreinte = hashlib.sha256(contenu.encode()).hexdigest()
        self.statut = 'signe'
        self.signataire = user
        self.date_signature = timezone.now()
        self.ip_signataire = ip
        self.save()


# ─── Partage documentaire ─────────────────────────────────────────────────────

class LienPartage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='liens_partage')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='liens_partage_crees'
    )
    email_destinataire = models.EmailField(blank=True)
    date_expiration = models.DateTimeField(null=True, blank=True)
    mot_de_passe = models.CharField(max_length=128, blank=True)
    nb_telechargements_max = models.IntegerField(null=True, blank=True)
    nb_telechargements = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lien de partage'
        ordering = ['-created_at']

    def __str__(self):
        return f"Lien {str(self.token)[:8]}... — {self.document.titre}"

    @property
    def est_expire(self):
        return self.date_expiration and self.date_expiration < timezone.now()

    @property
    def est_valide(self):
        if not self.actif:
            return False
        if self.est_expire:
            return False
        if self.nb_telechargements_max and self.nb_telechargements >= self.nb_telechargements_max:
            return False
        return True


class AccesDocument(models.Model):
    NIVEAU_CHOICES = [
        ('lecture', 'Lecture'),
        ('telechargement', 'Téléchargement'),
        ('modification', 'Modification'),
        ('administration', 'Administration'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='acces')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acces_documents'
    )
    niveau = models.CharField(max_length=15, choices=NIVEAU_CHOICES, default='lecture')
    date_expiration = models.DateField(null=True, blank=True)
    accorde_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='acces_accordes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Accès document"
        unique_together = ['document', 'utilisateur']


# ─── Audit et traçabilité ─────────────────────────────────────────────────────

class AuditDocument(models.Model):
    ACTION_CHOICES = [
        ('consultation', 'Consultation'),
        ('telechargement', 'Téléchargement'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('archivage', 'Archivage'),
        ('restauration', 'Restauration'),
        ('partage', 'Partage'),
        ('signature', 'Signature'),
        ('validation', 'Validation'),
        ('destruction', 'Destruction'),
    ]

    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='audit_ged'
    )
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Audit document'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} — {self.document} — {self.created_at}"


# ─── Commentaires sur documents ───────────────────────────────────────────────

class CommentaireDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='commentaires_ged'
    )
    contenu = models.TextField()
    en_reponse_a = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reponses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Commentaire document'
        ordering = ['created_at']


# ─── M25 : Archivage électronique ────────────────────────────────────────────

class PlanConservation(models.Model):
    categorie = models.OneToOneField(
        Categorie, on_delete=models.CASCADE, related_name='plan_conservation'
    )
    duree_active_ans = models.IntegerField(default=5, help_text="Durée en utilisation active")
    duree_intermediaire_ans = models.IntegerField(default=5, help_text="Durée en archivage intermédiaire")
    duree_totale_ans = models.IntegerField(null=True, blank=True, help_text="Null = conservation permanente")
    sort_final = models.CharField(
        max_length=20,
        choices=[('destruction', 'Destruction'), ('conservation', 'Conservation permanente'), ('tri', 'Tri')],
        default='conservation'
    )
    base_legale = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plan de conservation'

    def __str__(self):
        return f"Conservation — {self.categorie.nom}"


class BoiteArchive(models.Model):
    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('fermee', 'Fermée'),
        ('versee', 'Versée aux archives'),
        ('detruite', 'Détruite'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    intitule = models.CharField(max_length=300)
    categorie = models.ForeignKey(
        Categorie, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boites_archives'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boites_archives'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='boites_archives'
    )
    service_producteur = models.CharField(max_length=200, blank=True)
    annee_debut = models.IntegerField(null=True, blank=True)
    annee_fin = models.IntegerField(null=True, blank=True)
    localisation = models.CharField(max_length=200, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='ouverte')
    date_versement = models.DateField(null=True, blank=True)
    date_destruction_prevue = models.DateField(null=True, blank=True)
    chiffree = models.BooleanField(default=False)
    cle_chiffrement = models.TextField(
        blank=True,
        help_text="Clé AES-256 wrappée (base64). Générée automatiquement si chiffree=True."
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='boites_creees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Boîte d'archives"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.intitule}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = BoiteArchive.objects.count() + 1
            self.reference = f"BA-{timezone.now().year}-{count:04d}"
        if self.chiffree and not self.cle_chiffrement:
            from ged.services.chiffrement import generer_cle_boite
            self.cle_chiffrement = generer_cle_boite()
        super().save(*args, **kwargs)


class DocumentArchive(models.Model):
    """Association document → boîte d'archive avec métadonnées archivistiques."""
    boite = models.ForeignKey(BoiteArchive, on_delete=models.CASCADE, related_name='documents_archive')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='archives')
    reference_archive = models.CharField(max_length=50, blank=True)
    date_archivage = models.DateField(auto_now_add=True)
    archive_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='archivages_effectues'
    )
    horodatage_legal = models.DateTimeField(auto_now_add=True)
    empreinte_integrite = models.CharField(max_length=64, blank=True)
    # Coffre-fort : copie chiffrée du fichier (AES-256-GCM)
    fichier_chiffre = models.FileField(
        upload_to='ged/coffre/%Y/%m/', null=True, blank=True,
        help_text="Copie chiffrée AES-256-GCM du fichier (coffre-fort numérique)."
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Document archivé'
        unique_together = ['boite', 'document']

    def __str__(self):
        return f"{self.document.reference} → {self.boite.reference}"


class DemandeDestruction(models.Model):
    STATUT_CHOICES = [
        ('proposition', 'Proposition'),
        ('valide', 'Validé'),
        ('autorise', 'Autorisé'),
        ('execute', 'Exécuté'),
        ('rejete', 'Rejeté'),
    ]

    boite = models.ForeignKey(
        BoiteArchive, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='demandes_destruction'
    )
    documents = models.ManyToManyField(Document, related_name='demandes_destruction', blank=True)
    motif = models.TextField()
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='proposition')
    propose_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='destructions_proposees'
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='destructions_validees'
    )
    autorise_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='destructions_autorisees'
    )
    date_proposition = models.DateField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_autorisation = models.DateTimeField(null=True, blank=True)
    date_execution = models.DateTimeField(null=True, blank=True)
    pv_destruction = models.FileField(upload_to='pvs_destruction/%Y/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Demande de destruction'
        ordering = ['-date_proposition']

    def __str__(self):
        return f"Destruction {self.id} — {self.get_statut_display()}"


# ─── Bibliothèque documentaire ────────────────────────────────────────────────

class ModeleDocument(models.Model):
    TYPE_CHOICES = [
        ('tdr', 'Modèle TDR'),
        ('rapport', 'Modèle rapport'),
        ('courrier', 'Modèle courrier'),
        ('contrat', 'Modèle contrat'),
        ('budget', 'Modèle budget'),
        ('swot', 'Modèle SWOT'),
        ('plan_action', "Modèle plan d'action"),
        ('fiche', 'Modèle fiche'),
        ('autre', 'Autre modèle'),
    ]

    code = models.CharField(max_length=20, blank=True)
    titre = models.CharField(max_length=300)
    type_modele = models.CharField(max_length=15, choices=TYPE_CHOICES, default='rapport')
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='modeles/%Y/', null=True, blank=True)
    instructions = models.TextField(blank=True)
    langue = models.CharField(max_length=5, choices=Document.LANGUE_CHOICES, default='fr')
    version = models.CharField(max_length=10, default='1.0')
    actif = models.BooleanField(default=True)
    nb_utilisations = models.IntegerField(default=0)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='modeles_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Modèle de document'
        ordering = ['type_modele', 'titre']

    def __str__(self):
        return f"[{self.type_modele}] {self.titre}"


class EntreesBibliotheque(models.Model):
    CATEGORIE_CHOICES = [
        ('gestion_projet', 'Gestion de projet'),
        ('finance', 'Finance'),
        ('rh', 'Ressources humaines'),
        ('juridique', 'Juridique'),
        ('qualite', 'Qualité'),
        ('technique', 'Technique'),
        ('formation', 'Formation'),
    ]

    titre = models.CharField(max_length=300)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='gestion_projet')
    sous_categorie = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='bibliotheque/%Y/', null=True, blank=True)
    url_externe = models.URLField(blank=True)
    auteur = models.CharField(max_length=200, blank=True)
    organisation = models.CharField(max_length=200, blank=True)
    annee_publication = models.IntegerField(null=True, blank=True)
    langue = models.CharField(max_length=5, choices=Document.LANGUE_CHOICES, default='fr')
    mots_cles = models.TextField(blank=True)
    est_public = models.BooleanField(default=True)
    nb_telechargements = models.IntegerField(default=0)
    ajoute_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='entrees_bibliotheque_ajoutees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entrée bibliothèque'
        ordering = ['-created_at']

    def __str__(self):
        return self.titre
