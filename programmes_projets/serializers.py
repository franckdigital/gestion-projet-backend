from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from gouvernance.serializers import BailleurSerializer, PartenaireSerializer
from .models import (
    ZoneIntervention, Programme, ObjectifProgramme, PartenaireProgramme,
    DocumentProgramme, Projet, MembreEquipeProjet, RisqueProjet,
    LivrableProjet, JalonProjet,
)


class ZoneInterventionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneIntervention
        fields = ['id', 'nom', 'code', 'pays', 'region', 'description', 'actif']


class ObjectifProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectifProgramme
        fields = ['id', 'programme', 'type_objectif', 'code', 'libelle',
                  'description', 'indicateur_mesure', 'ordre', 'actif']


class PartenaireProgrammeSerializer(serializers.ModelSerializer):
    partenaire_detail = PartenaireSerializer(source='partenaire', read_only=True)

    class Meta:
        model = PartenaireProgramme
        fields = ['id', 'programme', 'partenaire', 'partenaire_detail', 'type_participation',
                  'montant_contribution', 'date_debut', 'date_fin', 'notes', 'actif']


class DocumentProgrammeSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserMinimalSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = DocumentProgramme
        fields = ['id', 'programme', 'titre', 'type_document', 'fichier', 'url_externe',
                  'date_document', 'version', 'description', 'statut',
                  'uploaded_by', 'uploaded_by_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProgrammeListSerializer(serializers.ModelSerializer):
    coordonnateur_nom = serializers.CharField(source='coordonnateur.nom_complet', read_only=True)
    bailleur_nom = serializers.CharField(source='bailleur.nom', read_only=True)
    organisation_nom = serializers.CharField(source='organisation.nom', read_only=True)
    nb_projets_actifs = serializers.SerializerMethodField()

    class Meta:
        model = Programme
        fields = ['id', 'code', 'intitule', 'acronyme', 'statut', 'organisation_nom',
                  'coordonnateur', 'coordonnateur_nom', 'bailleur', 'bailleur_nom',
                  'date_debut', 'date_fin', 'budget_total', 'devise',
                  'taux_avancement', 'nb_projets_actifs', 'created_at']

    def get_nb_projets_actifs(self, obj):
        return obj.projets.filter(statut='en_cours').count()


class ProgrammeDetailSerializer(serializers.ModelSerializer):
    coordonnateur_detail = UserMinimalSerializer(source='coordonnateur', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    objectifs = ObjectifProgrammeSerializer(many=True, read_only=True)
    participations = PartenaireProgrammeSerializer(many=True, read_only=True)
    documents = DocumentProgrammeSerializer(many=True, read_only=True)
    zones_intervention = ZoneInterventionSerializer(many=True, read_only=True)
    zones_intervention_ids = serializers.PrimaryKeyRelatedField(
        source='zones_intervention', many=True,
        queryset=ZoneIntervention.objects.all(), write_only=True, required=False
    )
    equipe_detail = UserMinimalSerializer(source='equipe', many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Programme
        fields = [
            'id', 'code', 'intitule', 'acronyme', 'description',
            'organisation', 'bailleur', 'zones_intervention', 'zones_intervention_ids',
            'coordonnateur', 'coordonnateur_detail', 'responsable', 'responsable_detail',
            'equipe', 'equipe_detail',
            'date_debut', 'date_fin', 'budget_total', 'devise',
            'statut', 'soumis_par', 'date_soumission', 'valide_par', 'valide_par_detail',
            'date_validation', 'date_cloture', 'motif_suspension',
            'contexte', 'impacts_attendus',
            'taux_avancement', 'nb_projets',
            'tags', 'notes', 'reference_externe',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'objectifs', 'participations', 'documents', 'stats', 'est_en_retard',
        ]
        read_only_fields = ['id', 'nb_projets', 'taux_avancement', 'created_at', 'updated_at']

    def get_stats(self, obj):
        projets = obj.projets.all()
        return {
            'total_projets': projets.count(),
            'projets_actifs': projets.filter(statut='en_cours').count(),
            'projets_termines': projets.filter(statut__in=['termine', 'cloture']).count(),
            'projets_suspendus': projets.filter(statut='suspendu').count(),
            'budget_total': float(obj.budget_total),
        }


class ProgrammeCreateSerializer(serializers.ModelSerializer):
    zones_intervention_ids = serializers.PrimaryKeyRelatedField(
        source='zones_intervention', many=True,
        queryset=ZoneIntervention.objects.all(), required=False
    )

    class Meta:
        model = Programme
        fields = [
            'code', 'intitule', 'acronyme', 'description',
            'organisation', 'bailleur', 'zones_intervention_ids',
            'coordonnateur', 'responsable',
            'date_debut', 'date_fin', 'budget_total', 'devise',
            'contexte', 'impacts_attendus', 'tags', 'notes', 'reference_externe',
        ]

    def create(self, validated_data):
        zones = validated_data.pop('zones_intervention', [])
        programme = Programme.objects.create(**validated_data)
        if zones:
            programme.zones_intervention.set(zones)
        return programme

    def update(self, instance, validated_data):
        zones = validated_data.pop('zones_intervention', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if zones is not None:
            instance.zones_intervention.set(zones)
        return instance


# ─── Projet ──────────────────────────────────────────────────────────────────

class MembreEquipeSerializer(serializers.ModelSerializer):
    user_detail = UserMinimalSerializer(source='user', read_only=True)

    class Meta:
        model = MembreEquipeProjet
        fields = ['id', 'projet', 'user', 'user_detail', 'role_projet',
                  'date_affectation', 'date_fin_affectation', 'taux_affectation',
                  'is_active', 'notes']


class RisqueSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable_suivi', read_only=True)

    class Meta:
        model = RisqueProjet
        fields = ['id', 'projet', 'titre', 'description', 'categorie',
                  'probabilite', 'impact', 'niveau_risque',
                  'mesures_mitigation', 'mesures_contingence',
                  'responsable_suivi', 'responsable_detail',
                  'statut', 'date_identification', 'date_resolution', 'notes']
        read_only_fields = ['id', 'niveau_risque', 'date_identification']


class LivrableSerializer(serializers.ModelSerializer):
    validateur_detail = UserMinimalSerializer(source='validateur', read_only=True)

    class Meta:
        model = LivrableProjet
        fields = ['id', 'projet', 'code', 'titre', 'description', 'type_livrable',
                  'date_prevue', 'date_livraison', 'statut',
                  'validateur', 'validateur_detail', 'date_validation',
                  'fichier', 'critere_acceptation', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class JalonProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = JalonProjet
        fields = ['id', 'projet', 'libelle', 'description',
                  'date_prevue', 'date_reelle', 'statut', 'notes']


class ProjetListSerializer(serializers.ModelSerializer):
    chef_projet_nom = serializers.CharField(source='chef_projet.nom_complet', read_only=True)
    programme_titre = serializers.CharField(source='programme.intitule', read_only=True)
    organisation_nom = serializers.CharField(source='organisation.nom', read_only=True)

    class Meta:
        model = Projet
        fields = ['id', 'code', 'titre', 'statut', 'priorite',
                  'programme', 'programme_titre', 'organisation_nom',
                  'chef_projet', 'chef_projet_nom',
                  'date_debut', 'date_fin_prevue', 'budget_initial', 'devise',
                  'taux_avancement', 'created_at']


class ProjetDetailSerializer(serializers.ModelSerializer):
    chef_projet_detail = UserMinimalSerializer(source='chef_projet', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    zones_intervention = ZoneInterventionSerializer(many=True, read_only=True)
    zones_intervention_ids = serializers.PrimaryKeyRelatedField(
        source='zones_intervention', many=True,
        queryset=ZoneIntervention.objects.all(), write_only=True, required=False
    )
    membres_equipe = MembreEquipeSerializer(many=True, read_only=True)
    risques = RisqueSerializer(many=True, read_only=True)
    livrables = LivrableSerializer(many=True, read_only=True)
    jalons = JalonProjetSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Projet
        fields = [
            'id', 'code', 'titre', 'description',
            'programme', 'organisation', 'zones_intervention', 'zones_intervention_ids',
            'chef_projet', 'chef_projet_detail',
            'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'budget_initial', 'budget_revise', 'devise',
            'statut', 'priorite',
            'valide_par', 'valide_par_detail', 'date_validation', 'date_cloture',
            'motif_suspension', 'taux_avancement',
            'tags', 'notes', 'reference_externe',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'membres_equipe', 'risques', 'livrables', 'jalons', 'stats', 'est_en_retard',
        ]
        read_only_fields = ['id', 'taux_avancement', 'created_at', 'updated_at']

    def get_stats(self, obj):
        livrables = obj.livrables.all()
        jalons = obj.jalons.all()
        risques = obj.risques.all()
        return {
            'nb_membres': obj.membres_equipe.filter(is_active=True).count(),
            'nb_livrables': livrables.count(),
            'livrables_valides': livrables.filter(statut='valide').count(),
            'nb_jalons': jalons.count(),
            'jalons_atteints': jalons.filter(statut='atteint').count(),
            'nb_risques': risques.count(),
            'risques_critiques': risques.filter(niveau_risque='critique').count(),
        }


class ProjetCreateSerializer(serializers.ModelSerializer):
    zones_intervention_ids = serializers.PrimaryKeyRelatedField(
        source='zones_intervention', many=True,
        queryset=ZoneIntervention.objects.all(), required=False
    )

    class Meta:
        model = Projet
        fields = [
            'code', 'titre', 'description',
            'programme', 'organisation', 'zones_intervention_ids',
            'chef_projet', 'date_debut', 'date_fin_prevue',
            'budget_initial', 'devise', 'priorite',
            'tags', 'notes', 'reference_externe',
        ]

    def create(self, validated_data):
        zones = validated_data.pop('zones_intervention', [])
        projet = Projet.objects.create(**validated_data)
        if zones:
            projet.zones_intervention.set(zones)
        return projet


# ─── Portefeuille ─────────────────────────────────────────────────────────────

class PortefeuilleSerializer(serializers.Serializer):
    total_programmes = serializers.IntegerField()
    programmes_actifs = serializers.IntegerField()
    total_projets = serializers.IntegerField()
    projets_actifs = serializers.IntegerField()
    projets_en_retard = serializers.IntegerField()
    projets_critiques = serializers.IntegerField()
    budget_total_programmes = serializers.DecimalField(max_digits=25, decimal_places=2)
    budget_total_projets = serializers.DecimalField(max_digits=25, decimal_places=2)
    taux_avancement_moyen = serializers.FloatField()
    par_statut = serializers.DictField()
    par_priorite = serializers.DictField()
    par_organisation = serializers.ListField()
