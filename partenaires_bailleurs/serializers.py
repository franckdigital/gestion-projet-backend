from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    Partenaire, ContactPartenaire, LiaisonProjetPartenaire,
    Convention, RenouvellementConvention,
    AccesPortailPartenaire, DepotDocumentPortail,
)


# ─── Partenaire ───────────────────────────────────────────────────────────────

class ContactPartenaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPartenaire
        fields = [
            'id', 'partenaire', 'nom', 'prenom', 'role', 'email',
            'telephone', 'est_principal',
        ]
        read_only_fields = ['id']


class ContactPartenaireInlineSerializer(serializers.ModelSerializer):
    """Serializer allégé pour imbrication dans Partenaire."""
    class Meta:
        model = ContactPartenaire
        fields = ['id', 'nom', 'prenom', 'role', 'email', 'telephone', 'est_principal']
        read_only_fields = ['id']


class PartenaireListSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    nb_conventions = serializers.SerializerMethodField()
    nb_contacts = serializers.SerializerMethodField()

    class Meta:
        model = Partenaire
        fields = [
            'id', 'nom', 'sigle', 'type_partenaire', 'statut',
            'pays', 'ville', 'email', 'telephone', 'site_web', 'logo',
            'contact_principal', 'email_contact', 'telephone_contact',
            'secteurs_intervention',
            'cree_par', 'cree_par_detail',
            'nb_conventions', 'nb_contacts',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_conventions(self, obj):
        return obj.conventions.count()

    def get_nb_contacts(self, obj):
        return obj.contacts.count()


class PartenaireDetailSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    contacts = ContactPartenaireInlineSerializer(many=True, read_only=True)
    nb_conventions = serializers.SerializerMethodField()
    nb_projets = serializers.SerializerMethodField()

    class Meta:
        model = Partenaire
        fields = [
            'id', 'nom', 'sigle', 'type_partenaire', 'statut',
            'pays', 'ville', 'adresse', 'site_web', 'email', 'telephone',
            'contact_principal', 'email_contact', 'telephone_contact',
            'secteurs_intervention', 'description', 'logo',
            'latitude', 'longitude', 'notes',
            'cree_par', 'cree_par_detail',
            'contacts', 'nb_conventions', 'nb_projets',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_conventions(self, obj):
        return obj.conventions.count()

    def get_nb_projets(self, obj):
        return obj.liaisons_projet.values('projet').distinct().count()


class PartenaireCartographieSerializer(serializers.ModelSerializer):
    """Serializer léger pour affichage SIG/cartographie."""
    nb_conventions = serializers.SerializerMethodField()

    class Meta:
        model = Partenaire
        fields = [
            'id', 'nom', 'sigle', 'type_partenaire', 'statut',
            'pays', 'ville', 'latitude', 'longitude',
            'email', 'telephone', 'nb_conventions',
        ]

    def get_nb_conventions(self, obj):
        return obj.conventions.count()


# ─── Liaison Projet-Partenaire ────────────────────────────────────────────────

class LiaisonProjetPartenaireSerializer(serializers.ModelSerializer):
    partenaire_nom = serializers.CharField(source='partenaire.nom', read_only=True)
    projet_titre = serializers.CharField(source='projet.titre', read_only=True)

    class Meta:
        model = LiaisonProjetPartenaire
        fields = [
            'id', 'partenaire', 'partenaire_nom',
            'projet', 'projet_titre',
            'role', 'montant_finance', 'date_debut', 'date_fin', 'notes',
        ]
        read_only_fields = ['id']


# ─── Convention ───────────────────────────────────────────────────────────────

class RenouvellementConventionSerializer(serializers.ModelSerializer):
    effectue_par_detail = UserMinimalSerializer(source='effectue_par', read_only=True)

    class Meta:
        model = RenouvellementConvention
        fields = [
            'id', 'convention', 'nouvelle_date_fin', 'nouveau_montant',
            'motif', 'date_signature', 'fichier',
            'effectue_par', 'effectue_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ConventionListSerializer(serializers.ModelSerializer):
    partenaire_nom = serializers.CharField(source='partenaire.nom', read_only=True)
    partenaire_sigle = serializers.CharField(source='partenaire.sigle', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    est_expiree = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()

    class Meta:
        model = Convention
        fields = [
            'id', 'reference', 'intitule', 'type_convention', 'statut',
            'partenaire', 'partenaire_nom', 'partenaire_sigle',
            'montant', 'devise',
            'date_signature', 'date_debut', 'date_fin',
            'responsable', 'responsable_detail',
            'est_expiree', 'jours_avant_expiration',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']


class ConventionDetailSerializer(serializers.ModelSerializer):
    partenaire_detail = PartenaireListSerializer(source='partenaire', read_only=True)
    signataire_interne_detail = UserMinimalSerializer(source='signataire_interne', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    renouvellements = RenouvellementConventionSerializer(many=True, read_only=True)
    est_expiree = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()
    programme_titre = serializers.CharField(source='programme.titre', read_only=True, default=None)
    projet_titre = serializers.CharField(source='projet.titre', read_only=True, default=None)

    class Meta:
        model = Convention
        fields = [
            'id', 'reference', 'intitule', 'type_convention', 'statut',
            'partenaire', 'partenaire_detail',
            'programme', 'programme_titre',
            'projet', 'projet_titre',
            'objet', 'montant', 'devise',
            'date_signature', 'date_debut', 'date_fin', 'date_expiration_alerte',
            'signataire_interne', 'signataire_interne_detail', 'signataire_externe',
            'clauses_principales', 'obligations_parties', 'conditions_renouvellement',
            'fichier', 'document_ged',
            'responsable', 'responsable_detail',
            'notes', 'renouvellements',
            'est_expiree', 'jours_avant_expiration',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']


class ConventionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convention
        fields = [
            'intitule', 'type_convention', 'statut',
            'partenaire', 'programme', 'projet',
            'objet', 'montant', 'devise',
            'date_signature', 'date_debut', 'date_fin', 'date_expiration_alerte',
            'signataire_interne', 'signataire_externe',
            'clauses_principales', 'obligations_parties', 'conditions_renouvellement',
            'fichier', 'document_ged', 'responsable', 'notes',
        ]


class RenouvellementCreateSerializer(serializers.Serializer):
    nouvelle_date_fin = serializers.DateField()
    nouveau_montant = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, allow_null=True)
    motif = serializers.CharField(required=False, allow_blank=True)
    date_signature = serializers.DateField(required=False, allow_null=True)
    fichier = serializers.FileField(required=False, allow_null=True)


# ─── Portail partenaire ───────────────────────────────────────────────────────

class AccesPortailPartenaireSerializer(serializers.ModelSerializer):
    partenaire_nom = serializers.CharField(source='partenaire.nom', read_only=True)
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)
    accorde_par_detail = UserMinimalSerializer(source='accorde_par', read_only=True)

    class Meta:
        model = AccesPortailPartenaire
        fields = [
            'id', 'partenaire', 'partenaire_nom',
            'utilisateur', 'utilisateur_detail',
            'niveau_acces', 'statut',
            'projets_accessibles', 'programmes_accessibles',
            'date_debut', 'date_fin',
            'accorde_par', 'accorde_par_detail',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DepotDocumentPortailSerializer(serializers.ModelSerializer):
    partenaire_nom = serializers.CharField(source='partenaire.nom', read_only=True)
    projet_titre = serializers.CharField(source='projet.titre', read_only=True, default=None)
    depose_par_detail = UserMinimalSerializer(source='depose_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = DepotDocumentPortail
        fields = [
            'id', 'partenaire', 'partenaire_nom',
            'projet', 'projet_titre',
            'titre', 'description', 'fichier', 'type_document', 'statut',
            'depose_par', 'depose_par_detail',
            'valide_par', 'valide_par_detail',
            'date_validation', 'motif_rejet',
            'created_at',
        ]
        read_only_fields = ['id', 'statut', 'valide_par', 'date_validation', 'motif_rejet', 'created_at']


class DepotRejeterSerializer(serializers.Serializer):
    motif_rejet = serializers.CharField()
