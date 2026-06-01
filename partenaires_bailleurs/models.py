from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M39 : Partenaires et bailleurs ──────────────────────────────────────────

class Partenaire(models.Model):
    TYPE_CHOICES = [
        ('ong', 'ONG'), ('bailleur', 'Bailleur de fonds'),
        ('institution_publique', 'Institution publique'),
        ('entreprise', 'Entreprise privée'), ('consultant', 'Cabinet / Consultant'),
        ('universite', 'Université / Recherche'),
        ('collectivite', 'Collectivité territoriale'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'), ('inactif', 'Inactif'), ('potentiel', 'Potentiel'),
    ]

    nom = models.CharField(max_length=300)
    sigle = models.CharField(max_length=50, blank=True)
    type_partenaire = models.CharField(max_length=25, choices=TYPE_CHOICES, default='ong')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='actif')
    pays = models.CharField(max_length=100, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    adresse = models.TextField(blank=True)
    site_web = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    contact_principal = models.CharField(max_length=200, blank=True)
    email_contact = models.EmailField(blank=True)
    telephone_contact = models.CharField(max_length=30, blank=True)
    secteurs_intervention = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='partenaires/logos/', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notes = models.TextField(blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='partenaires_crees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Partenaire'
        ordering = ['nom']

    def __str__(self):
        return f"[{self.sigle}] {self.nom}" if self.sigle else self.nom


class ContactPartenaire(models.Model):
    ROLE_CHOICES = [
        ('directeur', 'Directeur/Directrice'), ('coordinateur', 'Coordinateur/trice'),
        ('charge_programme', 'Chargé de programme'), ('financier', 'Responsable financier'),
        ('technique', 'Expert technique'), ('autre', 'Autre'),
    ]

    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name='contacts')
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default='autre')
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    est_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Contact partenaire'

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.partenaire.nom}"


class LiaisonProjetPartenaire(models.Model):
    ROLE_CHOICES = [
        ('bailleur_principal', 'Bailleur principal'),
        ('bailleur_secondaire', 'Bailleur secondaire'),
        ('partenaire_execution', 'Partenaire d\'exécution'),
        ('partenaire_technique', 'Partenaire technique'),
        ('sous_traitant', 'Sous-traitant'),
    ]

    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name='liaisons_projet')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.CASCADE,
                                related_name='liaisons_partenaire')
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default='partenaire_execution')
    montant_finance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Liaison projet-partenaire'
        unique_together = ['partenaire', 'projet', 'role']

    def __str__(self):
        return f"{self.partenaire.nom} → {self.projet.titre} ({self.get_role_display()})"


# ─── M40 : Conventions et accords ────────────────────────────────────────────

class Convention(models.Model):
    TYPE_CHOICES = [
        ('convention', 'Convention'), ('accord', 'Accord'),
        ('protocole', 'Protocole'), ('contrat', 'Contrat'),
        ('mou', 'Mémorandum (MoU)'), ('lettre_accord', "Lettre d'accord"),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'), ('en_validation', 'En validation'),
        ('valide', 'Validé'), ('signe', 'Signé'),
        ('actif', 'Actif'), ('suspendu', 'Suspendu'),
        ('expire', 'Expiré'), ('resilie', 'Résilié'), ('archive', 'Archivé'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    intitule = models.CharField(max_length=300)
    type_convention = models.CharField(max_length=20, choices=TYPE_CHOICES, default='convention')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name='conventions')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='conventions_partenaire')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='conventions_partenaire')
    objet = models.TextField()
    montant = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    devise = models.CharField(max_length=5, default='XOF')
    date_signature = models.DateField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    date_expiration_alerte = models.DateField(null=True, blank=True,
                                               help_text="Date pour déclencher l'alerte de renouvellement")
    signataire_interne = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='conventions_signees')
    signataire_externe = models.CharField(max_length=200, blank=True)
    clauses_principales = models.TextField(blank=True)
    obligations_parties = models.TextField(blank=True)
    conditions_renouvellement = models.TextField(blank=True)
    fichier = models.FileField(upload_to='conventions/%Y/', null=True, blank=True)
    document_ged = models.ForeignKey('ged.Document', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='conventions')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     related_name='conventions_suivies')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Convention'
        ordering = ['-date_signature', '-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.intitule} — {self.partenaire.nom}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Convention.objects.count() + 1
            self.reference = f"CONV-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def est_expiree(self):
        return self.date_fin and self.date_fin < timezone.now().date()

    @property
    def jours_avant_expiration(self):
        if not self.date_fin:
            return None
        delta = self.date_fin - timezone.now().date()
        return delta.days


class RenouvellementConvention(models.Model):
    convention = models.ForeignKey(Convention, on_delete=models.CASCADE, related_name='renouvellements')
    nouvelle_date_fin = models.DateField()
    nouveau_montant = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    motif = models.TextField(blank=True)
    date_signature = models.DateField(null=True, blank=True)
    fichier = models.FileField(upload_to='conventions/renouvellements/%Y/', null=True, blank=True)
    effectue_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                      related_name='renouvellements_conventions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Renouvellement convention'
        ordering = ['-created_at']

    def __str__(self):
        return f"Renouvellement {self.convention.reference} → {self.nouvelle_date_fin}"


# ─── M44 : Portail externe ────────────────────────────────────────────────────

class AccesPortailPartenaire(models.Model):
    NIVEAU_CHOICES = [
        ('lecture', 'Lecture seule'),
        ('depot', 'Lecture + Dépôt documents'),
        ('interaction', 'Interaction complète'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'), ('suspendu', 'Suspendu'), ('expire', 'Expiré'),
    ]

    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name='acces_portail')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='acces_portail_partenaire')
    niveau_acces = models.CharField(max_length=15, choices=NIVEAU_CHOICES, default='lecture')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    projets_accessibles = models.ManyToManyField('programmes_projets.Projet',
                                                   related_name='acces_portail', blank=True)
    programmes_accessibles = models.ManyToManyField('programmes_projets.Programme',
                                                      related_name='acces_portail', blank=True)
    date_debut = models.DateField(default=timezone.now)
    date_fin = models.DateField(null=True, blank=True)
    accorde_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, related_name='acces_portail_accordes')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Accès portail partenaire'
        unique_together = ['partenaire', 'utilisateur']

    def __str__(self):
        return f"{self.partenaire.nom} — {self.utilisateur} ({self.get_niveau_acces_display()})"


class DepotDocumentPortail(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé'), ('rejete', 'Rejeté'),
    ]

    partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, related_name='depots_documents')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='depots_portail')
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='portail/documents/%Y/%m/')
    type_document = models.CharField(max_length=50, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    depose_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='depots_portail')
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='depots_valides')
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dépôt document portail'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.partenaire.nom} — {self.titre}"
