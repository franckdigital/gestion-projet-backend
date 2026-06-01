from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M26 : Compte email ───────────────────────────────────────────────────────

class CompteEmail(models.Model):
    TYPE_CHOICES = [
        ('outlook', 'Microsoft Outlook / Exchange'),
        ('gmail', 'Gmail / Google Workspace'),
        ('imap', 'Serveur IMAP'),
        ('pop3', 'Serveur POP3'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('erreur', 'Erreur de connexion'),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comptes_email'
    )
    type_compte = models.CharField(max_length=10, choices=TYPE_CHOICES, default='imap')
    nom_affichage = models.CharField(max_length=200)
    adresse_email = models.EmailField()
    serveur_entrant = models.CharField(max_length=200, blank=True)
    port_entrant = models.IntegerField(default=993)
    serveur_sortant = models.CharField(max_length=200, blank=True)
    port_sortant = models.IntegerField(default=587)
    ssl_entrant = models.BooleanField(default=True)
    ssl_sortant = models.BooleanField(default=True)
    identifiant = models.CharField(max_length=200, blank=True)
    mot_de_passe = models.CharField(max_length=500, blank=True,
        help_text="Mot de passe ou App Password (stocké chiffré en production)")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    est_principal = models.BooleanField(default=False)
    derniere_synchro = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compte email'
        ordering = ['nom_affichage']

    def __str__(self):
        return f"{self.adresse_email} ({self.get_type_compte_display()})"


# ─── Signature email ──────────────────────────────────────────────────────────

class SignatureEmail(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='signatures_email'
    )
    compte = models.ForeignKey(
        CompteEmail, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='signatures'
    )
    nom = models.CharField(max_length=200)
    contenu_html = models.TextField(blank=True)
    contenu_texte = models.TextField(blank=True)
    est_principale = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Signature email'
        ordering = ['-est_principale', 'nom']

    def __str__(self):
        return f"{self.nom} — {self.utilisateur}"

    def save(self, *args, **kwargs):
        if self.est_principale:
            SignatureEmail.objects.filter(
                utilisateur=self.utilisateur, est_principale=True
            ).exclude(pk=self.pk).update(est_principale=False)
        super().save(*args, **kwargs)


# ─── Template de réponse ──────────────────────────────────────────────────────

class TemplateReponse(models.Model):
    TYPE_CHOICES = [
        ('accusé_reception', 'Accusé de réception'),
        ('demande_info', "Demande d'informations complémentaires"),
        ('validation', 'Validation / Accord'),
        ('refus', 'Refus / Rejet'),
        ('transmission', 'Transmission / Transfert'),
        ('relance', 'Relance'),
        ('convocation', 'Convocation à réunion'),
        ('autre', 'Autre'),
    ]
    LANGUE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'Anglais'),
        ('ar', 'Arabe'),
    ]

    titre = models.CharField(max_length=300)
    type_template = models.CharField(max_length=25, choices=TYPE_CHOICES, default='autre')
    sujet_template = models.CharField(max_length=500, blank=True,
                                      help_text="Modèle de sujet. Utilisez {{sujet_original}} pour inclure le sujet d'origine.")
    corps_html = models.TextField(blank=True)
    corps_texte = models.TextField()
    langue = models.CharField(max_length=5, choices=LANGUE_CHOICES, default='fr')
    variables = models.JSONField(default=list, blank=True,
                                 help_text="Variables disponibles dans ce template, ex: ['nom_destinataire', 'date']")
    est_global = models.BooleanField(default=False, help_text="Accessible à tous les utilisateurs")
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='templates_email_crees'
    )
    nb_utilisations = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template de réponse'
        ordering = ['type_template', 'titre']

    def __str__(self):
        return f"[{self.get_type_template_display()}] {self.titre}"


# ─── Règle de classification automatique ─────────────────────────────────────

class RegleClassification(models.Model):
    OPERATEUR_CHOICES = [
        ('et', 'Toutes les conditions (ET)'),
        ('ou', 'Au moins une condition (OU)'),
    ]
    ACTION_CHOICES = [
        ('etiqueter', 'Ajouter une étiquette'),
        ('classer_projet', 'Classer dans un projet'),
        ('classer_programme', 'Classer dans un programme'),
        ('marquer_urgent', 'Marquer comme urgent'),
        ('archiver', 'Archiver automatiquement'),
        ('notifier', 'Envoyer une notification'),
        ('assigner_ia', 'Déclencher analyse IA'),
    ]

    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    priorite = models.IntegerField(default=0, help_text="Ordre d'application (plus petit = plus prioritaire)")
    operateur = models.CharField(max_length=5, choices=OPERATEUR_CHOICES, default='et')

    # Conditions (JSON array of {champ, operateur, valeur})
    # champ: expediteur_email, sujet, corps_texte, direction
    # operateur: contient, ne_contient_pas, egal, commence_par, finit_par
    conditions = models.JSONField(default=list,
                                  help_text='[{"champ": "sujet", "operateur": "contient", "valeur": "urgent"}]')

    # Action
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='etiqueter')
    parametres_action = models.JSONField(default=dict, blank=True,
                                         help_text='{"etiquette_id": 1} ou {"projet_id": 5}')

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='regles_classification'
    )
    nb_applications = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Règle de classification'
        ordering = ['priorite', 'nom']

    def __str__(self):
        return f"[Prio {self.priorite}] {self.nom}"

    def evaluer_conditions(self, email):
        """Vérifie si les conditions de la règle sont remplies pour cet email."""
        resultats = []
        for cond in self.conditions:
            champ = cond.get('champ', '')
            op = cond.get('operateur', 'contient')
            valeur = cond.get('valeur', '').lower()

            valeur_email = ''
            if champ == 'expediteur_email':
                valeur_email = (email.expediteur_email or '').lower()
            elif champ == 'sujet':
                valeur_email = (email.sujet or '').lower()
            elif champ == 'corps_texte':
                valeur_email = (email.corps_texte or '').lower()
            elif champ == 'direction':
                valeur_email = (email.direction or '').lower()

            if op == 'contient':
                resultats.append(valeur in valeur_email)
            elif op == 'ne_contient_pas':
                resultats.append(valeur not in valeur_email)
            elif op == 'egal':
                resultats.append(valeur_email == valeur)
            elif op == 'commence_par':
                resultats.append(valeur_email.startswith(valeur))
            elif op == 'finit_par':
                resultats.append(valeur_email.endswith(valeur))
            else:
                resultats.append(False)

        if not resultats:
            return False
        return all(resultats) if self.operateur == 'et' else any(resultats)

    def appliquer(self, email):
        """Applique l'action de la règle à l'email si les conditions sont remplies."""
        if not self.evaluer_conditions(email):
            return False

        params = self.parametres_action or {}
        if self.action == 'etiqueter':
            etiquette_id = params.get('etiquette_id')
            if etiquette_id:
                try:
                    etiq = EtiquetteEmail.objects.get(id=etiquette_id)
                    etiq.emails.add(email)
                except EtiquetteEmail.DoesNotExist:
                    pass
        elif self.action == 'classer_projet':
            projet_id = params.get('projet_id')
            if projet_id:
                email.projet_id = projet_id
                email.save(update_fields=['projet'])
        elif self.action == 'classer_programme':
            programme_id = params.get('programme_id')
            if programme_id:
                email.programme_id = programme_id
                email.save(update_fields=['programme'])
        elif self.action == 'marquer_urgent':
            email.priorite = 'haute'
            email.score_urgence = 90
            email.save(update_fields=['priorite', 'score_urgence'])
        elif self.action == 'archiver':
            email.statut = 'archive'
            email.save(update_fields=['statut'])
        elif self.action == 'assigner_ia':
            email.traite_par_ia = True
            email.save(update_fields=['traite_par_ia'])

        self.nb_applications += 1
        self.save(update_fields=['nb_applications'])
        return True


# ─── Email ────────────────────────────────────────────────────────────────────

class Email(models.Model):
    DIRECTION_CHOICES = [
        ('entrant', 'Entrant'),
        ('sortant', 'Sortant'),
        ('brouillon', 'Brouillon'),
    ]
    PRIORITE_CHOICES = [
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('basse', 'Basse'),
    ]
    STATUT_CHOICES = [
        ('non_lu', 'Non lu'),
        ('lu', 'Lu'),
        ('repondu', 'Répondu'),
        ('transfiere', 'Transféré'),
        ('archive', 'Archivé'),
        ('supprime', 'Supprimé'),
        ('spam', 'Spam'),
    ]

    compte = models.ForeignKey(
        CompteEmail, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails'
    )
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_id = models.CharField(max_length=500, blank=True)
    sujet = models.CharField(max_length=500)
    corps_html = models.TextField(blank=True)
    corps_texte = models.TextField(blank=True)
    expediteur = models.CharField(max_length=300)
    expediteur_email = models.EmailField()
    destinataires = models.JSONField(default=list)
    destinataires_cc = models.JSONField(default=list, blank=True)
    destinataires_cci = models.JSONField(default=list, blank=True)
    date_envoi = models.DateTimeField(null=True, blank=True)
    date_reception = models.DateTimeField(null=True, blank=True)
    date_envoi_differe = models.DateTimeField(null=True, blank=True)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='non_lu')
    est_lu = models.BooleanField(default=False)
    lu_le = models.DateTimeField(null=True, blank=True)
    en_reponse_a = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reponses'
    )
    thread_id = models.CharField(max_length=300, blank=True)

    # Liaison ERP
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='emails'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='emails'
    )
    activite = models.ForeignKey(
        'execution.ActiviteExecution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='emails'
    )
    reunion = models.ForeignKey(
        'execution.Reunion', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='emails'
    )

    # IA
    resume_ia = models.TextField(blank=True)
    actions_detectees = models.JSONField(default=list, blank=True)
    echeances_detectees = models.JSONField(default=list, blank=True)
    categorie_ia = models.CharField(max_length=200, blank=True)
    score_urgence = models.IntegerField(default=0)
    risques_detectes = models.JSONField(default=list, blank=True)
    traite_par_ia = models.BooleanField(default=False)
    suggestion_reponse_ia = models.TextField(blank=True)

    archive_ged = models.BooleanField(default=False)
    document_ged = models.ForeignKey(
        'ged.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='emails'
    )

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='emails_geres'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email'
        ordering = ['-date_reception', '-created_at']

    def __str__(self):
        return f"[{self.direction}] {self.sujet}"

    def marquer_lu(self):
        if not self.est_lu:
            self.est_lu = True
            self.lu_le = timezone.now()
            self.statut = 'lu'
            self.save(update_fields=['est_lu', 'lu_le', 'statut'])

    def get_thread(self):
        """Retourne tous les emails du même thread."""
        if self.thread_id:
            return Email.objects.filter(thread_id=self.thread_id).order_by('date_reception', 'created_at')
        emails = [self]
        parent = self.en_reponse_a
        while parent:
            emails.insert(0, parent)
            parent = parent.en_reponse_a
        reponses = list(self.reponses.order_by('date_envoi', 'created_at'))
        return emails + reponses

    def appliquer_regles(self):
        """Applique les règles de classification actives."""
        for regle in RegleClassification.objects.filter(actif=True).order_by('priorite'):
            regle.appliquer(self)


class PieceJointeEmail(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='pieces_jointes')
    nom_fichier = models.CharField(max_length=300)
    type_mime = models.CharField(max_length=100, blank=True)
    taille = models.BigIntegerField(default=0)
    fichier = models.FileField(upload_to='emails/pj/%Y/%m/', null=True, blank=True)
    document_ged = models.ForeignKey(
        'ged.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pj_emails'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe email'

    def __str__(self):
        return f"{self.nom_fichier}"


class ActionEmail(models.Model):
    TYPE_CHOICES = [
        ('tache', 'Tâche'),
        ('activite', 'Activité'),
        ('reunion', 'Réunion'),
        ('livrable', 'Livrable'),
        ('courrier', 'Courrier administratif'),
        ('incident', 'Incident'),
    ]
    STATUT_CHOICES = [
        ('detectee', 'Détectée'),
        ('validee', 'Validée'),
        ('convertie', 'Convertie'),
        ('ignoree', 'Ignorée'),
    ]

    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='action_emails')
    type_action = models.CharField(max_length=15, choices=TYPE_CHOICES, default='tache')
    description = models.TextField()
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='actions_email'
    )
    echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='detectee')
    detectee_par_ia = models.BooleanField(default=True)
    objet_genere_id = models.IntegerField(null=True, blank=True)
    objet_genere_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Action email'
        ordering = ['echeance']

    def __str__(self):
        return f"[{self.get_type_action_display()}] {self.description[:80]}"


class LienEmail(models.Model):
    """Lie un email intelligent à un objet ERP (courrier, diligence, réunion, tâche)."""
    OBJET_TYPE_CHOICES = [
        ('courrier_entrant',  'Courrier entrant'),
        ('courrier_sortant',  'Courrier sortant'),
        ('diligence',         'Diligence'),
        ('reunion',           'Réunion'),
        ('tache',             'Tâche'),
    ]
    email      = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='liens')
    objet_type = models.CharField(max_length=20, choices=OBJET_TYPE_CHOICES)
    objet_id   = models.PositiveIntegerField()
    objet_libelle = models.CharField(max_length=300, blank=True)
    note       = models.CharField(max_length=300, blank=True)
    cree_par   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='liens_emails'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lien email'
        unique_together = ['email', 'objet_type', 'objet_id']

    def __str__(self):
        return f"{self.email.sujet} → {self.objet_type}#{self.objet_id}"


class EtiquetteEmail(models.Model):
    nom = models.CharField(max_length=100)
    couleur = models.CharField(max_length=7, default='#3388ff')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='etiquettes_email'
    )
    emails = models.ManyToManyField(Email, related_name='etiquettes', blank=True)

    class Meta:
        verbose_name = 'Étiquette email'

    def __str__(self):
        return self.nom
