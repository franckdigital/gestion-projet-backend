from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M28 : Messagerie interne ─────────────────────────────────────────────────

class Canal(models.Model):
    TYPE_CHOICES = [
        ('prive', 'Discussion privée'),
        ('groupe', 'Groupe'),
        ('projet', 'Canal projet'),
        ('programme', 'Canal programme'),
        ('direction', 'Canal direction'),
    ]

    nom = models.CharField(max_length=200)
    type_canal = models.CharField(max_length=15, choices=TYPE_CHOICES, default='groupe')
    description = models.TextField(blank=True)
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='canaux_messagerie'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='canaux_messagerie'
    )
    membres = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='canaux_messagerie', blank=True,
        through='MembreCanal'
    )
    est_prive = models.BooleanField(default=False)
    archive = models.BooleanField(default=False)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='canaux_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Canal messagerie'
        ordering = ['nom']

    def __str__(self):
        return f"[{self.get_type_canal_display()}] {self.nom}"


class MembreCanal(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('membre', 'Membre'),
        ('observateur', 'Observateur'),
    ]

    canal = models.ForeignKey(Canal, on_delete=models.CASCADE, related_name='memberships')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships_canal'
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='membre')
    rejoint_le = models.DateTimeField(auto_now_add=True)
    dernier_lu = models.DateTimeField(null=True, blank=True)
    notifications_actives = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Membre canal'
        unique_together = ['canal', 'utilisateur']


class Message(models.Model):
    TYPE_CHOICES = [
        ('texte', 'Texte'),
        ('fichier', 'Fichier'),
        ('image', 'Image'),
        ('systeme', 'Message système'),
    ]

    canal = models.ForeignKey(Canal, on_delete=models.CASCADE, related_name='messages')
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='messages_envoyes'
    )
    type_message = models.CharField(max_length=10, choices=TYPE_CHOICES, default='texte')
    contenu = models.TextField()
    fichier = models.FileField(upload_to='messagerie/%Y/%m/', null=True, blank=True)
    en_reponse_a = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reponses'
    )
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='messages_mentionnes', blank=True
    )
    reactions = models.JSONField(default=dict, blank=True)
    modifie = models.BooleanField(default=False)
    supprime = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Message'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.canal.nom}] {self.contenu[:60]}"


class LectureMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='lectures')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_lus'
    )
    lu_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'utilisateur']


# ─── Notifications ────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_CHOICES = [
        ('systeme', 'Système'),
        ('projet', 'Projet'),
        ('budget', 'Budget'),
        ('courrier', 'Courrier'),
        ('reunion', 'Réunion'),
        ('tache', 'Tâche'),
        ('livrable', 'Livrable'),
        ('document', 'Document'),
        ('message', 'Messagerie'),
        ('alerte', 'Alerte'),
    ]
    CANAL_CHOICES = [
        ('interne', 'Interne (app)'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push mobile'),
        ('whatsapp', 'WhatsApp'),
    ]
    PRIORITE_CHOICES = [
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    type_notification = models.CharField(max_length=15, choices=TYPE_CHOICES, default='systeme')
    titre = models.CharField(max_length=300)
    message = models.TextField()
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale')
    canal = models.CharField(max_length=15, choices=CANAL_CHOICES, default='interne')
    lue = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(null=True, blank=True)
    lien = models.CharField(max_length=500, blank=True)
    objet_type = models.CharField(max_length=50, blank=True)
    objet_id = models.IntegerField(null=True, blank=True)
    envoyee = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications_envoyees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type_notification}] {self.titre}"

    def marquer_lue(self):
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save(update_fields=['lue', 'date_lecture'])

    @classmethod
    def envoyer(cls, destinataire, type_notif, titre, message,
                canal='interne', priorite='normale', lien='',
                objet_type='', objet_id=None, cree_par=None):
        return cls.objects.create(
            destinataire=destinataire,
            type_notification=type_notif,
            titre=titre,
            message=message,
            canal=canal,
            priorite=priorite,
            lien=lien,
            objet_type=objet_type,
            objet_id=objet_id,
            cree_par=cree_par,
        )


class PreferenceNotification(models.Model):
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='preferences_notifications'
    )
    email_active = models.BooleanField(default=True)
    sms_active = models.BooleanField(default=False)
    push_active = models.BooleanField(default=True)
    whatsapp_active = models.BooleanField(default=False)
    types_actives = models.JSONField(default=list, blank=True)
    heure_debut_silence = models.TimeField(null=True, blank=True)
    heure_fin_silence = models.TimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Préférences notification'


# ─── Centre d'activités ───────────────────────────────────────────────────────

class ActiviteRecente(models.Model):
    TYPE_CHOICES = [
        ('document', 'Document modifié'),
        ('courrier', 'Courrier reçu'),
        ('livrable', 'Livrable validé'),
        ('tache', 'Tâche créée'),
        ('reunion', 'Réunion planifiée'),
        ('message', 'Message reçu'),
        ('budget', 'Budget modifié'),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activites_recentes'
    )
    type_activite = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    lien = models.CharField(max_length=500, blank=True)
    objet_type = models.CharField(max_length=50, blank=True)
    objet_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Activité récente'
        ordering = ['-created_at']


# ─── Groupes de travail ───────────────────────────────────────────────────────

class GroupeTravail(models.Model):
    TYPE_CHOICES = [
        ('equipe_projet', 'Équipe projet'),
        ('comite_technique', 'Comité technique'),
        ('comite_pilotage', 'Comité de pilotage'),
        ('direction', 'Direction'),
        ('finance', 'Finance'),
        ('autre', 'Autre'),
    ]

    nom = models.CharField(max_length=200)
    type_groupe = models.CharField(max_length=20, choices=TYPE_CHOICES, default='equipe_projet')
    description = models.TextField(blank=True)
    membres = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='groupes_travail', blank=True
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='groupes_travail'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='groupes_travail'
    )
    actif = models.BooleanField(default=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='groupes_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Groupe de travail'

    def __str__(self):
        return f"[{self.get_type_groupe_display()}] {self.nom}"


# ─── M43 : Gestion des événements ─────────────────────────────────────────────

class Evenement(models.Model):
    TYPE_CHOICES = [
        ('atelier', 'Atelier'), ('seminaire', 'Séminaire'),
        ('formation', 'Formation'), ('conference', 'Conférence'),
        ('forum', 'Forum'), ('mission', 'Mission terrain'),
        ('reunion', 'Réunion spéciale'), ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('planifie', 'Planifié'), ('ouvert_inscriptions', 'Ouvert aux inscriptions'),
        ('en_cours', 'En cours'), ('termine', 'Terminé'),
        ('annule', 'Annulé'), ('reporte', 'Reporté'),
    ]

    titre = models.CharField(max_length=300)
    type_evenement = models.CharField(max_length=15, choices=TYPE_CHOICES, default='atelier')
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default='planifie')
    description = models.TextField(blank=True)
    objectifs = models.TextField(blank=True)
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evenements'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evenements'
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    lieu = models.CharField(max_length=300, blank=True)
    adresse = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    nb_participants_attendus = models.IntegerField(null=True, blank=True)
    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ordre_du_jour = models.TextField(blank=True)
    compte_rendu = models.TextField(blank=True)
    fichier_programme = models.FileField(upload_to='evenements/programmes/%Y/', null=True, blank=True)
    fichier_compte_rendu = models.FileField(upload_to='evenements/cr/%Y/', null=True, blank=True)
    organisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='evenements_organises'
    )
    est_public = models.BooleanField(default=False)
    inscription_requise = models.BooleanField(default=True)
    date_limite_inscription = models.DateField(null=True, blank=True)
    lien_visio = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Événement'
        ordering = ['-date_debut']

    def __str__(self):
        return f"[{self.get_type_evenement_display()}] {self.titre} ({self.date_debut.date()})"

    @property
    def taux_budget(self):
        if not self.budget_prevu:
            return 0
        return round(float(self.budget_realise) / float(self.budget_prevu) * 100, 1)


class ParticipantEvenement(models.Model):
    STATUT_CHOICES = [
        ('inscrit', 'Inscrit'), ('confirme', 'Confirmé'),
        ('present', 'Présent'), ('absent', 'Absent'), ('annule', 'Annulé'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='participants')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='participations_evenements'
    )
    nom_externe = models.CharField(max_length=200, blank=True,
                                    help_text="Pour les participants externes (non-utilisateurs)")
    organisation = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='inscrit')
    heure_arrivee = models.DateTimeField(null=True, blank=True)
    heure_depart = models.DateTimeField(null=True, blank=True)
    code_badge = models.CharField(max_length=50, blank=True)
    qr_code_scan = models.BooleanField(default=False)
    note_evaluation = models.IntegerField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Participant événement'
        unique_together = ['evenement', 'utilisateur', 'email']

    def __str__(self):
        nom = self.utilisateur.get_full_name() if self.utilisateur else self.nom_externe
        return f"{nom} — {self.evenement.titre}"


class DepenseEvenement(models.Model):
    CATEGORIE_CHOICES = [
        ('hebergement', 'Hébergement'), ('restauration', 'Restauration'),
        ('transport', 'Transport'), ('location_salle', 'Location salle'),
        ('materiel', 'Matériel'), ('honoraires', 'Honoraires formateurs'),
        ('communication', 'Communication'), ('autre', 'Autre'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='depenses')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='autre')
    libelle = models.CharField(max_length=200)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    fournisseur = models.CharField(max_length=200, blank=True)
    facture = models.FileField(upload_to='evenements/depenses/%Y/', null=True, blank=True)
    saisi_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='depenses_evenements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dépense événement'
        ordering = ['categorie']

    def __str__(self):
        return f"{self.evenement.titre} — {self.libelle} : {self.montant}"
