from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    Categorie, Document, VersionDocument, DossierDocument,
    WorkflowValidation, SignatureElectronique, LienPartage, AccesDocument,
    AuditDocument, CommentaireDocument,
    PlanConservation, BoiteArchive, DocumentArchive, DemandeDestruction,
    ModeleDocument, EntreesBibliotheque,
)


# ─── Plan de classement ───────────────────────────────────────────────────────

class CategorieSerializer(serializers.ModelSerializer):
    sous_categories = serializers.SerializerMethodField()
    nb_documents = serializers.SerializerMethodField()

    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'code', 'description', 'domaine', 'parent',
                  'icone', 'couleur', 'ordre', 'actif', 'duree_conservation_ans',
                  'sous_categories', 'nb_documents']

    def get_sous_categories(self, obj):
        return CategorieSerializer(
            obj.sous_categories.filter(actif=True).order_by('ordre'), many=True
        ).data

    def get_nb_documents(self, obj):
        return obj.documents.count()


class CategorieMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'code', 'domaine']


# ─── Document ─────────────────────────────────────────────────────────────────

class VersionDocumentSerializer(serializers.ModelSerializer):
    modifie_par_detail = UserMinimalSerializer(source='modifie_par', read_only=True)

    class Meta:
        model = VersionDocument
        fields = ['id', 'document', 'numero_version', 'fichier', 'commentaire',
                  'modifie_par', 'modifie_par_detail', 'taille_fichier',
                  'empreinte_sha256', 'date_version']
        read_only_fields = ['id', 'date_version']


class WorkflowValidationSerializer(serializers.ModelSerializer):
    validateur_detail = UserMinimalSerializer(source='validateur', read_only=True)

    class Meta:
        model = WorkflowValidation
        fields = ['id', 'document', 'ordre', 'validateur', 'validateur_detail',
                  'role_validateur', 'statut', 'commentaire', 'date_validation']
        read_only_fields = ['id', 'date_validation']


class SignatureSerializer(serializers.ModelSerializer):
    signataire_detail = UserMinimalSerializer(source='signataire', read_only=True)

    class Meta:
        model = SignatureElectronique
        fields = ['id', 'document', 'type_signature', 'signataire', 'signataire_detail',
                  'ordre', 'statut', 'date_signature', 'date_expiration',
                  'empreinte', 'commentaire', 'created_at']
        read_only_fields = ['id', 'empreinte', 'date_signature', 'created_at']


class CommentaireDocumentSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)

    class Meta:
        model = CommentaireDocument
        fields = ['id', 'document', 'auteur', 'auteur_detail', 'contenu',
                  'en_reponse_a', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LienPartageSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    est_valide = serializers.ReadOnlyField()
    est_expire = serializers.ReadOnlyField()

    class Meta:
        model = LienPartage
        fields = ['id', 'document', 'token', 'cree_par', 'cree_par_detail',
                  'email_destinataire', 'date_expiration',
                  'nb_telechargements_max', 'nb_telechargements',
                  'actif', 'est_valide', 'est_expire', 'created_at']
        read_only_fields = ['id', 'token', 'nb_telechargements', 'created_at']


class AccesDocumentSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = AccesDocument
        fields = ['id', 'document', 'utilisateur', 'utilisateur_detail',
                  'niveau', 'date_expiration', 'accorde_par', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuditDocumentSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = AuditDocument
        fields = ['id', 'document', 'action', 'utilisateur', 'utilisateur_detail',
                  'details', 'ip_address', 'created_at']
        read_only_fields = ['id', 'created_at']


class DocumentListSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    categorie_detail = CategorieMinimalSerializer(source='categorie', read_only=True)
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = ['id', 'reference', 'titre', 'type_document', 'statut',
                  'confidentialite', 'version', 'est_version_courante',
                  'categorie', 'categorie_detail',
                  'projet', 'programme',
                  'auteur', 'auteur_detail',
                  'type_fichier', 'taille_fichier',
                  'mots_cles', 'langue', 'ocr_effectue',
                  'date_expiration', 'est_en_retard',
                  'created_at', 'updated_at']


class DocumentDetailSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    categorie_detail = CategorieMinimalSerializer(source='categorie', read_only=True)
    historique_versions = VersionDocumentSerializer(many=True, read_only=True)
    workflow_validations = WorkflowValidationSerializer(many=True, read_only=True)
    signatures = SignatureSerializer(many=True, read_only=True)
    commentaires = CommentaireDocumentSerializer(many=True, read_only=True)
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = [
            'id', 'reference', 'titre', 'description', 'type_document', 'statut',
            'confidentialite', 'langue', 'version', 'est_version_courante',
            'categorie', 'categorie_detail',
            'programme', 'projet', 'activite',
            'fichier', 'type_fichier', 'taille_fichier', 'empreinte_sha256', 'url_externe',
            'mots_cles', 'mots_cles_auto', 'source', 'auteur_externe',
            'texte_ocr', 'ocr_effectue', 'date_ocr',
            'resume_auto', 'categorie_suggeree', 'score_doublon',
            'date_expiration', 'date_archivage', 'date_destruction_prevue', 'horodatage',
            'auteur', 'auteur_detail',
            'valide_par', 'valide_par_detail', 'date_validation',
            'notes', 'tags', 'created_at', 'updated_at',
            'historique_versions', 'workflow_validations', 'signatures', 'commentaires',
            'est_en_retard', 'document_parent',
        ]
        read_only_fields = ['id', 'reference', 'empreinte_sha256', 'created_at', 'updated_at',
                            'ocr_effectue', 'date_ocr', 'resume_auto', 'mots_cles_auto']


class DocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'titre', 'description', 'type_document', 'categorie',
            'programme', 'projet', 'activite',
            'fichier', 'url_externe',
            'confidentialite', 'langue', 'mots_cles', 'source', 'auteur_externe',
            'date_expiration', 'notes', 'tags',
        ]


# ─── Dossiers ─────────────────────────────────────────────────────────────────

class DossierDocumentSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_documents = serializers.SerializerMethodField()
    sous_dossiers_count = serializers.SerializerMethodField()

    class Meta:
        model = DossierDocument
        fields = ['id', 'nom', 'description', 'parent', 'programme', 'projet',
                  'responsable', 'responsable_detail', 'confidentiel', 'ordre', 'icone',
                  'created_by', 'created_at', 'nb_documents', 'sous_dossiers_count']
        read_only_fields = ['id', 'created_at']

    def get_nb_documents(self, obj):
        return obj.documents.count()

    def get_sous_dossiers_count(self, obj):
        return obj.sous_dossiers.count()


# ─── M25 : Archivage ─────────────────────────────────────────────────────────

class PlanConservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanConservation
        fields = ['id', 'categorie', 'duree_active_ans', 'duree_intermediaire_ans',
                  'duree_totale_ans', 'sort_final', 'base_legale', 'notes', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class DocumentArchiveSerializer(serializers.ModelSerializer):
    archive_par_detail = UserMinimalSerializer(source='archive_par', read_only=True)

    class Meta:
        model = DocumentArchive
        fields = ['id', 'boite', 'document', 'reference_archive', 'date_archivage',
                  'archive_par', 'archive_par_detail', 'horodatage_legal',
                  'empreinte_integrite', 'notes']
        read_only_fields = ['id', 'date_archivage', 'horodatage_legal']


class BoiteArchiveListSerializer(serializers.ModelSerializer):
    nb_documents = serializers.SerializerMethodField()

    class Meta:
        model = BoiteArchive
        fields = ['id', 'reference', 'intitule', 'categorie', 'statut',
                  'programme', 'projet', 'service_producteur',
                  'annee_debut', 'annee_fin', 'localisation',
                  'date_versement', 'date_destruction_prevue', 'chiffree',
                  'nb_documents', 'created_at']

    def get_nb_documents(self, obj):
        return obj.documents_archive.count()


class BoiteArchiveDetailSerializer(serializers.ModelSerializer):
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    documents_archive = DocumentArchiveSerializer(many=True, read_only=True)

    class Meta:
        model = BoiteArchive
        fields = [
            'id', 'reference', 'intitule', 'categorie', 'statut',
            'programme', 'projet', 'service_producteur',
            'annee_debut', 'annee_fin', 'localisation',
            'date_versement', 'date_destruction_prevue', 'chiffree', 'notes',
            'created_by', 'created_by_detail', 'created_at',
            'documents_archive',
        ]
        read_only_fields = ['id', 'reference', 'created_at']


class DemandeDestructionSerializer(serializers.ModelSerializer):
    propose_par_detail = UserMinimalSerializer(source='propose_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    autorise_par_detail = UserMinimalSerializer(source='autorise_par', read_only=True)

    class Meta:
        model = DemandeDestruction
        fields = ['id', 'boite', 'documents', 'motif', 'statut',
                  'propose_par', 'propose_par_detail',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'autorise_par', 'autorise_par_detail', 'date_autorisation',
                  'date_execution', 'pv_destruction', 'notes', 'created_at']
        read_only_fields = ['id', 'date_proposition', 'created_at']


# ─── Bibliothèque ─────────────────────────────────────────────────────────────

class ModeleDocumentSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = ModeleDocument
        fields = ['id', 'code', 'titre', 'type_modele', 'description',
                  'fichier', 'instructions', 'langue', 'version',
                  'actif', 'nb_utilisations',
                  'cree_par', 'cree_par_detail', 'created_at', 'updated_at']
        read_only_fields = ['id', 'code', 'nb_utilisations', 'created_at', 'updated_at']


class EntreeBibliothequeSerializer(serializers.ModelSerializer):
    ajoute_par_detail = UserMinimalSerializer(source='ajoute_par', read_only=True)

    class Meta:
        model = EntreesBibliotheque
        fields = ['id', 'titre', 'categorie', 'sous_categorie', 'description',
                  'fichier', 'url_externe', 'auteur', 'organisation',
                  'annee_publication', 'langue', 'mots_cles',
                  'est_public', 'nb_telechargements',
                  'ajoute_par', 'ajoute_par_detail', 'created_at']
        read_only_fields = ['id', 'nb_telechargements', 'created_at']
