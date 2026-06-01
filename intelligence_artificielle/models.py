from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M31 : Assistant IA ───────────────────────────────────────────────────────

class ConversationIA(models.Model):
    CONTEXTE_CHOICES = [
        ('general', 'Général'),
        ('projet', 'Projet'),
        ('budget', 'Budget'),
        ('indicateurs', 'Indicateurs S&E'),
        ('courriers', 'Courriers'),
        ('documents', 'Documents GED'),
        ('rapports', 'Rapports'),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_ia'
    )
    titre = models.CharField(max_length=200, blank=True)
    contexte = models.CharField(max_length=20, choices=CONTEXTE_CHOICES, default='general')
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conversations_ia'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conversations_ia'
    )
    archivee = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversation IA'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation IA — {self.utilisateur} — {self.created_at.date()}"


class MessageIA(models.Model):
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant IA'),
        ('systeme', 'Système'),
    ]

    conversation = models.ForeignKey(ConversationIA, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    contenu = models.TextField()
    requete_metier = models.JSONField(default=dict, blank=True,
        help_text="Requête Django/SQL générée par l'IA")
    donnees_contexte = models.JSONField(default=dict, blank=True)
    tokens_utilises = models.IntegerField(default=0)
    duree_traitement_ms = models.IntegerField(default=0)
    confiance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message IA'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.contenu[:80]}"


# ─── M32 : Génération documentaire IA ────────────────────────────────────────

class GenerationDocument(models.Model):
    TYPE_CHOICES = [
        ('tdr', 'TDR (Termes de Référence)'),
        ('swot', 'Analyse SWOT'),
        ('cadre_logique', 'Cadre logique'),
        ('rapport_activites', "Rapport d'activités"),
        ('rapport_bailleur', 'Rapport bailleur'),
        ('compte_rendu', 'Compte rendu'),
        ('courrier', 'Courrier'),
        ('note_synthese', 'Note de synthèse'),
        ('plan_action', "Plan d'action"),
        ('rapport_se', 'Rapport S&E'),
        ('rapport_financier', 'Rapport financier'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours de génération'),
        ('complete', 'Complète'),
        ('erreur', 'Erreur'),
        ('revise', 'En révision'),
        ('valide', 'Validé'),
    ]
    MODE_CHOICES = [
        ('generation', 'Génération complète'),
        ('réécriture', 'Réécriture / Reformulation'),
        ('resume', 'Résumé'),
        ('traduction', 'Traduction'),
        ('correction', 'Correction'),
    ]

    demande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='generations_documents'
    )
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='generation')
    titre = models.CharField(max_length=300)
    langue = models.CharField(max_length=10, default='fr')

    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='generations_ia'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='generations_ia'
    )

    instructions = models.TextField(blank=True)
    texte_source = models.TextField(blank=True)
    parametres = models.JSONField(default=dict, blank=True)

    contenu_genere = models.TextField(blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    score_qualite = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tokens_utilises = models.IntegerField(default=0)

    document_ged = models.ForeignKey(
        'ged.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='generations_ia'
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='generations_validees'
    )
    date_validation = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Génération documentaire IA'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_document_display()}] {self.titre}"

    def executer(self):
        self.statut = 'en_cours'
        self.save(update_fields=['statut'])
        try:
            contexte = ""
            if self.projet:
                contexte += f"Projet: {self.projet.titre}. "
            if self.programme:
                contexte += f"Programme: {self.programme.intitule}. "
            templates = {
                'tdr': f"TERMES DE RÉFÉRENCE\n\n1. CONTEXTE\n{contexte}\n2. OBJECTIFS\n[À compléter]\n3. ACTIVITÉS\n[À compléter]\n4. LIVRABLES\n[À compléter]\n5. PROFIL REQUIS\n[À compléter]",
                'swot': f"ANALYSE SWOT — {self.titre}\n\nFORCES\n- [À compléter]\n\nFAIBLESSES\n- [À compléter]\n\nOPPORTUNITÉS\n- [À compléter]\n\nMENACES\n- [À compléter]",
                'compte_rendu': f"COMPTE RENDU\n\nObjet: {self.titre}\n{contexte}\n\nPARTICIPANTS\n[Liste des participants]\n\nDISCUSSIONS\n{self.instructions}\n\nDÉCISIONS\n[À compléter]\n\nACTIONS\n[À compléter]",
            }
            contenu = templates.get(self.type_document,
                f"[DOCUMENT GÉNÉRÉ PAR IA]\n\nType: {self.get_type_document_display()}\nTitre: {self.titre}\n{contexte}\n\n{self.instructions}")
            if self.texte_source and self.mode == 'resume':
                contenu = f"[RÉSUMÉ]\n\n{self.texte_source[:500]}..."
            self.contenu_genere = contenu
            self.statut = 'complete'
            self.score_qualite = 75
            self.tokens_utilises = len(contenu.split())
            self.completed_at = timezone.now()
            self.save(update_fields=['contenu_genere', 'statut', 'score_qualite',
                                      'tokens_utilises', 'completed_at'])
        except Exception as e:
            self.statut = 'erreur'
            self.save(update_fields=['statut'])


# ─── M33 : IA Prédictive ──────────────────────────────────────────────────────

class ModeleIA(models.Model):
    TYPE_CHOICES = [
        ('prevision_budget', 'Prévision budgétaire'),
        ('prevision_indicateur', 'Prévision indicateurs'),
        ('prevision_tresorerie', 'Prévision trésorerie'),
        ('prevision_livrable', 'Prévision livrables'),
        ('detection_anomalie', 'Détection des anomalies'),
        ('detection_retard', 'Détection des retards'),
        ('detection_fraude', 'Détection des fraudes potentielles'),
        ('recommandation', 'Recommandation stratégique'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('en_entrainement', 'En entraînement'),
    ]

    nom = models.CharField(max_length=200)
    type_modele = models.CharField(max_length=25, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    version = models.CharField(max_length=10, default='1.0')
    precision = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    parametres = models.JSONField(default=dict, blank=True)
    derniere_execution = models.DateTimeField(null=True, blank=True)
    nb_executions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Modèle IA'

    def __str__(self):
        return f"{self.nom} v{self.version} ({self.get_type_modele_display()})"


class AnalyseIAPredictive(models.Model):
    TYPE_CHOICES = ModeleIA.TYPE_CHOICES
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('complete', 'Complète'),
        ('erreur', 'Erreur'),
    ]

    modele = models.ForeignKey(
        ModeleIA, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses'
    )
    type_analyse = models.CharField(max_length=25, choices=TYPE_CHOICES)
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses_ia_predictives'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analyses_ia_predictives'
    )
    parametres = models.JSONField(default=dict, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')

    resultats = models.JSONField(default=dict, blank=True)
    previsions = models.JSONField(default=list, blank=True)
    anomalies = models.JSONField(default=list, blank=True)
    suggestions_ia = models.TextField(blank=True)
    score_confiance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    demande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='analyses_ia_demandees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Analyse IA prédictive'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_analyse_display()}] {self.created_at.date()}"


class AlerteIA(models.Model):
    NIVEAU_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critique', 'Critique'),
    ]
    TYPE_CHOICES = [
        ('retard_prevu', 'Retard prévu'),
        ('depassement_budget', 'Dépassement budgétaire prévu'),
        ('risque_identifie', 'Risque identifié'),
        ('anomalie', 'Anomalie détectée'),
        ('derive', 'Dérive détectée'),
        ('fraude_potentielle', 'Fraude potentielle'),
    ]

    analyse = models.ForeignKey(
        AnalyseIAPredictive, on_delete=models.CASCADE, related_name='alertes'
    )
    type_alerte = models.CharField(max_length=25, choices=TYPE_CHOICES)
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, default='warning')
    titre = models.CharField(max_length=300)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alertes_ia'
    )
    lue = models.BooleanField(default=False)
    traitee = models.BooleanField(default=False)
    date_alerte = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Alerte IA'
        ordering = ['-date_alerte']

    def __str__(self):
        return f"[{self.niveau}] {self.titre}"


class RecommandationIA(models.Model):
    TYPE_CHOICES = [
        ('action_corrective', 'Action corrective'),
        ('reallocation', 'Réallocation de ressources'),
        ('revision_calendrier', 'Révision du calendrier'),
        ('mitigation_risque', 'Mitigation de risque'),
        ('opportunite', 'Saisie d\'opportunité'),
        ('strategie', 'Recommandation stratégique'),
    ]
    STATUT_CHOICES = [
        ('proposee', 'Proposée'),
        ('acceptee', 'Acceptée'),
        ('rejetee', 'Rejetée'),
        ('en_cours', 'En cours de mise en œuvre'),
        ('implementee', 'Implémentée'),
    ]

    analyse = models.ForeignKey(
        AnalyseIAPredictive, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recommandations'
    )
    type_recommandation = models.CharField(max_length=25, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=300)
    description = models.TextField()
    justification = models.TextField(blank=True)
    impact_estime = models.TextField(blank=True)
    priorite = models.IntegerField(default=3,
        help_text="1=Faible, 2=Moyenne, 3=Haute, 4=Critique")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='proposee')
    score_pertinence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recommandations_ia'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recommandations_ia'
    )
    acceptee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recommandations_acceptees'
    )
    date_decision = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recommandation IA'
        ordering = ['-priorite', '-created_at']

    def __str__(self):
        return f"[{self.get_type_recommandation_display()}] {self.titre}"


class JournalIA(models.Model):
    """Traçabilité obligatoire de toutes les actions IA (RG-IA-001, RG-IA-003)."""
    TYPE_CHOICES = [
        ('conversation', 'Conversation assistant'),
        ('generation', 'Génération documentaire'),
        ('analyse_predictive', 'Analyse prédictive'),
        ('alerte', 'Alerte IA'),
        ('recommandation', 'Recommandation'),
        ('classification', 'Classification automatique'),
        ('resume', 'Résumé automatique'),
    ]

    type_action = models.CharField(max_length=25, choices=TYPE_CHOICES)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='journal_ia'
    )
    objet_type = models.CharField(max_length=50, blank=True)
    objet_id = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    parametres_entree = models.JSONField(default=dict, blank=True)
    resultats_sortie = models.JSONField(default=dict, blank=True)
    tokens_utilises = models.IntegerField(default=0)
    duree_ms = models.IntegerField(default=0)
    succes = models.BooleanField(default=True)
    message_erreur = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Journal IA'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_action_display()}] {self.utilisateur} — {self.created_at}"
