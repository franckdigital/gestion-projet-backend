from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M41 : SIG avancé ────────────────────────────────────────────────────────

class ZoneSIG(models.Model):
    TYPE_CHOICES = [
        ('pays', 'Pays'), ('region', 'Région'), ('departement', 'Département'),
        ('commune', 'Commune'), ('village', 'Village / Localité'),
        ('zone_intervention', "Zone d'intervention"), ('perimetre', 'Périmètre projet'),
    ]

    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True)
    type_zone = models.CharField(max_length=25, choices=TYPE_CHOICES, default='commune')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='sous_zones')
    pays = models.CharField(max_length=100, blank=True)
    superficie_km2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    latitude_centre = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude_centre = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geojson = models.JSONField(default=dict, blank=True,
                                help_text="GeoJSON complet du polygone de la zone")
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Zone SIG'
        ordering = ['type_zone', 'nom']

    def __str__(self):
        return f"[{self.get_type_zone_display()}] {self.nom}"


class CoucheCartographique(models.Model):
    TYPE_CHOICES = [
        ('projets', 'Projets'), ('activites', 'Activités'),
        ('beneficiaires', 'Bénéficiaires'), ('partenaires', 'Partenaires'),
        ('infrastructures', 'Infrastructures'), ('risques', 'Risques'),
        ('indicateurs', 'Indicateurs S&E'), ('zones', 'Zones'),
        ('personnalisee', 'Couche personnalisée'),
    ]
    STYLE_CHOICES = [
        ('points', 'Points'), ('lignes', 'Lignes'),
        ('polygones', 'Polygones'), ('heatmap', 'Heatmap'),
        ('cluster', 'Clusters'),
    ]
    SOURCE_CHOICES = [
        ('openstreetmap', 'OpenStreetMap'), ('google_maps', 'Google Maps'),
        ('satellite', 'Satellite'), ('terrain', 'Terrain'), ('custom', 'Personnalisée'),
    ]

    nom = models.CharField(max_length=200)
    type_couche = models.CharField(max_length=20, choices=TYPE_CHOICES, default='projets')
    style_affichage = models.CharField(max_length=15, choices=STYLE_CHOICES, default='points')
    source_fond = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='openstreetmap')
    description = models.TextField(blank=True)
    couleur = models.CharField(max_length=7, default='#3388ff')
    icone = models.CharField(max_length=50, blank=True)
    opacite = models.DecimalField(max_digits=3, decimal_places=2, default=1)
    est_visible = models.BooleanField(default=True)
    est_publique = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    configuration = models.JSONField(default=dict, blank=True)
    filtre_programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                          null=True, blank=True)
    filtre_projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                       null=True, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='couches_cartographiques')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Couche cartographique'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"[{self.get_type_couche_display()}] {self.nom}"


class PointCartographie(models.Model):
    TYPE_CHOICES = [
        ('projet', 'Projet'), ('activite', 'Activité'),
        ('beneficiaire', 'Bénéficiaire'), ('infrastructure', 'Infrastructure'),
        ('partenaire', 'Partenaire'), ('collecte', 'Point de collecte'),
        ('risque', 'Risque'), ('ressource', 'Ressource'),
    ]

    couche = models.ForeignKey(CoucheCartographique, on_delete=models.CASCADE,
                                related_name='points', null=True, blank=True)
    type_point = models.CharField(max_length=20, choices=TYPE_CHOICES, default='projet')
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rayon_metres = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='points_sig_avances')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='points_sig_avances')
    zone = models.ForeignKey(ZoneSIG, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='points')
    valeur = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    unite = models.CharField(max_length=50, blank=True)
    couleur = models.CharField(max_length=7, default='#3388ff')
    icone = models.CharField(max_length=50, blank=True)
    proprietes = models.JSONField(default=dict, blank=True)
    image = models.ImageField(upload_to='sig/points/%Y/', null=True, blank=True)
    source_gps = models.CharField(max_length=50, blank=True)
    precision_gps = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actif = models.BooleanField(default=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='points_carto_crees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Point cartographique'
        ordering = ['type_point', 'titre']

    def __str__(self):
        return f"[{self.get_type_point_display()}] {self.titre} ({self.latitude}, {self.longitude})"


class InfrastructureSIG(models.Model):
    TYPE_CHOICES = [
        ('ecole', 'École'), ('hopital', 'Hôpital / Centre de santé'),
        ('puits', 'Puits / Forage'), ('route', 'Route'),
        ('pont', 'Pont'), ('marche', 'Marché'),
        ('bureau', 'Bureau / Siège'), ('entrepot', 'Entrepôt'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('operationnel', 'Opérationnel'), ('en_construction', 'En construction'),
        ('en_renovation', 'En rénovation'), ('abandonne', 'Abandonné'),
    ]

    nom = models.CharField(max_length=200)
    type_infrastructure = models.CharField(max_length=15, choices=TYPE_CHOICES, default='bureau')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='operationnel')
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    zone = models.ForeignKey(ZoneSIG, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='infrastructures')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='infrastructures_sig')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='infrastructures_sig')
    capacite = models.IntegerField(null=True, blank=True)
    population_beneficiaire = models.IntegerField(null=True, blank=True)
    date_mise_en_service = models.DateField(null=True, blank=True)
    cout_realisation = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    photos = models.JSONField(default=list, blank=True)
    proprietes = models.JSONField(default=dict, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='infrastructures_creees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Infrastructure SIG'
        ordering = ['type_infrastructure', 'nom']

    def __str__(self):
        return f"[{self.get_type_infrastructure_display()}] {self.nom}"


class CarteSIG(models.Model):
    """Configuration d'une carte sauvegardée."""
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    couches = models.ManyToManyField(CoucheCartographique, related_name='cartes', blank=True)
    centre_lat = models.DecimalField(max_digits=9, decimal_places=6, default=5.3599)
    centre_lon = models.DecimalField(max_digits=9, decimal_places=6, default=-4.0083)
    zoom_defaut = models.IntegerField(default=7)
    est_publique = models.BooleanField(default=False)
    est_defaut = models.BooleanField(default=False)
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='cartes_sig')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='cartes_sig')
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='cartes_sig_creees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carte SIG'
        ordering = ['-est_defaut', 'nom']

    def __str__(self):
        return f"Carte: {self.nom}"
