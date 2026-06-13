from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class EmployeProjet(models.Model):
    TYPE_CHOICES = [
        ('employe', 'Employé permanent'), ('consultant', 'Consultant'),
        ('volontaire', 'Volontaire'), ('expert', 'Expert international'), ('stagiaire', 'Stagiaire'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'), ('inactif', 'Inactif'), ('conge', 'En congé'), ('mission', 'En mission'),
    ]
    NIVEAU_CHOICES = [
        ('junior', 'Junior'), ('intermediaire', 'Intermédiaire'), ('senior', 'Senior'), ('expert', 'Expert'),
    ]

    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='employe_profil')
    matricule = models.CharField(max_length=30, blank=True, unique=True)
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200)
    type_personnel = models.CharField(max_length=15, choices=TYPE_CHOICES, default='employe')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    poste = models.CharField(max_length=200, blank=True)
    specialite = models.CharField(max_length=200, blank=True)
    niveau_expertise = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='intermediaire')
    date_embauche = models.DateField(null=True, blank=True)
    date_fin_contrat = models.DateField(null=True, blank=True)
    taux_journalier = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    devise = models.CharField(max_length=5, default='XOF')
    taux_occupation_max = models.IntegerField(default=100)
    competences = models.JSONField(default=list, blank=True)
    cv = models.FileField(upload_to='rh/cv/%Y/', null=True, blank=True)
    photo = models.ImageField(upload_to='rh/photos/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employé projet'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"[{self.matricule}] {self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.matricule:
            count = EmployeProjet.objects.count() + 1
            self.matricule = f"EMP-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class AffectationRH(models.Model):
    STATUT_CHOICES = [
        ('active', 'Active'), ('terminee', 'Terminée'),
        ('suspendue', 'Suspendue'), ('annulee', 'Annulée'),
    ]

    employe = models.ForeignKey(EmployeProjet, on_delete=models.CASCADE, related_name='affectations')
    programme = models.ForeignKey('programmes_projets.Programme', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='affectations_rh')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='affectations_rh')
    activite = models.ForeignKey('execution.ActiviteExecution', on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='affectations_rh')
    role = models.CharField(max_length=200)
    taux_affectation = models.IntegerField(default=100,
                                            validators=[MinValueValidator(1), MaxValueValidator(100)])
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='active')
    description = models.TextField(blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name='affectations_rh_creees')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Affectation RH'
        ordering = ['-date_debut']

    def __str__(self):
        ref = self.projet or self.programme or "N/A"
        return f"{self.employe.nom_complet} → {ref} ({self.taux_affectation}%)"


class FeuilleTemps(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'), ('soumise', 'Soumise'),
        ('validee', 'Validée'), ('rejetee', 'Rejetée'),
    ]

    employe = models.ForeignKey(EmployeProjet, on_delete=models.CASCADE, related_name='feuilles_temps')
    mois = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    annee = models.IntegerField()
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    total_heures = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_jours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    montant_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valideur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='feuilles_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Feuille de temps'
        unique_together = ['employe', 'mois', 'annee']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"Feuille {self.employe.nom_complet} — {self.mois:02d}/{self.annee}"

    def calculer_totaux(self):
        from django.db.models import Sum
        agg = self.lignes.aggregate(h=Sum('heures'))
        self.total_heures = agg['h'] or 0
        self.total_jours = round(float(self.total_heures) / 8, 2)
        if self.employe.taux_journalier:
            self.montant_total = float(self.total_jours) * float(self.employe.taux_journalier)
        self.save(update_fields=['total_heures', 'total_jours', 'montant_total'])


class LigneFeuilleTemps(models.Model):
    feuille = models.ForeignKey(FeuilleTemps, on_delete=models.CASCADE, related_name='lignes')
    date = models.DateField()
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='lignes_feuille_temps')
    activite = models.ForeignKey('execution.ActiviteExecution', on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='lignes_feuille_temps')
    heures = models.DecimalField(max_digits=4, decimal_places=2,
                                  validators=[MinValueValidator(0), MaxValueValidator(24)])
    description = models.CharField(max_length=300, blank=True)
    est_jour_ferie = models.BooleanField(default=False)
    est_conge = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Ligne feuille de temps'
        ordering = ['date']

    def __str__(self):
        return f"{self.feuille.employe.nom_complet} — {self.date} — {self.heures}h"


class EvaluationPerformance(models.Model):
    PERIODE_CHOICES = [
        ('mensuelle', 'Mensuelle'), ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'), ('annuelle', 'Annuelle'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'), ('en_cours', 'En cours'),
        ('soumise', 'Soumise'), ('validee', 'Validée'),
    ]

    employe = models.ForeignKey(EmployeProjet, on_delete=models.CASCADE, related_name='evaluations')
    evaluateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='evaluations_effectuees')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='evaluations_rh')
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='annuelle')
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True,
                                     validators=[MinValueValidator(1), MaxValueValidator(4)])
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    note_globale = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(0), MaxValueValidator(20)])
    criteres = models.JSONField(default=dict, blank=True)
    points_forts = models.TextField(blank=True)
    axes_amelioration = models.TextField(blank=True)
    objectifs_periode_suivante = models.TextField(blank=True)
    commentaire_employe = models.TextField(blank=True)
    date_evaluation = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Évaluation de performance'
        ordering = ['-annee']

    def __str__(self):
        return f"Évaluation {self.employe.nom_complet} — {self.annee}"


class BesoinFormation(models.Model):
    STATUT_CHOICES = [
        ('identifie', 'Identifié'), ('valide', 'Validé'),
        ('planifie', 'Planifié'), ('realise', 'Réalisé'), ('annule', 'Annulé'),
    ]
    PRIORITE_CHOICES = [
        ('basse', 'Basse'), ('normale', 'Normale'),
        ('haute', 'Haute'), ('critique', 'Critique'),
    ]

    employe = models.ForeignKey(EmployeProjet, on_delete=models.CASCADE, related_name='besoins_formation')
    projet = models.ForeignKey('programmes_projets.Projet', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='besoins_formation')
    intitule = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    domaine = models.CharField(max_length=200, blank=True)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='identifie')
    date_souhaitee = models.DateField(null=True, blank=True)
    date_realisation = models.DateField(null=True, blank=True)
    cout_estime = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cout_reel = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    duree_jours = models.IntegerField(default=1)
    organisme_formation = models.CharField(max_length=300, blank=True)
    lieu = models.CharField(max_length=200, blank=True)
    attestation = models.FileField(upload_to='rh/formations/%Y/', null=True, blank=True)
    identifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                       related_name='besoins_formation_identifies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Besoin de formation'
        ordering = ['-priorite', 'date_souhaitee']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.intitule}"


class DemandeConge(models.Model):
    TYPE_CHOICES = [
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('maternite', 'Congé maternité'),
        ('paternite', 'Congé paternité'),
        ('exceptionnel', 'Congé exceptionnel'),
        ('sans_solde', 'Congé sans solde'),
        ('recuperation', 'Récupération'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumise', 'Soumise'),
        ('approuvee', 'Approuvée'),
        ('rejetee', 'Rejetée'),
        ('annulee', 'Annulée'),
    ]

    employe = models.ForeignKey(
        EmployeProjet, on_delete=models.CASCADE, related_name='demandes_conge'
    )
    type_conge = models.CharField(max_length=20, choices=TYPE_CHOICES, default='annuel')
    date_debut = models.DateField()
    date_fin = models.DateField()
    nombre_jours = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    motif = models.TextField(blank=True)
    piece_justificative = models.FileField(
        upload_to='rh/conges/%Y/', null=True, blank=True
    )
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='conges_approuves'
    )
    date_approbation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demande de congé'
        verbose_name_plural = 'Demandes de congé'
        ordering = ['-created_at']

    def __str__(self):
        return f"Congé {self.employe.nom_complet} — {self.date_debut} → {self.date_fin}"

    def save(self, *args, **kwargs):
        if self.date_debut and self.date_fin:
            delta = (self.date_fin - self.date_debut).days + 1
            self.nombre_jours = max(delta, 0)
        super().save(*args, **kwargs)

    def soumettre(self):
        self.statut = 'soumise'
        self.save(update_fields=['statut'])

    def approuver(self, user):
        self.statut = 'approuvee'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation'])
        self.employe.statut = 'conge'
        self.employe.save(update_fields=['statut'])

    def rejeter(self, user, motif=''):
        self.statut = 'rejetee'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.motif_rejet = motif
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation', 'motif_rejet'])


class DemandeAbsence(models.Model):
    TYPE_CHOICES = [
        ('autorisation', 'Autorisation d\'absence'),
        ('absence_injustifiee', 'Absence injustifiée'),
        ('absence_justifiee', 'Absence justifiée'),
        ('retard', 'Retard'),
        ('mission', 'Absence pour mission'),
        ('formation', 'Absence pour formation'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('soumise', 'Soumise'),
        ('approuvee', 'Approuvée'),
        ('rejetee', 'Rejetée'),
        ('annulee', 'Annulée'),
    ]

    employe = models.ForeignKey(
        EmployeProjet, on_delete=models.CASCADE, related_name='demandes_absence'
    )
    type_absence = models.CharField(max_length=25, choices=TYPE_CHOICES, default='autorisation')
    date_absence = models.DateField()
    heure_debut = models.TimeField(null=True, blank=True)
    heure_fin = models.TimeField(null=True, blank=True)
    duree_heures = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    motif = models.TextField()
    piece_justificative = models.FileField(
        upload_to='rh/absences/%Y/', null=True, blank=True
    )
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='soumise')
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='absences_approuvees'
    )
    date_approbation = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demande d\'absence'
        verbose_name_plural = 'Demandes d\'absence'
        ordering = ['-date_absence']

    def __str__(self):
        return f"Absence {self.employe.nom_complet} — {self.date_absence} ({self.type_absence})"

    def approuver(self, user):
        self.statut = 'approuvee'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation'])

    def rejeter(self, user, motif=''):
        self.statut = 'rejetee'
        self.approuve_par = user
        self.date_approbation = timezone.now()
        self.motif_rejet = motif
        self.save(update_fields=['statut', 'approuve_par', 'date_approbation', 'motif_rejet'])


class OccurrenceSpeciale(models.Model):
    TYPE_CHOICES = [
        ('naissance', 'Naissance'),
        ('deces_conjoint', 'Décès conjoint'),
        ('deces_enfant', 'Décès enfant'),
        ('deces_parent', 'Décès parent'),
        ('mariage', 'Mariage'),
        ('maladie_grave', 'Maladie grave'),
        ('accident', 'Accident de travail'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('soumise', 'Soumise'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée'),
    ]

    employe = models.ForeignKey(
        EmployeProjet, on_delete=models.CASCADE, related_name='occurrences_speciales'
    )
    type_occurrence = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_evenement = models.DateField()
    description = models.TextField(blank=True)
    jours_accordes = models.IntegerField(default=0)
    date_debut_conge = models.DateField(null=True, blank=True)
    date_fin_conge = models.DateField(null=True, blank=True)
    piece_justificative = models.FileField(
        upload_to='rh/occurrences/%Y/', null=True, blank=True
    )
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='soumise')
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='occurrences_validees'
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Occurrence spéciale'
        verbose_name_plural = 'Occurrences spéciales'
        ordering = ['-date_evenement']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.get_type_occurrence_display()} ({self.date_evenement})"

    def valider(self, user):
        self.statut = 'validee'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'valide_par', 'date_validation'])
