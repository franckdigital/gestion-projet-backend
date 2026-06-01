from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    FicheCapitalisation, EntreeBibliotheque, CommentaireFiche, CentreConnaissance,
)


# ─── FicheCapitalisation ─────────────────────────────────────────────────────

class FicheCapitalisationListSerializer(serializers.ModelSerializer):
    type_fiche_display = serializers.CharField(source='get_type_fiche_display', read_only=True)
    domaine_display = serializers.CharField(source='get_domaine_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    niveau_replicabilite_display = serializers.CharField(
        source='get_niveau_replicabilite_display', read_only=True)
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    nb_commentaires = serializers.SerializerMethodField()

    class Meta:
        model = FicheCapitalisation
        fields = [
            'id', 'reference', 'titre', 'type_fiche', 'type_fiche_display',
            'domaine', 'domaine_display', 'statut', 'statut_display',
            'programme', 'projet',
            'niveau_replicabilite', 'niveau_replicabilite_display',
            'auteur', 'auteur_detail',
            'genere_par_ia', 'nb_consultations', 'nb_favoris',
            'nb_commentaires', 'created_at',
        ]

    def get_nb_commentaires(self, obj):
        return obj.commentaires.count()


class FicheCapitalisationDetailSerializer(serializers.ModelSerializer):
    type_fiche_display = serializers.CharField(source='get_type_fiche_display', read_only=True)
    domaine_display = serializers.CharField(source='get_domaine_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    niveau_replicabilite_display = serializers.CharField(
        source='get_niveau_replicabilite_display', read_only=True)
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    contributeurs_detail = UserMinimalSerializer(source='contributeurs', many=True, read_only=True)
    nb_commentaires = serializers.SerializerMethodField()

    class Meta:
        model = FicheCapitalisation
        fields = [
            'id', 'reference', 'titre', 'type_fiche', 'type_fiche_display',
            'domaine', 'domaine_display', 'statut', 'statut_display',
            'programme', 'projet',
            'contexte', 'probleme_defi', 'solution_approche',
            'resultats_obtenus', 'lecon_principale', 'recommandation',
            'conditions_replicabilite', 'indicateurs_succes',
            'tags', 'mots_cles', 'niveau_replicabilite', 'niveau_replicabilite_display',
            'periode_reference', 'zone_geographique', 'public_cible',
            'auteur', 'auteur_detail',
            'contributeurs', 'contributeurs_detail',
            'valide_par', 'valide_par_detail', 'date_validation',
            'fichier_principal', 'document_ged',
            'genere_par_ia', 'nb_consultations', 'nb_favoris',
            'nb_commentaires', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at',
                            'nb_consultations', 'nb_favoris']

    def get_nb_commentaires(self, obj):
        return obj.commentaires.count()


class FicheCapitalisationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FicheCapitalisation
        fields = [
            'titre', 'type_fiche', 'domaine', 'statut',
            'programme', 'projet',
            'contexte', 'probleme_defi', 'solution_approche',
            'resultats_obtenus', 'lecon_principale', 'recommandation',
            'conditions_replicabilite', 'indicateurs_succes',
            'tags', 'mots_cles', 'niveau_replicabilite',
            'periode_reference', 'zone_geographique', 'public_cible',
            'contributeurs', 'fichier_principal', 'document_ged',
        ]


# ─── EntreeBibliotheque ───────────────────────────────────────────────────────

class EntreeBibliothequeListSerializer(serializers.ModelSerializer):
    categorie_display = serializers.CharField(source='get_categorie_display', read_only=True)
    domaine_display = serializers.CharField(source='get_domaine_display', read_only=True)
    ajoute_par_detail = UserMinimalSerializer(source='ajoute_par', read_only=True)

    class Meta:
        model = EntreeBibliotheque
        fields = [
            'id', 'titre', 'categorie', 'categorie_display', 'sous_categorie',
            'domaine', 'domaine_display', 'auteur', 'organisation',
            'annee_publication', 'langue', 'est_public',
            'programme', 'projet',
            'nb_telechargements',
            'ajoute_par', 'ajoute_par_detail', 'created_at',
        ]


class EntreeBibliothequeDetailSerializer(serializers.ModelSerializer):
    categorie_display = serializers.CharField(source='get_categorie_display', read_only=True)
    domaine_display = serializers.CharField(source='get_domaine_display', read_only=True)
    ajoute_par_detail = UserMinimalSerializer(source='ajoute_par', read_only=True)

    class Meta:
        model = EntreeBibliotheque
        fields = [
            'id', 'titre', 'categorie', 'categorie_display', 'sous_categorie',
            'domaine', 'domaine_display', 'description',
            'auteur', 'organisation', 'annee_publication', 'langue',
            'fichier', 'url_externe', 'mots_cles', 'tags',
            'est_public', 'programme', 'projet',
            'nb_telechargements',
            'ajoute_par', 'ajoute_par_detail', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'nb_telechargements', 'created_at', 'updated_at']


# ─── CommentaireFiche ─────────────────────────────────────────────────────────

class CommentaireFicheSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    reponses = serializers.SerializerMethodField()

    class Meta:
        model = CommentaireFiche
        fields = [
            'id', 'fiche', 'auteur', 'auteur_detail',
            'contenu', 'en_reponse_a', 'reponses', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_reponses(self, obj):
        # Sérialisation légère sans récursion infinie
        return [
            {
                'id': r.id,
                'auteur_id': r.auteur_id,
                'contenu': r.contenu,
                'created_at': r.created_at,
            }
            for r in obj.reponses.select_related('auteur').all()
        ]


# ─── CentreConnaissance ───────────────────────────────────────────────────────

class CentreConnaissanceListSerializer(serializers.ModelSerializer):
    domaine_display = serializers.CharField(source='get_domaine_display', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_fiches = serializers.SerializerMethodField()
    nb_entrees = serializers.SerializerMethodField()

    class Meta:
        model = CentreConnaissance
        fields = [
            'id', 'nom', 'domaine', 'domaine_display',
            'responsable', 'responsable_detail',
            'icone', 'couleur', 'actif',
            'nb_fiches', 'nb_entrees', 'created_at',
        ]

    def get_nb_fiches(self, obj):
        return obj.fiches.count()

    def get_nb_entrees(self, obj):
        return obj.entrees_bibliotheque.count()


class CentreConnaissanceDetailSerializer(serializers.ModelSerializer):
    domaine_display = serializers.CharField(source='get_domaine_display', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    fiches_detail = FicheCapitalisationListSerializer(source='fiches', many=True, read_only=True)
    entrees_detail = EntreeBibliothequeListSerializer(source='entrees_bibliotheque', many=True, read_only=True)

    class Meta:
        model = CentreConnaissance
        fields = [
            'id', 'nom', 'description', 'domaine', 'domaine_display',
            'responsable', 'responsable_detail',
            'fiches', 'fiches_detail',
            'entrees_bibliotheque', 'entrees_detail',
            'icone', 'couleur', 'actif', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
