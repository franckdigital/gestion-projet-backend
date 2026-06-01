from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


# ─── M17 : Indicateurs ───────────────────────────────────────────────────────

class Indicateur(models.Model):
    TYPE_CHOICES = [
        ('activite', "Indicateur d'activité"),
        ('resultat', 'Indicateur de résultat'),
        ('effet', "Indicateur d'effet"),
        ('impact', "Indicateur d'impact"),
        ('financier', 'Indicateur financier'),
        ('processus', 'Indicateur de processus'),
        ('intrant', "Indicateur d'intrant"),
    ]
    FREQUENCE_CHOICES = [
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'),
        ('annuelle', 'Annuelle'),
        ('ponctuelle', 'Ponctuelle'),
    ]
    STATUT_CHOICES = [
        ('non_demarre', 'Non démarré'),
        ('en_cours', 'En cours'),
        ('atteint', 'Atteint'),
        ('partiellement_atteint', 'Partiellement atteint'),
        ('non_atteint', 'Non atteint'),
    ]
    UNITE_CHOICES = [
        ('nombre', 'Nombre'),
        ('pourcentage', 'Pourcentage (%)'),
        ('montant', 'Montant (FCFA)'),
        ('taux', 'Taux'),
        ('score', 'Score'),
        ('indice', 'Indice'),
        ('autre', 'Autre'),
    ]
    MODE_CALCUL_CHOICES = [
        ('manuel', 'Saisie manuelle'),
        ('automatique', 'Calcul automatique'),
        ('formule', 'Formule personnalisée'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='indicateurs', null=True, blank=True,
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='indicateurs', null=True, blank=True,
    )
    niveau_resultat = models.ForeignKey(
        'NiveauResultat', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='indicateurs',
    )
    code = models.CharField(max_length=30)
    intitule = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_indicateur = models.CharField(max_length=15, choices=TYPE_CHOICES, default='resultat')
    unite_mesure = models.CharField(max_length=50, choices=UNITE_CHOICES, default='nombre')
    unite_personnalisee = models.CharField(max_length=50, blank=True)

    valeur_baseline = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    date_baseline = models.DateField(null=True, blank=True)
    valeur_cible_globale = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    valeur_realisee = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    frequence_collecte = models.CharField(max_length=15, choices=FREQUENCE_CHOICES, default='trimestrielle')
    mode_calcul = models.CharField(max_length=15, choices=MODE_CALCUL_CHOICES, default='manuel')
    formule = models.TextField(blank=True, help_text="Ex: (realise / prevu) * 100")

    source_verification = models.CharField(max_length=300, blank=True)
    methode_collecte = models.TextField(blank=True)
    responsable_collecte = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='indicateurs_collecte',
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='indicateurs_responsable',
    )
    hypotheses = models.TextField(blank=True)
    risques = models.TextField(blank=True)

    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='non_demarre')
    actif = models.BooleanField(default=True)
    est_disaggregue = models.BooleanField(default=False)
    dimensions_disaggregation = models.JSONField(default=list, blank=True,
        help_text="Ex: ['sexe', 'age', 'region']")

    ordre = models.IntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='indicateurs_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Indicateur'
        ordering = ['ordre', 'code']

    def __str__(self):
        return f"[{self.code}] {self.intitule}"

    @property
    def taux_realisation(self):
        if not self.valeur_cible_globale or not self.valeur_realisee:
            return 0
        return round((float(self.valeur_realisee) / float(self.valeur_cible_globale)) * 100, 2)

    @property
    def derniere_collecte(self):
        return self.collectes.filter(statut='valide').order_by('-date_collecte').first()

    def calculer_statut(self):
        taux = self.taux_realisation
        if taux == 0:
            return 'non_demarre'
        elif taux >= 100:
            return 'atteint'
        elif taux >= 80:
            return 'partiellement_atteint'
        else:
            return 'non_atteint'


class ValeurCiblePeriode(models.Model):
    indicateur = models.ForeignKey(Indicateur, on_delete=models.CASCADE, related_name='cibles_periodes')
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)])
    valeur_cible = models.DecimalField(max_digits=15, decimal_places=4)
    valeur_realisee = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Cible par période'
        unique_together = ['indicateur', 'annee', 'trimestre']
        ordering = ['annee', 'trimestre']

    def __str__(self):
        q = f"T{self.trimestre}" if self.trimestre else ""
        return f"{self.indicateur.code} — {self.annee}{q}"

    @property
    def taux_realisation(self):
        if not self.valeur_cible or not self.valeur_realisee:
            return None
        return round((float(self.valeur_realisee) / float(self.valeur_cible)) * 100, 2)


class CollecteIndicateur(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    indicateur = models.ForeignKey(Indicateur, on_delete=models.CASCADE, related_name='collectes')
    periode = models.ForeignKey(
        ValeurCiblePeriode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collectes',
    )
    date_collecte = models.DateField()
    valeur_reelle = models.DecimalField(max_digits=15, decimal_places=4)
    valeur_disaggregee = models.JSONField(default=dict, blank=True,
        help_text="Ex: {'hommes': 30, 'femmes': 20}")
    collecteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='collectes_effectuees',
    )
    commentaire = models.TextField(blank=True)
    source_donnee = models.CharField(max_length=200, blank=True)
    fichier_justificatif = models.FileField(upload_to='collectes/%Y/%m/', null=True, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collectes_validees',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Collecte indicateur'
        ordering = ['-date_collecte']

    def __str__(self):
        return f"{self.indicateur.code} — {self.date_collecte} : {self.valeur_reelle}"

    def valider(self, user):
        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])
        self.indicateur.valeur_realisee = self.valeur_reelle
        self.indicateur.statut = self.indicateur.calculer_statut()
        self.indicateur.save(update_fields=['valeur_realisee', 'statut'])

    def rejeter(self, user, motif=''):
        self.statut = 'rejete'
        self.valide_par = user
        self.motif_rejet = motif
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'motif_rejet', 'date_validation'])


class AlerteIndicateur(models.Model):
    TYPE_CHOICES = [
        ('cible_non_atteinte', 'Cible non atteinte'),
        ('donnees_manquantes', 'Données manquantes'),
        ('indicateur_critique', 'Indicateur critique'),
        ('retard_collecte', 'Retard de collecte'),
    ]
    NIVEAU_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critique', 'Critique'),
    ]

    indicateur = models.ForeignKey(Indicateur, on_delete=models.CASCADE, related_name='alertes')
    type_alerte = models.CharField(max_length=25, choices=TYPE_CHOICES)
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, default='warning')
    message = models.TextField()
    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alertes_indicateurs',
    )
    lue = models.BooleanField(default=False)
    date_alerte = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Alerte indicateur'
        ordering = ['-date_alerte']


# ─── M18 : Collecte de données ───────────────────────────────────────────────

class FormulaireDynamique(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publie', 'Publié'),
        ('ferme', 'Fermé'),
        ('archive', 'Archivé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='formulaires_se',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='formulaires_se',
    )
    indicateur = models.ForeignKey(
        Indicateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='formulaires',
    )
    code = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    date_ouverture = models.DateField(null=True, blank=True)
    date_fermeture = models.DateField(null=True, blank=True)
    allow_offline = models.BooleanField(default=True)
    require_gps = models.BooleanField(default=False)
    require_photo = models.BooleanField(default=False)
    require_signature = models.BooleanField(default=False)
    max_soumissions = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='formulaires_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Formulaire dynamique'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.code}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.code:
            count = FormulaireDynamique.objects.count() + 1
            self.code = f"FORM-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class ChampFormulaire(models.Model):
    TYPE_CHOICES = [
        ('texte', 'Texte court'),
        ('texte_long', 'Texte long'),
        ('nombre', 'Nombre'),
        ('decimal', 'Nombre décimal'),
        ('date', 'Date'),
        ('heure', 'Heure'),
        ('datetime', 'Date et heure'),
        ('choix_unique', 'Choix unique'),
        ('choix_multiple', 'Choix multiple'),
        ('echelle_likert', 'Échelle Likert'),
        ('oui_non', 'Oui / Non'),
        ('gps', 'GPS (géolocalisation)'),
        ('photo', 'Photo'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('fichier', 'Fichier'),
        ('signature', 'Signature'),
        ('qr_code', 'QR Code'),
        ('calcul', 'Champ calculé'),
        ('section', 'En-tête de section'),
    ]

    formulaire = models.ForeignKey(FormulaireDynamique, on_delete=models.CASCADE, related_name='champs')
    type_champ = models.CharField(max_length=20, choices=TYPE_CHOICES)
    libelle = models.CharField(max_length=300)
    description = models.CharField(max_length=500, blank=True)
    obligatoire = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    options = models.JSONField(default=list, blank=True,
        help_text="Pour QCM: ['Option A', 'Option B'] / Pour Likert: {'min': 1, 'max': 5}")
    formule_calcul = models.CharField(max_length=500, blank=True)
    condition_affichage = models.JSONField(default=dict, blank=True,
        help_text="Ex: {'champ_id': 5, 'valeur': 'Oui'}")
    valeur_defaut = models.CharField(max_length=200, blank=True)
    validation_min = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    validation_max = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    indicateur_lie = models.ForeignKey(
        Indicateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='champs_formulaire',
    )

    class Meta:
        verbose_name = 'Champ formulaire'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.formulaire.titre} — {self.libelle}"


class SoumissionFormulaire(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    formulaire = models.ForeignKey(FormulaireDynamique, on_delete=models.CASCADE, related_name='soumissions')
    soumetteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='soumissions_formulaires',
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='soumis')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='soumissions_validees',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    precision_gps = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    appareil = models.CharField(max_length=200, blank=True)
    soumis_hors_ligne = models.BooleanField(default=False)
    date_soumission_locale = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Soumission formulaire'
        ordering = ['-created_at']

    def valider(self, user):
        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])

    def rejeter(self, user, motif=''):
        self.statut = 'rejete'
        self.valide_par = user
        self.motif_rejet = motif
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'motif_rejet', 'date_validation'])


class ReponseChamp(models.Model):
    soumission = models.ForeignKey(SoumissionFormulaire, on_delete=models.CASCADE, related_name='reponses')
    champ = models.ForeignKey(ChampFormulaire, on_delete=models.CASCADE, related_name='reponses')
    valeur_texte = models.TextField(blank=True)
    valeur_nombre = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    valeur_date = models.DateField(null=True, blank=True)
    valeur_json = models.JSONField(default=None, null=True, blank=True)
    fichier = models.FileField(upload_to='reponses_formulaires/%Y/%m/', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'Réponse champ'
        unique_together = ['soumission', 'champ']

    def __str__(self):
        return f"Soumission {self.soumission_id} — {self.champ.libelle}"


# ─── M19 : Enquêtes ───────────────────────────────────────────────────────────

class Enquete(models.Model):
    TYPE_CHOICES = [
        ('baseline', 'Baseline (situation de référence)'),
        ('midline', 'Midline (mi-parcours)'),
        ('endline', 'Endline (évaluation finale)'),
        ('satisfaction', 'Enquête de satisfaction'),
        ('impact', "Enquête d'impact"),
        ('besoins', 'Analyse des besoins'),
        ('evaluation', 'Évaluation'),
        ('connaissance', 'Connaissance, Attitudes, Pratiques (CAP)'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('test', 'En test'),
        ('active', 'Active'),
        ('fermee', 'Fermée'),
        ('analysee', 'Analysée'),
        ('archivee', 'Archivée'),
    ]
    CANAL_CHOICES = [
        ('mobile', 'Application mobile'),
        ('web', 'Web'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('papier', 'Papier'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='enquetes',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='enquetes',
    )
    code = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_enquete = models.CharField(max_length=20, choices=TYPE_CHOICES, default='satisfaction')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    canaux = models.JSONField(default=list, blank=True, help_text="Ex: ['mobile', 'web']")

    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    population_cible = models.CharField(max_length=300, blank=True)
    taille_echantillon = models.IntegerField(null=True, blank=True)
    objectifs = models.TextField(blank=True)
    methodologie = models.TextField(blank=True)

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='enquetes_responsable',
    )
    enqueteurs = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='enquetes_assignees', blank=True
    )
    allow_anonymous = models.BooleanField(default=False)
    nb_reponses_attendues = models.IntegerField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='enquetes_creees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Enquête'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.code}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.code:
            count = Enquete.objects.count() + 1
            self.code = f"ENQ-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def nb_reponses(self):
        return self.reponses.filter(statut__in=['soumis', 'complete']).count()

    @property
    def taux_completion(self):
        if not self.nb_reponses_attendues:
            return None
        return round((self.nb_reponses / self.nb_reponses_attendues) * 100, 1)


class SectionEnquete(models.Model):
    enquete = models.ForeignKey(Enquete, on_delete=models.CASCADE, related_name='sections')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    condition_affichage = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Section enquête'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.enquete.titre} — {self.titre}"


class QuestionEnquete(models.Model):
    TYPE_CHOICES = [
        ('texte', 'Texte court'),
        ('texte_long', 'Texte long'),
        ('nombre', 'Nombre'),
        ('choix_unique', 'Choix unique'),
        ('choix_multiple', 'Choix multiple'),
        ('likert', 'Échelle Likert'),
        ('date', 'Date'),
        ('image', 'Image'),
        ('gps', 'Géolocalisation GPS'),
        ('note', 'Note / Évaluation'),
        ('classification', 'Classement'),
        ('matrice', 'Matrice'),
    ]

    section = models.ForeignKey(
        SectionEnquete, on_delete=models.CASCADE, related_name='questions',
        null=True, blank=True
    )
    enquete = models.ForeignKey(Enquete, on_delete=models.CASCADE, related_name='questions')
    type_question = models.CharField(max_length=20, choices=TYPE_CHOICES)
    libelle = models.CharField(max_length=500)
    description = models.CharField(max_length=500, blank=True)
    obligatoire = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)
    options = models.JSONField(default=list, blank=True)
    config_likert = models.JSONField(default=dict, blank=True,
        help_text="Ex: {'min': 1, 'max': 5, 'labels': {'1': 'Très insatisfait', '5': 'Très satisfait'}}")
    indicateur_lie = models.ForeignKey(
        Indicateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='questions_enquete',
    )
    condition_affichage = models.JSONField(default=dict, blank=True)
    allow_other = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Question enquête'
        ordering = ['ordre']

    def __str__(self):
        return f"{self.enquete.titre} Q{self.ordre}: {self.libelle[:60]}"


class ReponseEnquete(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('soumis', 'Soumis'),
        ('complete', 'Complété'),
        ('invalide', 'Invalide'),
    ]

    enquete = models.ForeignKey(Enquete, on_delete=models.CASCADE, related_name='reponses')
    repondant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reponses_enquetes',
    )
    identifiant_anonyme = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='en_cours')
    langue = models.CharField(max_length=10, default='fr')
    duree_completion = models.IntegerField(null=True, blank=True, help_text="En secondes")

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    canal = models.CharField(max_length=10, choices=Enquete.CANAL_CHOICES, default='web')
    appareil = models.CharField(max_length=200, blank=True)
    soumis_hors_ligne = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    soumis_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Réponse enquête'
        ordering = ['-created_at']


class ReponseQuestion(models.Model):
    reponse_enquete = models.ForeignKey(ReponseEnquete, on_delete=models.CASCADE, related_name='reponses_questions')
    question = models.ForeignKey(QuestionEnquete, on_delete=models.CASCADE, related_name='reponses')
    valeur_texte = models.TextField(blank=True)
    valeur_nombre = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    valeur_choix = models.JSONField(default=list, blank=True)
    valeur_date = models.DateField(null=True, blank=True)
    valeur_fichier = models.FileField(upload_to='reponses_enquetes/%Y/%m/', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'Réponse question'
        unique_together = ['reponse_enquete', 'question']


# ─── M20 : Cadre de résultats ─────────────────────────────────────────────────

class CadreResultats(models.Model):
    projet = models.OneToOneField(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='cadre_resultats', null=True, blank=True,
    )
    programme = models.OneToOneField(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='cadre_resultats', null=True, blank=True,
    )
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=10, default='1.0')
    date_validation = models.DateField(null=True, blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadres_resultats_valides',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='cadres_resultats_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cadre de résultats'

    def __str__(self):
        ref = self.projet or self.programme
        return f"Cadre résultats — {ref}"


class NiveauResultat(models.Model):
    NIVEAU_CHOICES = [
        ('impact', 'Impact'),
        ('effet', 'Effet'),
        ('resultat', 'Résultat'),
        ('produit', 'Produit/Extrant'),
        ('activite', 'Activité'),
        ('intrant', 'Intrant'),
    ]

    cadre = models.ForeignKey(CadreResultats, on_delete=models.CASCADE, related_name='niveaux')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='enfants'
    )
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES)
    code = models.CharField(max_length=20, blank=True)
    intitule = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Niveau de résultat'
        ordering = ['niveau', 'ordre']

    def __str__(self):
        return f"[{self.get_niveau_display()}] {self.intitule[:80]}"


class TheorieChangement(models.Model):
    projet = models.OneToOneField(
        'programmes_projets.Projet', on_delete=models.CASCADE,
        related_name='theorie_changement', null=True, blank=True,
    )
    programme = models.OneToOneField(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='theorie_changement', null=True, blank=True,
    )
    titre = models.CharField(max_length=300)
    contexte = models.TextField(blank=True)
    probleme_central = models.TextField(blank=True)
    vision_changement = models.TextField(blank=True)
    hypotheses_changement = models.TextField(blank=True)
    facteurs_risque = models.TextField(blank=True)
    diagramme_json = models.JSONField(default=dict, blank=True,
        help_text="Structure JSON du diagramme de théorie du changement")
    version = models.CharField(max_length=10, default='1.0')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='theories_creees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Théorie du changement'

    def __str__(self):
        ref = self.projet or self.programme
        return f"Théorie du changement — {ref}"


class Evaluation(models.Model):
    TYPE_CHOICES = [
        ('initiale', 'Évaluation initiale'),
        ('intermediaire', 'Évaluation intermédiaire'),
        ('finale', 'Évaluation finale'),
        ('ex_post', 'Évaluation ex-post'),
        ('thematique', 'Évaluation thématique'),
        ('impact', "Évaluation d'impact"),
    ]
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('rapport_provisoire', 'Rapport provisoire'),
        ('rapport_final', 'Rapport final'),
        ('validee', 'Validée'),
        ('publiee', 'Publiée'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evaluations',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evaluations',
    )
    reference = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    type_evaluation = models.CharField(max_length=20, choices=TYPE_CHOICES, default='intermediaire')
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='planifiee')
    description = models.TextField(blank=True)

    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    date_rapport = models.DateField(null=True, blank=True)

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='evaluations_responsable',
    )
    evaluateurs_externes = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    note_globale = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    conclusions = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    rapport_final = models.FileField(upload_to='evaluations/%Y/', null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='evaluations_creees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Évaluation'
        ordering = ['-date_debut']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Evaluation.objects.count() + 1
            self.reference = f"EVAL-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class CritereEvaluation(models.Model):
    CRITERE_CHOICES = [
        ('pertinence', 'Pertinence'),
        ('efficacite', 'Efficacité'),
        ('efficience', 'Efficience'),
        ('impact', 'Impact'),
        ('durabilite', 'Durabilité / Viabilité'),
        ('coherence', 'Cohérence'),
    ]

    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='criteres')
    critere = models.CharField(max_length=15, choices=CRITERE_CHOICES)
    note = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    observation = models.TextField(blank=True)
    points_forts = models.TextField(blank=True)
    points_faibles = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Critère évaluation'
        unique_together = ['evaluation', 'critere']

    def __str__(self):
        return f"{self.evaluation.titre} — {self.get_critere_display()} : {self.note}/5"


class LeconApprise(models.Model):
    TYPE_CHOICES = [
        ('bonne_pratique', 'Bonne pratique'),
        ('difficulte', 'Difficulté rencontrée'),
        ('recommandation', 'Recommandation'),
        ('innovation', 'Innovation'),
        ('lecon', 'Leçon apprise'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lecons_apprises',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lecons_apprises',
    )
    evaluation = models.ForeignKey(
        Evaluation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lecons',
    )
    type_lecon = models.CharField(max_length=20, choices=TYPE_CHOICES, default='lecon')
    titre = models.CharField(max_length=300)
    contexte = models.TextField(blank=True)
    description = models.TextField()
    recommandation = models.TextField(blank=True)
    domaine = models.CharField(max_length=200, blank=True)
    tags = models.JSONField(default=list, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='lecons_creees',
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lecons_validees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leçon apprise'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_lecon_display()}] {self.titre}"


# ─── Rapports S&E ─────────────────────────────────────────────────────────────

class RapportSE(models.Model):
    TYPE_CHOICES = [
        ('activites', "Rapport d'activités"),
        ('resultats', 'Rapport de résultats'),
        ('effets', "Rapport d'effets"),
        ('impact', "Rapport d'impact"),
        ('performance', 'Rapport de performance'),
        ('suivi_evaluation', 'Rapport suivi-évaluation'),
        ('bailleur', 'Rapport bailleur'),
        ('cadre_logique', 'Rapport cadre logique'),
        ('theorie_changement', 'Rapport théorie du changement'),
        ('indicateurs', 'Rapport indicateurs'),
        ('geographique', 'Rapport géographique'),
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

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_se',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_se',
    )
    reference = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    type_rapport = models.CharField(max_length=25, choices=TYPE_CHOICES, default='suivi_evaluation')
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='trimestriel')
    date_debut_periode = models.DateField(null=True, blank=True)
    date_fin_periode = models.DateField(null=True, blank=True)
    date_rapport = models.DateField(default=timezone.now)

    contenu = models.TextField(blank=True)
    synthese = models.TextField(blank=True)
    principales_realisations = models.TextField(blank=True)
    defis = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    perspectives = models.TextField(blank=True)

    indicateurs_inclus = models.ManyToManyField(Indicateur, blank=True, related_name='rapports_se')
    donnees_json = models.JSONField(default=dict, blank=True)

    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='rapports_se_rediges',
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_se_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    fichier = models.FileField(upload_to='rapports_se/%Y/%m/', null=True, blank=True)
    genere_par_ia = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapport S&E'
        ordering = ['-date_rapport']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = RapportSE.objects.count() + 1
            self.reference = f"RSE-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


# ─── Analyse prédictive IA ────────────────────────────────────────────────────

class AnalysePredictive(models.Model):
    TYPE_CHOICES = [
        ('tendance', 'Analyse des tendances'),
        ('prevision', "Prévision d'indicateurs"),
        ('risque', 'Détection des risques'),
        ('retard', 'Détection des retards'),
        ('correction', 'Suggestion corrective'),
        ('rapport_auto', 'Génération automatique rapport'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('complete', 'Complète'),
        ('erreur', 'Erreur'),
    ]

    indicateur = models.ForeignKey(
        Indicateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses_predictives',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses_predictives',
    )
    type_analyse = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='en_attente')
    parametres = models.JSONField(default=dict, blank=True)
    resultats = models.JSONField(default=dict, blank=True)
    previsions = models.JSONField(default=list, blank=True,
        help_text="Liste de {date, valeur_prevue, intervalle_confiance}")
    risques_detectes = models.JSONField(default=list, blank=True)
    suggestions = models.TextField(blank=True)
    confiance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)])
    demande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='analyses_demandees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Analyse prédictive'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_analyse_display()} — {self.created_at.date()}"


# ─── Points SIG ───────────────────────────────────────────────────────────────

class PointSIG(models.Model):
    TYPE_CHOICES = [
        ('projet', 'Projet'),
        ('activite', 'Activité'),
        ('beneficiaire', 'Bénéficiaire'),
        ('indicateur', 'Indicateur'),
        ('collecte', 'Point de collecte'),
    ]

    type_point = models.CharField(max_length=15, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rayon = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="En mètres, pour les zones")

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='points_sig',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='points_sig',
    )
    indicateur = models.ForeignKey(
        Indicateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='points_sig',
    )
    valeur = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    couleur = models.CharField(max_length=7, default='#3388ff')
    icone = models.CharField(max_length=50, blank=True)
    donnees_extra = models.JSONField(default=dict, blank=True)
    actif = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='points_sig_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Point SIG'
        ordering = ['type_point', 'titre']

    def __str__(self):
        return f"[{self.get_type_point_display()}] {self.titre} ({self.latitude}, {self.longitude})"


# ─── M29 : Gestion des Risques ───────────────────────────────────────────────

class RegistreRisque(models.Model):
    CATEGORIE_CHOICES = [
        ('strategique', 'Stratégique'),
        ('financier', 'Financier'),
        ('operationnel', 'Opérationnel'),
        ('technique', 'Technique'),
        ('securitaire', 'Sécuritaire'),
        ('environnemental', 'Environnemental'),
        ('social', 'Social'),
        ('reglementaire', 'Réglementaire'),
    ]
    PROBABILITE_CHOICES = [
        (1, 'Très faible'),
        (2, 'Faible'),
        (3, 'Moyenne'),
        (4, 'Élevée'),
        (5, 'Très élevée'),
    ]
    IMPACT_CHOICES = [
        (1, 'Très faible'),
        (2, 'Faible'),
        (3, 'Moyen'),
        (4, 'Élevé'),
        (5, 'Critique'),
    ]
    STATUT_CHOICES = [
        ('identifie', 'Identifié'),
        ('en_cours_traitement', 'En cours de traitement'),
        ('mitige', 'Mitigé'),
        ('surveille', 'Surveillé'),
        ('resolu', 'Résolu'),
        ('accepte', 'Accepté'),
        ('transfere', 'Transféré'),
    ]
    TENDANCE_CHOICES = [
        ('croissant', 'Croissant'),
        ('stable', 'Stable'),
        ('decroissant', 'Décroissant'),
    ]

    reference = models.CharField(max_length=20, blank=True)
    intitule = models.CharField(max_length=300)
    description = models.TextField()
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='operationnel')

    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='risques_registre'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='risques_registre'
    )
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='risques_registre'
    )

    probabilite = models.IntegerField(choices=PROBABILITE_CHOICES, default=3)
    impact = models.IntegerField(choices=IMPACT_CHOICES, default=3)
    score_risque = models.IntegerField(default=9)
    niveau_risque = models.CharField(max_length=15, blank=True)
    tendance = models.CharField(max_length=15, choices=TENDANCE_CHOICES, default='stable')

    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='identifie')
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='risques_responsable'
    )
    date_identification = models.DateField(auto_now_add=True)
    date_revue = models.DateField(null=True, blank=True)
    date_resolution = models.DateField(null=True, blank=True)

    causes = models.TextField(blank=True)
    consequences = models.TextField(blank=True)
    indicateurs_declenchement = models.TextField(blank=True)
    hypotheses = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='risques_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Risque'
        ordering = ['-score_risque', '-date_identification']

    def __str__(self):
        return f"[{self.reference}] {self.intitule} — {self.niveau_risque}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = RegistreRisque.objects.count() + 1
            self.reference = f"RSK-{timezone.now().year}-{count:04d}"
        self.score_risque = self.probabilite * self.impact
        if self.score_risque <= 4:
            self.niveau_risque = 'faible'
        elif self.score_risque <= 9:
            self.niveau_risque = 'modere'
        elif self.score_risque <= 16:
            self.niveau_risque = 'important'
        else:
            self.niveau_risque = 'critique'
        super().save(*args, **kwargs)

    @property
    def est_critique(self):
        return self.niveau_risque == 'critique'


class PlanMitigation(models.Model):
    TYPE_CHOICES = [
        ('prevention', 'Prévention (réduire probabilité)'),
        ('reduction', 'Réduction (réduire impact)'),
        ('transfert', 'Transfert (assurance, sous-traitance)'),
        ('acceptation', 'Acceptation'),
        ('contingence', 'Plan de contingence'),
    ]
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('realise', 'Réalisé'),
        ('inefficace', 'Inefficace'),
    ]

    risque = models.ForeignKey(RegistreRisque, on_delete=models.CASCADE, related_name='plans_mitigation')
    type_mitigation = models.CharField(max_length=15, choices=TYPE_CHOICES, default='prevention')
    description = models.TextField()
    objectif = models.TextField(blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifie')
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='plans_mitigation_responsable'
    )
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    cout_estime = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    probabilite_residuelle = models.IntegerField(null=True, blank=True)
    impact_residuel = models.IntegerField(null=True, blank=True)
    resultat = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan de mitigation'
        ordering = ['risque', 'date_debut']

    def __str__(self):
        return f"{self.risque.reference} — {self.get_type_mitigation_display()}"

    @property
    def score_residuel(self):
        if self.probabilite_residuelle and self.impact_residuel:
            return self.probabilite_residuelle * self.impact_residuel
        return None


class SuiviRisque(models.Model):
    risque = models.ForeignKey(RegistreRisque, on_delete=models.CASCADE, related_name='suivis')
    date_suivi = models.DateField()
    probabilite = models.IntegerField(choices=RegistreRisque.PROBABILITE_CHOICES)
    impact = models.IntegerField(choices=RegistreRisque.IMPACT_CHOICES)
    statut = models.CharField(max_length=25, choices=RegistreRisque.STATUT_CHOICES)
    tendance = models.CharField(max_length=15, choices=RegistreRisque.TENDANCE_CHOICES)
    observations = models.TextField(blank=True)
    actions_prises = models.TextField(blank=True)
    suivi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='suivis_risque'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suivi risque'
        ordering = ['-date_suivi']

    def __str__(self):
        return f"{self.risque.reference} — {self.date_suivi}"


class AlerteRisque(models.Model):
    NIVEAU_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critique', 'Critique'),
    ]

    risque = models.ForeignKey(RegistreRisque, on_delete=models.CASCADE, related_name='alertes_risque')
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, default='warning')
    message = models.TextField()
    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alertes_risques'
    )
    lue = models.BooleanField(default=False)
    date_alerte = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Alerte risque'
        ordering = ['-date_alerte']

    def __str__(self):
        return f"[{self.niveau}] {self.risque.reference} — {self.message[:60]}"
