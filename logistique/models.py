from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M38 : Parc automobile ────────────────────────────────────────────────────

class Vehicule(models.Model):
    TYPE_CHOICES = [
        ('voiture', 'Voiture'), ('4x4', '4x4 / SUV'), ('moto', 'Moto'),
        ('camion', 'Camion'), ('minibus', 'Minibus'), ('bateau', 'Bateau'),
    ]
    STATUT_CHOICES = [
        ('disponible', 'Disponible'), ('en_mission', 'En mission'),
        ('en_entretien', 'En entretien'), ('en_panne', 'En panne'),
        ('reforme', 'Réformé'), ('loue', 'Loué'),
    ]

    immatriculation = models.CharField(max_length=30, unique=True)
    type_vehicule = models.CharField(max_length=10, choices=TYPE_CHOICES, default='voiture')
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100, blank=True)
    annee = models.IntegerField(null=True, blank=True)
    couleur = models.CharField(max_length=50, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='disponible')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='vehicules')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='vehicules')
    kilometrage_actuel = models.IntegerField(default=0)
    date_acquisition = models.DateField(null=True, blank=True)
    valeur_acquisition = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date_expiration_assurance = models.DateField(null=True, blank=True)
    date_expiration_vignette = models.DateField(null=True, blank=True)
    date_prochain_entretien = models.DateField(null=True, blank=True)
    km_prochain_entretien = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Véhicule'
        ordering = ['immatriculation']

    def __str__(self):
        return f"[{self.immatriculation}] {self.marque} {self.modele}"

    @property
    def est_assurance_expiree(self):
        return self.date_expiration_assurance and self.date_expiration_assurance < timezone.now().date()


class MissionVehicule(models.Model):
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'), ('en_cours', 'En cours'),
        ('terminee', 'Terminée'), ('annulee', 'Annulée'),
    ]

    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='missions')
    conducteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='missions_vehicule')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='missions_vehicule')
    activite = models.ForeignKey('execution.ActiviteExecution', on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='missions_vehicule')
    objet = models.CharField(max_length=300)
    lieu_depart = models.CharField(max_length=200)
    lieu_arrivee = models.CharField(max_length=200)
    date_depart = models.DateTimeField()
    date_retour_prevue = models.DateTimeField(null=True, blank=True)
    date_retour_reelle = models.DateTimeField(null=True, blank=True)
    km_depart = models.IntegerField(default=0)
    km_retour = models.IntegerField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')
    carburant_litres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    cout_carburant = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)
    autorise_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='missions_autorisees')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mission véhicule'
        ordering = ['-date_depart']

    def __str__(self):
        return f"{self.vehicule.immatriculation} — {self.objet} ({self.date_depart.date()})"

    @property
    def distance(self):
        if self.km_retour and self.km_depart:
            return self.km_retour - self.km_depart
        return None


class EntretienVehicule(models.Model):
    TYPE_CHOICES = [
        ('vidange', 'Vidange'), ('revision', 'Révision'),
        ('reparation', 'Réparation'), ('controle_technique', 'Contrôle technique'),
        ('pneumatiques', 'Pneumatiques'), ('autre', 'Autre'),
    ]

    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='entretiens')
    type_entretien = models.CharField(max_length=20, choices=TYPE_CHOICES, default='revision')
    description = models.TextField()
    date_entretien = models.DateField()
    km_entretien = models.IntegerField(null=True, blank=True)
    prestataire = models.CharField(max_length=200, blank=True)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prochaine_echeance_date = models.DateField(null=True, blank=True)
    prochaine_echeance_km = models.IntegerField(null=True, blank=True)
    facture = models.FileField(upload_to='logistique/entretiens/%Y/', null=True, blank=True)
    effectue_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                      related_name='entretiens_saisis')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entretien véhicule'
        ordering = ['-date_entretien']

    def __str__(self):
        return f"{self.vehicule.immatriculation} — {self.get_type_entretien_display()} ({self.date_entretien})"


# ─── M38 : Équipements ────────────────────────────────────────────────────────

class Equipement(models.Model):
    TYPE_CHOICES = [
        ('informatique', 'Informatique'), ('bureau', 'Mobilier de bureau'),
        ('terrain', 'Matériel terrain'), ('communication', 'Communication'),
        ('vehicule', 'Véhicule'), ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('disponible', 'Disponible'), ('affecte', 'Affecté'),
        ('en_reparation', 'En réparation'), ('hors_service', 'Hors service'),
        ('perdu', 'Perdu'), ('reforme', 'Réformé'),
    ]

    code_inventaire = models.CharField(max_length=30, blank=True, unique=True)
    nom = models.CharField(max_length=200)
    type_equipement = models.CharField(max_length=20, choices=TYPE_CHOICES, default='informatique')
    marque = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='disponible')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='equipements')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='equipements')
    affecte_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='equipements_affectes')
    lieu = models.CharField(max_length=200, blank=True)
    date_acquisition = models.DateField(null=True, blank=True)
    valeur_acquisition = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date_fin_garantie = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='logistique/equipements/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Équipement'
        ordering = ['type_equipement', 'nom']

    def __str__(self):
        return f"[{self.code_inventaire}] {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code_inventaire:
            count = Equipement.objects.count() + 1
            self.code_inventaire = f"EQ-{timezone.now().year}-{count:05d}"
        super().save(*args, **kwargs)


# ─── M38 : Gestion des stocks ─────────────────────────────────────────────────

class Magasin(models.Model):
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    adresse = models.CharField(max_length=300, blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     related_name='magasins_responsable')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='magasins')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='magasins')
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Magasin'
        ordering = ['nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}" if self.code else self.nom


class ArticleStock(models.Model):
    UNITE_CHOICES = [
        ('piece', 'Pièce'), ('kg', 'Kilogramme'), ('litre', 'Litre'),
        ('boite', 'Boîte'), ('carton', 'Carton'), ('rame', 'Rame'), ('autre', 'Autre'),
    ]

    code = models.CharField(max_length=30, blank=True)
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES, default='piece')
    categorie = models.CharField(max_length=100, blank=True)
    stock_alerte = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                        help_text="Seuil de réapprovisionnement")
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Article stock'
        ordering = ['categorie', 'nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            count = ArticleStock.objects.count() + 1
            self.code = f"ART-{count:05d}"
        super().save(*args, **kwargs)


class LigneStock(models.Model):
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name='lignes_stock')
    article = models.ForeignKey(ArticleStock, on_delete=models.CASCADE, related_name='lignes_stock')
    quantite = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valeur_totale = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ligne stock'
        unique_together = ['magasin', 'article']

    def __str__(self):
        return f"{self.magasin.nom} — {self.article.nom}: {self.quantite}"

    @property
    def est_sous_alerte(self):
        return self.quantite <= self.article.stock_alerte


class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'), ('sortie', 'Sortie'), ('transfert', 'Transfert'),
        ('inventaire', 'Ajustement inventaire'), ('perte', 'Perte/Détérioration'),
    ]

    article = models.ForeignKey(ArticleStock, on_delete=models.CASCADE, related_name='mouvements')
    magasin_source = models.ForeignKey(Magasin, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='mouvements_sortie')
    magasin_destination = models.ForeignKey(Magasin, on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='mouvements_entree')
    type_mouvement = models.CharField(max_length=15, choices=TYPE_CHOICES)
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valeur_totale = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reference_document = models.CharField(max_length=100, blank=True)
    motif = models.TextField(blank=True)
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='mouvements_stock')
    effectue_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                      related_name='mouvements_stock')
    date_mouvement = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mouvement stock'
        ordering = ['-date_mouvement', '-created_at']

    def __str__(self):
        return f"[{self.get_type_mouvement_display()}] {self.article.nom} × {self.quantite}"

    def save(self, *args, **kwargs):
        self.valeur_totale = float(self.quantite) * float(self.prix_unitaire)
        super().save(*args, **kwargs)
