from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M13 : Activités d'exécution ─────────────────────────────────────────────

class ActiviteExecution(models.Model):
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('suspendue', 'Suspendue'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('archivee', 'Archivée'),
    ]
    PRIORITE_CHOICES = [
        ('critique', 'Critique'),
        ('haute', 'Haute'),
        ('normale', 'Normale'),
        ('faible', 'Faible'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE, related_name='activites_execution'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activites_execution',
    )
    activite_pa = models.ForeignKey(
        'planification.ActivitePA', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='executions',
    )
    plan_travail_activite = models.ForeignKey(
        'planification.Activite', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='executions',
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_activites'
    )

    code = models.CharField(max_length=30)
    intitule = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='activites_execution_responsable',
    )
    co_responsables = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='activites_execution_co', blank=True
    )

    date_debut_prevue = models.DateField()
    date_fin_prevue = models.DateField()
    date_debut_reelle = models.DateField(null=True, blank=True)
    date_fin_reelle = models.DateField(null=True, blank=True)

    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ordre = models.IntegerField(default=0)

    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activites_execution_validees',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_suspension = models.TextField(blank=True)

    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='activites_execution_creees',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Activité d'exécution"
        ordering = ['ordre', 'date_debut_prevue']

    def __str__(self):
        return f"[{self.code}] {self.intitule}"

    @property
    def est_en_retard(self):
        return (
            self.date_fin_prevue < timezone.now().date()
            and self.statut not in ('terminee', 'annulee', 'archivee')
        )

    def demarrer(self, user=None):
        self.statut = 'en_cours'
        self.date_debut_reelle = self.date_debut_reelle or timezone.now().date()
        self.save(update_fields=['statut', 'date_debut_reelle'])

    def terminer(self, user=None):
        self.statut = 'terminee'
        self.date_fin_reelle = timezone.now().date()
        self.taux_avancement = 100
        self.save(update_fields=['statut', 'date_fin_reelle', 'taux_avancement'])

    def suspendre(self, motif=''):
        self.statut = 'suspendue'
        self.motif_suspension = motif
        self.save(update_fields=['statut', 'motif_suspension'])


class AffectationRessource(models.Model):
    TYPE_CHOICES = [
        ('utilisateur', 'Utilisateur'),
        ('consultant', 'Consultant'),
        ('partenaire', 'Partenaire'),
        ('equipement', 'Équipement'),
        ('vehicule', 'Véhicule'),
    ]

    activite = models.ForeignKey(ActiviteExecution, on_delete=models.CASCADE, related_name='affectations')
    type_ressource = models.CharField(max_length=15, choices=TYPE_CHOICES)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='affectations_activites',
    )
    nom_ressource = models.CharField(max_length=200, blank=True)
    taux_affectation = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Affectation ressource'

    def __str__(self):
        return f"{self.get_type_ressource_display()} — {self.activite.code}"


class DependanceActivite(models.Model):
    TYPE_CHOICES = [
        ('FD', 'Fin → Début'),
        ('DD', 'Début → Début'),
        ('FF', 'Fin → Fin'),
        ('DF', 'Début → Fin'),
    ]

    activite_source = models.ForeignKey(
        ActiviteExecution, on_delete=models.CASCADE, related_name='dependances_sortantes'
    )
    activite_cible = models.ForeignKey(
        ActiviteExecution, on_delete=models.CASCADE, related_name='dependances_entrantes'
    )
    type_dependance = models.CharField(max_length=5, choices=TYPE_CHOICES, default='FD')
    decalage_jours = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Dépendance activité'
        unique_together = ['activite_source', 'activite_cible']


class RapportActivite(models.Model):
    PERIODE_CHOICES = [
        ('journalier', 'Journalier'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
    ]

    activite = models.ForeignKey(
        ActiviteExecution, on_delete=models.CASCADE, related_name='rapports'
    )
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES)
    date_rapport = models.DateField()
    taux_realisation = models.DecimalField(max_digits=5, decimal_places=2)
    observations = models.TextField(blank=True)
    problemes = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    prochaines_etapes = models.TextField(blank=True)
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rapports_activites'
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    fichier = models.FileField(upload_to='rapports_activites/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rapport d'activité"
        ordering = ['-date_rapport']


# ─── M14 : Tâches ────────────────────────────────────────────────────────────

class Tache(models.Model):
    PRIORITE_CHOICES = [
        ('critique', 'Critique'),
        ('haute', 'Haute'),
        ('normale', 'Normale'),
        ('faible', 'Faible'),
    ]
    STATUT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('en_attente', 'En attente'),
        ('a_valider', 'À valider'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('bloquee', 'Bloquée'),
    ]

    activite = models.ForeignKey(
        ActiviteExecution, on_delete=models.CASCADE, related_name='taches', null=True, blank=True
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_taches'
    )
    code = models.CharField(max_length=20, blank=True)
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='a_faire')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='taches_assignees',
    )
    co_assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='taches_co_assignees', blank=True
    )
    date_debut = models.DateField(null=True, blank=True)
    date_echeance = models.DateField(null=True, blank=True)
    date_completion = models.DateField(null=True, blank=True)
    estimation_heures = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    heures_realisees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    taux_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='taches_creees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tâche'
        ordering = ['ordre', 'date_echeance']

    def __str__(self):
        return self.titre

    @property
    def est_en_retard(self):
        return (
            self.date_echeance
            and self.date_echeance < timezone.now().date()
            and self.statut not in ('terminee', 'annulee')
        )

    @property
    def progression_checklist(self):
        items = self.checklist.all()
        if not items.exists():
            return None
        done = items.filter(complete=True).count()
        total = items.count()
        return {'done': done, 'total': total, 'percent': round(done / total * 100)}


class ChecklistItem(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='checklist')
    libelle = models.CharField(max_length=300)
    complete = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    complete_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='checklist_completes',
    )
    date_completion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Item checklist'
        ordering = ['ordre']

    def complete_item(self, user):
        self.complete = True
        self.complete_par = user
        self.date_completion = timezone.now()
        self.save()

    def uncomplete_item(self):
        self.complete = False
        self.complete_par = None
        self.date_completion = None
        self.save()


class DependanceTache(models.Model):
    TYPE_CHOICES = [
        ('FD', 'Fin → Début'),
        ('DD', 'Début → Début'),
        ('FF', 'Fin → Fin'),
        ('DF', 'Début → Fin'),
    ]

    tache_source = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='dependances_sortantes')
    tache_cible = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='dependances_entrantes')
    type_dependance = models.CharField(max_length=5, choices=TYPE_CHOICES, default='FD')

    class Meta:
        verbose_name = 'Dépendance tâche'
        unique_together = ['tache_source', 'tache_cible']


class CommentaireTache(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    contenu = models.TextField()
    fichier = models.FileField(upload_to='commentaires_taches/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']


class HistoriqueTache(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='historique')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    ancien_statut = models.CharField(max_length=15, blank=True)
    nouveau_statut = models.CharField(max_length=15, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


# ─── M15 : Livrables ──────────────────────────────────────────────────────────

class Livrable(models.Model):
    TYPE_CHOICES = [
        ('rapport', 'Rapport'),
        ('etude', 'Étude'),
        ('tdr', 'Termes de Référence'),
        ('manuel', 'Manuel/Guide'),
        ('document', 'Document'),
        ('logiciel', 'Logiciel'),
        ('plateforme', 'Plateforme'),
        ('bdd', 'Base de données'),
        ('api', 'API'),
        ('media', 'Photos/Vidéos'),
        ('enquete', 'Enquête'),
        ('cartographie', 'Cartographie'),
        ('infrastructure', 'Infrastructure'),
        ('formation', 'Formation'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('en_revision', 'En révision'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
    ]

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.CASCADE, related_name='livrables_exec'
    )
    activite = models.ForeignKey(
        ActiviteExecution, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='livrables',
    )
    code = models.CharField(max_length=30, blank=True)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type_livrable = models.CharField(max_length=15, choices=TYPE_CHOICES, default='rapport')
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='livrables_responsable',
    )
    date_prevue = models.DateField()
    date_livraison = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    version_courante = models.CharField(max_length=10, default='0.1')
    critere_acceptation = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='livrables_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Livrable'
        ordering = ['date_prevue']

    def __str__(self):
        return f"[{self.code}] {self.titre}"

    @property
    def est_en_retard(self):
        return (
            self.date_prevue < timezone.now().date()
            and self.statut not in ('valide', 'publie', 'archive')
        )

    def soumettre(self):
        self.statut = 'soumis'
        self.save(update_fields=['statut'])

    def publier(self):
        self.statut = 'publie'
        self.date_livraison = self.date_livraison or timezone.now().date()
        self.save(update_fields=['statut', 'date_livraison'])


class VersionLivrable(models.Model):
    livrable = models.ForeignKey(Livrable, on_delete=models.CASCADE, related_name='versions')
    numero_version = models.CharField(max_length=10)
    fichier = models.FileField(upload_to='livrables/%Y/%m/', null=True, blank=True)
    url_externe = models.URLField(blank=True)
    description_changements = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='versions_uploadees'
    )
    date_upload = models.DateTimeField(auto_now_add=True)
    est_courante = models.BooleanField(default=True)
    taille_fichier = models.BigIntegerField(default=0)

    class Meta:
        verbose_name = 'Version livrable'
        ordering = ['-date_upload']

    def save(self, *args, **kwargs):
        if self.est_courante:
            VersionLivrable.objects.filter(
                livrable=self.livrable, est_courante=True
            ).update(est_courante=False)
            self.livrable.version_courante = self.numero_version
            self.livrable.save(update_fields=['version_courante'])
        super().save(*args, **kwargs)


class ValidationLivrable(models.Model):
    ETAPE_CHOICES = [
        ('chef_projet', 'Chef Projet'),
        ('responsable_programme', 'Responsable Programme'),
        ('coordonnateur', 'Coordonnateur'),
        ('final', 'Validation finale'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('commente', 'Commenté'),
    ]

    livrable = models.ForeignKey(Livrable, on_delete=models.CASCADE, related_name='validations')
    etape = models.CharField(max_length=25, choices=ETAPE_CHOICES)
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='validations_livrables',
    )
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    commentaire = models.TextField(blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Validation livrable'
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
        self.livrable.statut = 'rejete'
        self.livrable.save(update_fields=['statut'])


class CommentaireLivrable(models.Model):
    livrable = models.ForeignKey(Livrable, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    contenu = models.TextField()
    fichier = models.FileField(upload_to='commentaires_livrables/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


# ─── M16 : Réunions ───────────────────────────────────────────────────────────

class Reunion(models.Model):
    TYPE_CHOICES = [
        ('interne', 'Réunion interne'),
        ('partenaires', 'Réunion partenaires'),
        ('bailleurs', 'Réunion bailleurs'),
        ('comite_pilotage', 'Comité de pilotage'),
        ('comite_technique', 'Comité technique'),
        ('atelier', 'Atelier'),
        ('seminaire', 'Séminaire'),
        ('formation', 'Formation'),
        ('conference', 'Conférence'),
    ]
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('confirmee', 'Confirmée'),
        ('reportee', 'Reportée'),
        ('annulee', 'Annulée'),
        ('en_cours', 'En cours'),
        ('tenue', 'Tenue'),
    ]
    PLATEFORME_CHOICES = [
        ('presentiel', 'Présentiel'),
        ('teams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('meet', 'Google Meet'),
        ('jitsi', 'Jitsi Meet'),
        ('hybride', 'Hybride'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    type_reunion = models.CharField(max_length=20, choices=TYPE_CHOICES)
    objet = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    organisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='reunions_organisees',
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reunions',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reunions',
    )
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField(null=True, blank=True)
    lieu = models.CharField(max_length=300, blank=True)
    plateforme = models.CharField(max_length=15, choices=PLATEFORME_CHOICES, default='presentiel')
    lien_visio = models.URLField(blank=True)
    id_reunion_virtuelle = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')
    rappel_envoye = models.BooleanField(default=False)
    rappel_24h = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reunions_creees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Réunion'
        ordering = ['-date', '-heure_debut']

    def __str__(self):
        return f"[{self.reference}] {self.objet}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from datetime import date
            count = Reunion.objects.count() + 1
            self.reference = f"REU-{date.today().year}-{count:04d}"
        super().save(*args, **kwargs)


class ParticipantReunion(models.Model):
    TYPE_CHOICES = [
        ('interne', 'Interne'),
        ('partenaire', 'Partenaire'),
        ('bailleur', 'Bailleur'),
        ('consultant', 'Consultant'),
        ('autre', 'Autre'),
    ]
    PRESENCE_CHOICES = [
        ('invite', 'Invité'),
        ('confirme', 'Confirmé'),
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('excuse', 'Excusé'),
    ]

    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='participants')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='participations_reunion',
    )
    nom_externe = models.CharField(max_length=200, blank=True)
    email_externe = models.EmailField(blank=True)
    fonction_externe = models.CharField(max_length=200, blank=True)
    organisation_externe = models.CharField(max_length=200, blank=True)
    type_participant = models.CharField(max_length=15, choices=TYPE_CHOICES, default='interne')
    statut_presence = models.CharField(max_length=10, choices=PRESENCE_CHOICES, default='invite')
    date_invitation = models.DateTimeField(null=True, blank=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    role_reunion = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Participant réunion'


class PointOrdreJour(models.Model):
    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='points_ordre_jour')
    ordre = models.IntegerField(default=0)
    intitule = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='points_presentes',
    )
    duree_prevue = models.IntegerField(default=15)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Point ordre du jour"
        ordering = ['ordre']


class CompteRendu(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
    ]

    reunion = models.OneToOneField(Reunion, on_delete=models.CASCADE, related_name='compte_rendu')
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comptes_rendus'
    )
    participants_presents = models.JSONField(default=list, blank=True)
    synthese = models.TextField(blank=True)
    discussions = models.TextField(blank=True)
    decisions_prises = models.TextField(blank=True)
    points_divers = models.TextField(blank=True)
    prochaine_reunion = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comptes_rendus_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    fichier_final = models.FileField(upload_to='comptes_rendus/%Y/%m/', null=True, blank=True)
    genere_par_ia = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compte rendu'


class DecisionReunion(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('realise', 'Réalisé'),
        ('reporte', 'Reporté'),
        ('annule', 'Annulé'),
    ]

    compte_rendu = models.ForeignKey(CompteRendu, on_delete=models.CASCADE, related_name='decisions')
    intitule = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='decisions_responsable',
    )
    echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_cours')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Décision réunion'
        ordering = ['echeance']


class ActionReunion(models.Model):
    STATUT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]

    compte_rendu = models.ForeignKey(CompteRendu, on_delete=models.CASCADE, related_name='actions')
    decision = models.ForeignKey(
        DecisionReunion, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions'
    )
    libelle = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='actions_reunion_responsable',
    )
    echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='a_faire')
    tache_generee = models.ForeignKey(
        Tache, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_source'
    )

    class Meta:
        verbose_name = 'Action réunion'
        ordering = ['echeance']

    def generer_tache(self, activite=None, created_by=None):
        if self.tache_generee:
            return self.tache_generee
        tache = Tache.objects.create(
            activite=activite,
            titre=self.libelle,
            description=self.description,
            assignee=self.responsable,
            date_echeance=self.echeance,
            statut='a_faire',
            created_by=created_by,
        )
        self.tache_generee = tache
        self.save(update_fields=['tache_generee'])
        return tache


# ─── M16 : Missions ───────────────────────────────────────────────────────────

class Mission(models.Model):
    TYPE_CHOICES = [
        ('terrain', 'Mission terrain'),
        ('supervision', 'Mission de supervision'),
        ('evaluation', "Mission d'évaluation"),
        ('audit', "Mission d'audit"),
        ('formation', 'Mission de formation'),
        ('partenariat', 'Mission de partenariat'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('approuvee', 'Approuvée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]

    reference = models.CharField(max_length=30, blank=True)
    objet = models.CharField(max_length=300)
    type_mission = models.CharField(max_length=15, choices=TYPE_CHOICES, default='terrain')
    description = models.TextField(blank=True)
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='missions',
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='missions',
    )
    lieu_depart = models.CharField(max_length=200, blank=True)
    destination = models.CharField(max_length=200)
    pays_destination = models.CharField(max_length=100, blank=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    demandeur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='missions_demandees'
    )
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='missions_approuvees',
    )
    date_approbation = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='planifiee')
    objectifs = models.TextField(blank=True)
    resultats_attendus = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mission'
        ordering = ['-date_debut']

    def __str__(self):
        return f"[{self.reference}] {self.objet}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from datetime import date
            count = Mission.objects.count() + 1
            self.reference = f"MSN-{date.today().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def duree_jours(self):
        return (self.date_fin - self.date_debut).days + 1

    def approuver(self, user):
        self.statut = 'approuvee'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation'])


class MembreMission(models.Model):
    ROLE_CHOICES = [
        ('chef_mission', 'Chef de mission'),
        ('membre', 'Membre'),
        ('chauffeur', 'Chauffeur'),
        ('consultant', 'Consultant'),
        ('observateur', 'Observateur'),
    ]

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='membres')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='missions_membre'
    )
    role_mission = models.CharField(max_length=15, choices=ROLE_CHOICES, default='membre')
    indemnite_journaliere = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frais_transport = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frais_hebergement = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    autres_frais = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Membre mission'
        unique_together = ['mission', 'user']

    @property
    def total_frais(self):
        return (
            self.indemnite_journaliere + self.frais_transport
            + self.frais_hebergement + self.autres_frais
        )


class OrdreMission(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('emis', 'Émis'),
        ('signe', 'Signé'),
        ('annule', 'Annulé'),
    ]

    mission = models.OneToOneField(Mission, on_delete=models.CASCADE, related_name='ordre_mission')
    numero = models.CharField(max_length=30, blank=True)
    date_emission = models.DateField(auto_now_add=True)
    signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ordres_signes'
    )
    contenu = models.TextField(blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    fichier = models.FileField(upload_to='ordres_mission/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ordre de mission'

    def save(self, *args, **kwargs):
        if not self.numero:
            from datetime import date
            count = OrdreMission.objects.count() + 1
            self.numero = f"OM-{date.today().year}-{count:04d}"
        super().save(*args, **kwargs)


class RapportMission(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
    ]

    mission = models.OneToOneField(Mission, on_delete=models.CASCADE, related_name='rapport')
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rapports_mission'
    )
    resume = models.TextField(blank=True)
    objectifs_atteints = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    suite_a_donner = models.TextField(blank=True)
    fichier = models.FileField(upload_to='rapports_mission/%Y/%m/', null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    date_soumission = models.DateField(null=True, blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_mission_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rapport de mission'


# ─── Rapport d'avancement projet ─────────────────────────────────────────────

class RapportAvancement(models.Model):
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
    ]

    TYPE_OBJET_CHOICES = [
        ('projet', 'Rapport de projet'),
        ('tache', 'Rapport de tâche'),
        ('reunion', 'Rapport de réunion'),
        ('mission', 'Rapport de mission'),
    ]

    type_objet = models.CharField(max_length=10, choices=TYPE_OBJET_CHOICES, default='projet')
    titre = models.CharField(max_length=300, blank=True)

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_avancement'
    )
    activite = models.ForeignKey(
        ActiviteExecution, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_avancement',
    )
    tache = models.ForeignKey(
        'Tache', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports',
    )
    reunion = models.ForeignKey(
        'Reunion', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports',
    )
    mission = models.ForeignKey(
        'Mission', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_avancement',
    )
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES)
    date_rapport = models.DateField()
    taux_realisation = models.DecimalField(max_digits=5, decimal_places=2)
    observations = models.TextField(blank=True)
    problemes = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    prochaines_etapes = models.TextField(blank=True)
    redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rapports_rediges'
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_valides',
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    fichier = models.FileField(upload_to='rapports/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rapport d'avancement"
        ordering = ['-date_rapport']
