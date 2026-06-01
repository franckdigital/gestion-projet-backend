from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    ActiviteExecution, AffectationRessource, DependanceActivite, RapportActivite,
    Tache, ChecklistItem, DependanceTache, CommentaireTache, HistoriqueTache,
    Livrable, VersionLivrable, ValidationLivrable, CommentaireLivrable,
    Reunion, ParticipantReunion, PointOrdreJour, CompteRendu,
    DecisionReunion, ActionReunion,
    Mission, MembreMission, OrdreMission, RapportMission, RapportAvancement,
)


# ─── M13 : Activités ─────────────────────────────────────────────────────────

class AffectationRessourceSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = AffectationRessource
        fields = ['id', 'activite', 'type_ressource', 'utilisateur', 'utilisateur_detail',
                  'nom_ressource', 'taux_affectation', 'date_debut', 'date_fin', 'notes']


class DependanceActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DependanceActivite
        fields = ['id', 'activite_source', 'activite_cible', 'type_dependance', 'decalage_jours', 'notes']


class RapportActiviteSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)

    class Meta:
        model = RapportActivite
        fields = ['id', 'activite', 'periode', 'date_rapport', 'taux_realisation',
                  'observations', 'problemes', 'recommandations', 'prochaines_etapes',
                  'redacteur', 'redacteur_detail', 'statut', 'fichier', 'created_at']
        read_only_fields = ['id', 'created_at']


class ActiviteExecutionListSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source='responsable.nom_complet', read_only=True)
    projet_titre = serializers.CharField(source='projet.titre', read_only=True)
    est_en_retard = serializers.ReadOnlyField()
    nb_taches = serializers.SerializerMethodField()

    class Meta:
        model = ActiviteExecution
        fields = ['id', 'code', 'intitule', 'statut', 'priorite',
                  'projet', 'projet_titre', 'responsable', 'responsable_nom',
                  'date_debut_prevue', 'date_fin_prevue', 'taux_avancement',
                  'budget_prevu', 'est_en_retard', 'nb_taches', 'ordre', 'created_at']

    def get_nb_taches(self, obj):
        return obj.taches.count()


class ActiviteExecutionDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    affectations = AffectationRessourceSerializer(many=True, read_only=True)
    dependances_sortantes = DependanceActiviteSerializer(many=True, read_only=True)
    sous_activites = serializers.SerializerMethodField()
    est_en_retard = serializers.ReadOnlyField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = ActiviteExecution
        fields = [
            'id', 'code', 'intitule', 'description', 'priorite', 'statut',
            'projet', 'programme', 'activite_pa', 'plan_travail_activite', 'parent',
            'responsable', 'responsable_detail',
            'date_debut_prevue', 'date_fin_prevue', 'date_debut_reelle', 'date_fin_reelle',
            'budget_prevu', 'budget_realise', 'taux_avancement', 'ordre',
            'valide_par', 'valide_par_detail', 'date_validation', 'motif_suspension',
            'tags', 'notes', 'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'affectations', 'dependances_sortantes', 'sous_activites', 'est_en_retard', 'stats',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sous_activites(self, obj):
        return ActiviteExecutionListSerializer(
            obj.sous_activites.all().order_by('ordre'), many=True
        ).data

    def get_stats(self, obj):
        taches = obj.taches.all()
        return {
            'nb_taches': taches.count(),
            'taches_terminees': taches.filter(statut='terminee').count(),
            'taches_en_retard': sum(1 for t in taches if t.est_en_retard),
            'nb_livrables': obj.livrables.count(),
        }


class ActiviteExecutionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiviteExecution
        fields = [
            'code', 'intitule', 'description', 'priorite',
            'projet', 'programme', 'activite_pa', 'plan_travail_activite', 'parent',
            'responsable', 'date_debut_prevue', 'date_fin_prevue',
            'budget_prevu', 'ordre', 'tags', 'notes',
        ]


# ─── M14 : Tâches ─────────────────────────────────────────────────────────────

class ChecklistItemSerializer(serializers.ModelSerializer):
    complete_par_detail = UserMinimalSerializer(source='complete_par', read_only=True)

    class Meta:
        model = ChecklistItem
        fields = ['id', 'tache', 'libelle', 'complete', 'ordre',
                  'complete_par', 'complete_par_detail', 'date_completion']


class DependanceTacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = DependanceTache
        fields = ['id', 'tache_source', 'tache_cible', 'type_dependance']


class CommentaireTacheSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)

    class Meta:
        model = CommentaireTache
        fields = ['id', 'tache', 'auteur', 'auteur_detail', 'contenu', 'fichier', 'created_at']
        read_only_fields = ['id', 'created_at']


class HistoriqueTacheSerializer(serializers.ModelSerializer):
    user_detail = UserMinimalSerializer(source='user', read_only=True)

    class Meta:
        model = HistoriqueTache
        fields = ['id', 'tache', 'user', 'user_detail', 'action',
                  'ancien_statut', 'nouveau_statut', 'details', 'created_at']


class TacheListSerializer(serializers.ModelSerializer):
    assignee_detail = UserMinimalSerializer(source='assignee', read_only=True)
    est_en_retard = serializers.ReadOnlyField()
    progression_checklist = serializers.ReadOnlyField()
    activite_titre = serializers.CharField(source='activite.intitule', read_only=True)

    class Meta:
        model = Tache
        fields = ['id', 'code', 'titre', 'statut', 'priorite',
                  'activite', 'activite_titre', 'assignee', 'assignee_detail',
                  'date_debut', 'date_echeance', 'taux_avancement',
                  'estimation_heures', 'heures_realisees',
                  'est_en_retard', 'progression_checklist', 'ordre', 'created_at']


class TacheDetailSerializer(serializers.ModelSerializer):
    assignee_detail = UserMinimalSerializer(source='assignee', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    checklist = ChecklistItemSerializer(many=True, read_only=True)
    sous_taches = serializers.SerializerMethodField()
    commentaires = CommentaireTacheSerializer(many=True, read_only=True)
    historique = HistoriqueTacheSerializer(many=True, read_only=True)
    est_en_retard = serializers.ReadOnlyField()
    progression_checklist = serializers.ReadOnlyField()

    class Meta:
        model = Tache
        fields = [
            'id', 'code', 'titre', 'description', 'statut', 'priorite',
            'activite', 'parent',
            'assignee', 'assignee_detail',
            'date_debut', 'date_echeance', 'date_completion',
            'estimation_heures', 'heures_realisees', 'taux_avancement',
            'tags', 'notes', 'ordre',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'checklist', 'sous_taches', 'commentaires', 'historique',
            'est_en_retard', 'progression_checklist',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sous_taches(self, obj):
        return TacheListSerializer(
            obj.sous_taches.all().order_by('ordre'), many=True
        ).data


# ─── M15 : Livrables ──────────────────────────────────────────────────────────

class VersionLivrableSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserMinimalSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = VersionLivrable
        fields = ['id', 'livrable', 'numero_version', 'fichier', 'url_externe',
                  'description_changements', 'uploaded_by', 'uploaded_by_detail',
                  'date_upload', 'est_courante', 'taille_fichier']
        read_only_fields = ['id', 'date_upload']


class ValidationLivrableSerializer(serializers.ModelSerializer):
    validateur_detail = UserMinimalSerializer(source='validateur', read_only=True)

    class Meta:
        model = ValidationLivrable
        fields = ['id', 'livrable', 'etape', 'validateur', 'validateur_detail',
                  'statut', 'commentaire', 'date_validation', 'ordre']


class CommentaireLivrableSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)

    class Meta:
        model = CommentaireLivrable
        fields = ['id', 'livrable', 'auteur', 'auteur_detail', 'contenu', 'fichier', 'created_at']


class LivrableListSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source='responsable.nom_complet', read_only=True)
    projet_titre = serializers.CharField(source='projet.titre', read_only=True)
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Livrable
        fields = ['id', 'code', 'titre', 'type_livrable', 'statut',
                  'projet', 'projet_titre', 'activite',
                  'responsable', 'responsable_nom',
                  'date_prevue', 'date_livraison', 'version_courante',
                  'est_en_retard', 'created_at']


class LivrableDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    versions = VersionLivrableSerializer(many=True, read_only=True)
    validations = ValidationLivrableSerializer(many=True, read_only=True)
    commentaires = CommentaireLivrableSerializer(many=True, read_only=True)
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Livrable
        fields = [
            'id', 'code', 'titre', 'description', 'type_livrable', 'statut',
            'projet', 'activite',
            'responsable', 'responsable_detail',
            'date_prevue', 'date_livraison', 'version_courante',
            'critere_acceptation', 'notes',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'versions', 'validations', 'commentaires', 'est_en_retard',
        ]
        read_only_fields = ['id', 'version_courante', 'created_at', 'updated_at']


# ─── M16 : Réunions ───────────────────────────────────────────────────────────

class ParticipantReunionSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = ParticipantReunion
        fields = ['id', 'reunion', 'utilisateur', 'utilisateur_detail',
                  'nom_externe', 'email_externe', 'fonction_externe', 'organisation_externe',
                  'type_participant', 'statut_presence', 'date_invitation', 'date_confirmation',
                  'role_reunion']


class PointOrdreJourSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = PointOrdreJour
        fields = ['id', 'reunion', 'ordre', 'intitule', 'description',
                  'responsable', 'responsable_detail', 'duree_prevue', 'notes']


class DecisionReunionSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = DecisionReunion
        fields = ['id', 'compte_rendu', 'intitule', 'description',
                  'responsable', 'responsable_detail', 'echeance', 'statut', 'notes']


class ActionReunionSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = ActionReunion
        fields = ['id', 'compte_rendu', 'decision', 'libelle', 'description',
                  'responsable', 'responsable_detail', 'echeance', 'statut', 'tache_generee']


class CompteRenduSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    decisions = DecisionReunionSerializer(many=True, read_only=True)
    actions = ActionReunionSerializer(many=True, read_only=True)

    class Meta:
        model = CompteRendu
        fields = ['id', 'reunion', 'redacteur', 'redacteur_detail',
                  'participants_presents', 'synthese', 'discussions',
                  'decisions_prises', 'points_divers', 'prochaine_reunion',
                  'statut', 'valide_par', 'valide_par_detail', 'date_validation',
                  'fichier_final', 'genere_par_ia',
                  'created_at', 'updated_at', 'decisions', 'actions']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReunionListSerializer(serializers.ModelSerializer):
    organisateur_nom = serializers.CharField(source='organisateur.nom_complet', read_only=True)
    nb_participants = serializers.SerializerMethodField()
    a_compte_rendu = serializers.SerializerMethodField()

    class Meta:
        model = Reunion
        fields = ['id', 'reference', 'type_reunion', 'objet', 'statut',
                  'projet', 'programme', 'organisateur', 'organisateur_nom',
                  'date', 'heure_debut', 'heure_fin', 'lieu', 'plateforme',
                  'nb_participants', 'a_compte_rendu', 'created_at']

    def get_nb_participants(self, obj):
        return obj.participants.count()

    def get_a_compte_rendu(self, obj):
        return hasattr(obj, 'compte_rendu')


class ReunionDetailSerializer(serializers.ModelSerializer):
    organisateur_detail = UserMinimalSerializer(source='organisateur', read_only=True)
    participants = ParticipantReunionSerializer(many=True, read_only=True)
    points_ordre_jour = PointOrdreJourSerializer(many=True, read_only=True)
    compte_rendu_data = serializers.SerializerMethodField()

    class Meta:
        model = Reunion
        fields = [
            'id', 'reference', 'type_reunion', 'objet', 'description', 'statut',
            'projet', 'programme',
            'organisateur', 'organisateur_detail',
            'date', 'heure_debut', 'heure_fin', 'lieu',
            'plateforme', 'lien_visio', 'id_reunion_virtuelle',
            'rappel_envoye', 'rappel_24h', 'notes',
            'created_by', 'created_at', 'updated_at',
            'participants', 'points_ordre_jour', 'compte_rendu_data',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_compte_rendu_data(self, obj):
        try:
            return CompteRenduSerializer(obj.compte_rendu).data
        except CompteRendu.DoesNotExist:
            return None


# ─── M16 : Missions ───────────────────────────────────────────────────────────

class MembreMissionSerializer(serializers.ModelSerializer):
    user_detail = UserMinimalSerializer(source='user', read_only=True)
    total_frais = serializers.ReadOnlyField()

    class Meta:
        model = MembreMission
        fields = ['id', 'mission', 'user', 'user_detail', 'role_mission',
                  'indemnite_journaliere', 'frais_transport', 'frais_hebergement',
                  'autres_frais', 'total_frais', 'notes']


class OrdreMissionSerializer(serializers.ModelSerializer):
    signataire_detail = UserMinimalSerializer(source='signataire', read_only=True)

    class Meta:
        model = OrdreMission
        fields = ['id', 'mission', 'numero', 'date_emission', 'signataire',
                  'signataire_detail', 'contenu', 'statut', 'fichier', 'created_at']
        read_only_fields = ['id', 'numero', 'date_emission', 'created_at']


class RapportMissionSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RapportMission
        fields = ['id', 'mission', 'redacteur', 'redacteur_detail',
                  'resume', 'objectifs_atteints', 'observations', 'recommandations',
                  'suite_a_donner', 'fichier', 'statut', 'date_soumission',
                  'valide_par', 'valide_par_detail', 'date_validation', 'created_at']
        read_only_fields = ['id', 'created_at']


class MissionListSerializer(serializers.ModelSerializer):
    demandeur_nom = serializers.CharField(source='demandeur.nom_complet', read_only=True)
    duree_jours = serializers.ReadOnlyField()

    class Meta:
        model = Mission
        fields = ['id', 'reference', 'objet', 'type_mission', 'statut',
                  'projet', 'programme', 'demandeur', 'demandeur_nom',
                  'destination', 'date_debut', 'date_fin', 'duree_jours',
                  'budget_prevu', 'created_at']


class MissionDetailSerializer(serializers.ModelSerializer):
    demandeur_detail = UserMinimalSerializer(source='demandeur', read_only=True)
    approuve_par_detail = UserMinimalSerializer(source='approuve_par', read_only=True)
    membres = MembreMissionSerializer(many=True, read_only=True)
    ordre_mission_data = serializers.SerializerMethodField()
    rapport_data = serializers.SerializerMethodField()
    duree_jours = serializers.ReadOnlyField()

    class Meta:
        model = Mission
        fields = [
            'id', 'reference', 'objet', 'type_mission', 'description', 'statut',
            'projet', 'programme',
            'lieu_depart', 'destination', 'pays_destination',
            'date_debut', 'date_fin', 'duree_jours',
            'budget_prevu', 'budget_realise',
            'demandeur', 'demandeur_detail',
            'approuve_par', 'approuve_par_detail', 'date_approbation',
            'objectifs', 'resultats_attendus', 'notes',
            'created_at', 'updated_at',
            'membres', 'ordre_mission_data', 'rapport_data',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_ordre_mission_data(self, obj):
        try:
            return OrdreMissionSerializer(obj.ordre_mission).data
        except OrdreMission.DoesNotExist:
            return None

    def get_rapport_data(self, obj):
        try:
            return RapportMissionSerializer(obj.rapport).data
        except RapportMission.DoesNotExist:
            return None


# ─── Rapport d'avancement ─────────────────────────────────────────────────────

class RapportAvancementSerializer(serializers.ModelSerializer):
    redacteur_detail  = UserMinimalSerializer(source='redacteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    objet_libelle     = serializers.SerializerMethodField()

    class Meta:
        model = RapportAvancement
        fields = [
            'id', 'type_objet', 'titre',
            'projet', 'activite', 'tache', 'reunion', 'mission',
            'periode', 'date_rapport', 'taux_realisation',
            'observations', 'problemes', 'recommandations', 'prochaines_etapes',
            'redacteur', 'redacteur_detail', 'statut',
            'valide_par', 'valide_par_detail', 'date_validation',
            'fichier', 'created_at', 'objet_libelle',
        ]
        read_only_fields = ['id', 'created_at']

    def get_objet_libelle(self, obj):
        if obj.type_objet == 'tache'   and obj.tache:   return obj.tache.titre
        if obj.type_objet == 'reunion' and obj.reunion:  return obj.reunion.objet
        if obj.type_objet == 'mission' and obj.mission:  return obj.mission.objet
        if obj.type_objet == 'projet'  and obj.projet:   return obj.projet.titre
        return obj.titre or '—'
