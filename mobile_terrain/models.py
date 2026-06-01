from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M30 : Session terrain ────────────────────────────────────────────────────

class SessionTerrain(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('synchronisee', 'Synchronisée'),
        ('erreur', 'Erreur de synchronisation'),
    ]

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions_terrain'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sessions_terrain'
    )
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sessions_terrain'
    )
    appareil = models.CharField(max_length=200, blank=True)
    version_app = models.CharField(max_length=20, blank=True)
    mode_hors_ligne = models.BooleanField(default=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')

    latitude_debut = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude_debut = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitude_fin = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude_fin = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    date_synchronisation = models.DateTimeField(null=True, blank=True)
    nb_collectes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Session terrain'
        ordering = ['-date_debut']

    def __str__(self):
        return f"Session {self.agent} — {self.date_debut.date()}"

    def terminer(self, lat=None, lon=None):
        self.statut = 'terminee'
        self.date_fin = timezone.now()
        if lat:
            self.latitude_fin = lat
        if lon:
            self.longitude_fin = lon
        self.save(update_fields=['statut', 'date_fin', 'latitude_fin', 'longitude_fin'])

    def synchroniser(self):
        self.statut = 'synchronisee'
        self.date_synchronisation = timezone.now()
        self.save(update_fields=['statut', 'date_synchronisation'])


class CollecteTerrain(models.Model):
    TYPE_CHOICES = [
        ('formulaire', 'Formulaire'),
        ('photo', 'Photo'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('observation', 'Observation'),
        ('interview', 'Interview'),
        ('mesure', 'Mesure'),
    ]
    STATUT_CHOICES = [
        ('local', 'Stocké localement'),
        ('en_attente_sync', 'En attente de synchronisation'),
        ('synchronise', 'Synchronisé'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    session = models.ForeignKey(SessionTerrain, on_delete=models.CASCADE, related_name='collectes')
    type_collecte = models.CharField(max_length=15, choices=TYPE_CHOICES, default='observation')
    indicateur = models.ForeignKey(
        'suivi_evaluation.Indicateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collectes_terrain'
    )
    formulaire = models.ForeignKey(
        'suivi_evaluation.FormulaireDynamique', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collectes_terrain'
    )
    titre = models.CharField(max_length=200, blank=True)
    donnees = models.JSONField(default=dict, blank=True)
    valeur_numerique = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    notes = models.TextField(blank=True)

    fichier_media = models.FileField(upload_to='terrain/media/%Y/%m/', null=True, blank=True)
    type_mime = models.CharField(max_length=100, blank=True)
    taille_fichier = models.BigIntegerField(default=0)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    precision_gps = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    adresse_geo = models.CharField(max_length=500, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='local')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collectes_terrain_validees'
    )
    date_collecte_locale = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Collecte terrain'
        ordering = ['-date_collecte_locale']

    def __str__(self):
        return f"[{self.get_type_collecte_display()}] {self.session.agent} — {self.date_collecte_locale.date()}"


class PointageTerrain(models.Model):
    TYPE_CHOICES = [
        ('presence', 'Présence'),
        ('mission', 'Mission'),
        ('visite', 'Visite terrain'),
        ('controle', 'Contrôle'),
        ('audit', 'Audit'),
    ]

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pointages_terrain'
    )
    type_pointage = models.CharField(max_length=15, choices=TYPE_CHOICES, default='presence')
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pointages'
    )
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pointages'
    )
    date_heure = models.DateTimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    precision_gps = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    adresse_geo = models.CharField(max_length=500, blank=True)
    photo_preuve = models.ImageField(upload_to='terrain/pointages/%Y/%m/', null=True, blank=True)
    notes = models.TextField(blank=True)
    valide = models.BooleanField(default=False)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pointages_valides'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pointage terrain'
        ordering = ['-date_heure']

    def __str__(self):
        return f"[{self.get_type_pointage_display()}] {self.agent} — {self.date_heure.date()}"


class SynchronisationMobile(models.Model):
    STATUT_CHOICES = [
        ('succes', 'Succès'),
        ('partiel', 'Partiel'),
        ('echec', 'Échec'),
    ]

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='synchronisations'
    )
    date_synchro = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='succes')
    nb_elements_envoyes = models.IntegerField(default=0)
    nb_elements_recus = models.IntegerField(default=0)
    nb_erreurs = models.IntegerField(default=0)
    duree_secondes = models.IntegerField(default=0)
    version_app = models.CharField(max_length=20, blank=True)
    details = models.JSONField(default=dict, blank=True)
    message_erreur = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Synchronisation mobile'
        ordering = ['-date_synchro']

    def __str__(self):
        return f"Sync {self.agent} — {self.date_synchro.date()} — {self.get_statut_display()}"


class QRCodeScan(models.Model):
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qr_scans'
    )
    contenu_qr = models.TextField()
    type_objet = models.CharField(max_length=50, blank=True)
    objet_id = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    date_scan = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Scan QR Code'
        ordering = ['-date_scan']

    def __str__(self):
        return f"QR {self.agent} — {self.date_scan.date()}"
