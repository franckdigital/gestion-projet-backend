from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M45 : Capitalisation des connaissances ───────────────────────────────────

class FicheCapitalisation(models.Model):
    TYPE_CHOICES = [
        ('bonne_pratique', 'Bonne pratique'),
        ('retour_experience', "Retour d'expérience"),
        ('lecon_apprise', 'Leçon apprise'),
        ('etude_cas', 'Étude de cas'),
        ('innovation', 'Innovation'),
        ('echec_analyse', 'Échec analysé'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'), ('soumise', 'Soumise'),
        ('validee', 'Validée'), ('publiee', 'Publiée'), ('archivee', 'Archivée'),
    ]
    DOMAINE_CHOICES = [
        ('gestion_projet', 'Gestion de projet'),
        ('suivi_evaluation', 'Suivi-évaluation'),
        ('finance', 'Finance / Comptabilité'),
        ('rh', 'Ressources humaines'),
        ('juridique', 'Juridique'),
        ('logistique', 'Logistique'),
        ('communication', 'Communication'),
        ('technique', 'Technique'),
        ('participation', 'Participation communautaire'),
        ('gouvernance', 'Gouvernance'),
        ('autre', 'Autre'),
    ]

    reference = models.CharField(max_length=20, blank=True)
    titre = models.CharField(max_length=300)
    type_fiche = models.CharField(max_length=20, choices=TYPE_CHOICES, default='lecon_apprise')
    domaine = models.CharField(max_length=25, choices=DOMAINE_CHOICES, default='gestion_projet')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')

    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='fiches_capitalisation')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='fiches_capitalisation')

    contexte = models.TextField(blank=True)
    probleme_defi = models.TextField(blank=True)
    solution_approche = models.TextField()
    resultats_obtenus = models.TextField(blank=True)
    lecon_principale = models.TextField()
    recommandation = models.TextField(blank=True)
    conditions_replicabilite = models.TextField(blank=True)
    indicateurs_succes = models.TextField(blank=True)

    tags = models.JSONField(default=list, blank=True)
    mots_cles = models.TextField(blank=True)
    niveau_replicabilite = models.CharField(
        max_length=20,
        choices=[('faible', 'Faible'), ('moyen', 'Moyen'), ('eleve', 'Élevé')],
        default='moyen'
    )
    periode_reference = models.CharField(max_length=100, blank=True)
    zone_geographique = models.CharField(max_length=200, blank=True)
    public_cible = models.TextField(blank=True)

    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                related_name='fiches_capitalisation')
    contributeurs = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                            related_name='fiches_contribuees', blank=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='fiches_validees')
    date_validation = models.DateTimeField(null=True, blank=True)

    fichier_principal = models.FileField(upload_to='capitalisation/fiches/%Y/', null=True, blank=True)
    document_ged = models.ForeignKey('ged.Document', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='fiches_capitalisation')
    genere_par_ia = models.BooleanField(default=False)
    nb_consultations = models.IntegerField(default=0)
    nb_favoris = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fiche de capitalisation'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.reference}] {self.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = FicheCapitalisation.objects.count() + 1
            self.reference = f"CAP-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)


class EntreeBibliotheque(models.Model):
    CATEGORIE_CHOICES = [
        ('guide', 'Guide / Manuel'), ('rapport', 'Rapport'),
        ('etude', 'Étude / Recherche'), ('outil', 'Outil / Template'),
        ('formation', 'Support de formation'),
        ('reference', 'Document de référence'),
        ('article', 'Article / Publication'), ('autre', 'Autre'),
    ]

    titre = models.CharField(max_length=300)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='guide')
    sous_categorie = models.CharField(max_length=100, blank=True)
    domaine = models.CharField(max_length=25, choices=FicheCapitalisation.DOMAINE_CHOICES,
                                default='gestion_projet')
    description = models.TextField(blank=True)
    auteur = models.CharField(max_length=200, blank=True)
    organisation = models.CharField(max_length=200, blank=True)
    annee_publication = models.IntegerField(null=True, blank=True)
    langue = models.CharField(max_length=5, default='fr')
    fichier = models.FileField(upload_to='capitalisation/bibliotheque/%Y/', null=True, blank=True)
    url_externe = models.URLField(blank=True)
    mots_cles = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    est_public = models.BooleanField(default=True)
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='entrees_bibliotheque')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='entrees_bibliotheque')
    nb_telechargements = models.IntegerField(default=0)
    ajoute_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='entrees_ajoutees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrée bibliothèque'
        ordering = ['-created_at']

    def __str__(self):
        return self.titre


class CommentaireFiche(models.Model):
    fiche = models.ForeignKey(FicheCapitalisation, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                related_name='commentaires_capitalisation')
    contenu = models.TextField()
    en_reponse_a = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='reponses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commentaire fiche capitalisation'
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire sur {self.fiche.titre[:60]}"


class CentreConnaissance(models.Model):
    """Centre de connaissances thématique."""
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    domaine = models.CharField(max_length=25, choices=FicheCapitalisation.DOMAINE_CHOICES,
                                default='gestion_projet')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     related_name='centres_connaissance')
    fiches = models.ManyToManyField(FicheCapitalisation, related_name='centres_connaissance', blank=True)
    entrees_bibliotheque = models.ManyToManyField(EntreeBibliotheque,
                                                   related_name='centres_connaissance', blank=True)
    icone = models.CharField(max_length=50, blank=True)
    couleur = models.CharField(max_length=7, default='#7e22ce')
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Centre de connaissances'
        ordering = ['domaine', 'nom']

    def __str__(self):
        return f"[{self.get_domaine_display()}] {self.nom}"
