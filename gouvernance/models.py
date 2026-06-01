from django.db import models
from django.conf import settings


class Organisation(models.Model):
    TYPE_CHOICES = [
        ('ong', 'ONG'),
        ('administration', 'Administration publique'),
        ('projet', 'Projet/Programme'),
        ('entreprise', 'Entreprise privée'),
        ('institution', 'Institution internationale'),
    ]
    STATUT_CHOICES = [
        ('active', 'Active'),
        ('suspendue', 'Suspendue'),
        ('dissoute', 'Dissoute'),
    ]

    nom = models.CharField(max_length=300)
    sigle = models.CharField(max_length=30, blank=True)
    type_organisation = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='active')
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organisations/logos/', null=True, blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, default="Côte d'Ivoire")
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    date_creation = models.DateField(null=True, blank=True)
    numero_agrement = models.CharField(max_length=100, blank=True)
    directeur_general = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='organisations_dirigees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organisation'
        ordering = ['nom']

    def __str__(self):
        return self.sigle or self.nom


class Direction(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='directions')
    code = models.CharField(max_length=20)
    nom = models.CharField(max_length=200)
    sigle = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='directions_dirigees',
    )
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Direction'
        unique_together = ['organisation', 'code']
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.nom}"


class SousDirection(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='sous_directions')
    code = models.CharField(max_length=20)
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sous_directions_dirigees',
    )
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sous-direction'
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.nom}"


class Service(models.Model):
    direction = models.ForeignKey(
        Direction, on_delete=models.CASCADE, related_name='services', null=True, blank=True
    )
    sous_direction = models.ForeignKey(
        SousDirection, on_delete=models.CASCADE, related_name='services', null=True, blank=True
    )
    code = models.CharField(max_length=20)
    intitule = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='services_diriges',
    )
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Service'
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.intitule}"

    @property
    def organisation(self):
        if self.direction:
            return self.direction.organisation
        if self.sous_direction:
            return self.sous_direction.direction.organisation
        return None


class Site(models.Model):
    TYPE_CHOICES = [
        ('siege', 'Siège'),
        ('agence', 'Agence'),
        ('representation', 'Représentation régionale'),
        ('bureau_projet', 'Bureau de projet'),
        ('antenne', 'Antenne'),
    ]

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='sites')
    code = models.CharField(max_length=20)
    nom = models.CharField(max_length=200)
    type_site = models.CharField(max_length=20, choices=TYPE_CHOICES)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, default="Côte d'Ivoire")
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sites_diriges',
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Site'
        ordering = ['type_site', 'nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"


class Partenaire(models.Model):
    TYPE_CHOICES = [
        ('ong', 'ONG'),
        ('ministere', 'Ministère'),
        ('bailleur', 'Bailleur de fonds'),
        ('prestataire', 'Prestataire'),
        ('entreprise_privee', 'Entreprise privée'),
        ('institution_internationale', 'Institution internationale'),
        ('collectivite', 'Collectivité territoriale'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
    ]

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='partenaires')
    nom = models.CharField(max_length=300)
    sigle = models.CharField(max_length=30, blank=True)
    type_partenaire = models.CharField(max_length=30, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='actif')
    pays = models.CharField(max_length=100, blank=True)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    contact_nom = models.CharField(max_length=200, blank=True)
    contact_fonction = models.CharField(max_length=200, blank=True)
    contact_telephone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    date_debut_partenariat = models.DateField(null=True, blank=True)
    date_fin_partenariat = models.DateField(null=True, blank=True)
    domaines_intervention = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    logo = models.ImageField(upload_to='partenaires/logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Partenaire'
        ordering = ['nom']

    def __str__(self):
        return self.sigle or self.nom


class Bailleur(models.Model):
    TYPE_CHOICES = [
        ('bilateral', 'Bilatéral'),
        ('multilateral', 'Multilatéral'),
        ('prive', 'Privé'),
        ('national', 'National/Gouvernemental'),
        ('fondation', 'Fondation'),
    ]

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='bailleurs')
    nom = models.CharField(max_length=300)
    sigle = models.CharField(max_length=30, blank=True)
    type_bailleur = models.CharField(max_length=15, choices=TYPE_CHOICES)
    pays_origine = models.CharField(max_length=100, blank=True)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    contact_nom = models.CharField(max_length=200, blank=True)
    contact_fonction = models.CharField(max_length=200, blank=True)
    contact_telephone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    exigences_reporting = models.TextField(blank=True)
    conditions_financement = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    logo = models.ImageField(upload_to='bailleurs/logos/', null=True, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bailleur'
        ordering = ['nom']

    def __str__(self):
        return self.sigle or self.nom


class ComiteDirecteur(models.Model):
    STATUT_CHOICES = [
        ('programme', 'Programmé'),
        ('tenu', 'Tenu'),
        ('reporte', 'Reporté'),
        ('annule', 'Annulé'),
    ]

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='comites')
    intitule = models.CharField(max_length=200)
    date_tenue = models.DateTimeField()
    lieu = models.CharField(max_length=200, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='programme')
    ordre_du_jour = models.TextField(blank=True)
    compte_rendu = models.TextField(blank=True)
    president = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comites_presides'
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='comites_participant', blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comité directeur'
        ordering = ['-date_tenue']

    def __str__(self):
        return f"{self.intitule} — {self.date_tenue.strftime('%d/%m/%Y')}"
