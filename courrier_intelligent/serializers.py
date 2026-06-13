from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import CompteEmail, SignatureEmail, TemplateReponse, Email, PieceJointeEmail, ActionEmail, EtiquetteEmail, LienEmail, RegleClassification


class CompteEmailSerializer(serializers.ModelSerializer):
    smtp_config_detectee = serializers.SerializerMethodField(read_only=True)
    imap_config_detectee = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompteEmail
        fields = ['id', 'type_compte', 'nom_affichage', 'adresse_email',
                  'serveur_entrant', 'port_entrant', 'serveur_sortant', 'port_sortant',
                  'ssl_entrant', 'ssl_sortant', 'identifiant', 'mot_de_passe',
                  'statut', 'est_principal', 'derniere_synchro', 'created_at',
                  'smtp_config_detectee', 'imap_config_detectee']
        read_only_fields = ['id', 'derniere_synchro', 'created_at',
                            'smtp_config_detectee', 'imap_config_detectee']
        extra_kwargs = {
            'identifiant':   {'write_only': False},
            'mot_de_passe':  {'write_only': True},
        }

    def get_smtp_config_detectee(self, obj):
        from .services import detect_smtp_config
        return detect_smtp_config(obj.adresse_email)

    def get_imap_config_detectee(self, obj):
        from .services import detect_imap_config
        return detect_imap_config(obj.adresse_email)


class PieceJointeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceJointeEmail
        fields = ['id', 'email', 'nom_fichier', 'type_mime', 'taille', 'fichier',
                  'document_ged', 'created_at']
        read_only_fields = ['id', 'created_at']


class ActionEmailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = ActionEmail
        fields = ['id', 'email', 'type_action', 'description', 'responsable',
                  'responsable_detail', 'echeance', 'statut', 'detectee_par_ia',
                  'objet_genere_id', 'objet_genere_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class EtiquetteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtiquetteEmail
        fields = ['id', 'nom', 'couleur', 'utilisateur']
        read_only_fields = ['id']


class EmailListSerializer(serializers.ModelSerializer):
    nb_pj = serializers.SerializerMethodField()
    etiquettes = EtiquetteSerializer(many=True, read_only=True)
    pieces_jointes = PieceJointeSerializer(many=True, read_only=True)

    class Meta:
        model = Email
        fields = ['id', 'direction', 'sujet', 'expediteur', 'expediteur_email',
                  'date_envoi', 'date_reception', 'priorite', 'statut', 'est_lu',
                  'projet', 'programme', 'score_urgence', 'traite_par_ia',
                  'resume_ia', 'corps_texte', 'nb_pj', 'pieces_jointes',
                  'etiquettes', 'thread_id', 'en_reponse_a', 'created_at']

    def get_nb_pj(self, obj):
        return obj.pieces_jointes.count()


class EmailDetailSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    pieces_jointes = PieceJointeSerializer(many=True, read_only=True)
    action_emails = ActionEmailSerializer(many=True, read_only=True)
    etiquettes = EtiquetteSerializer(many=True, read_only=True)

    class Meta:
        model = Email
        fields = [
            'id', 'compte', 'direction', 'message_id', 'sujet', 'corps_html', 'corps_texte',
            'expediteur', 'expediteur_email', 'destinataires', 'destinataires_cc',
            'destinataires_cci', 'date_envoi', 'date_reception', 'date_envoi_differe',
            'priorite', 'statut', 'est_lu', 'lu_le', 'en_reponse_a', 'thread_id',
            'programme', 'projet', 'activite', 'reunion',
            'resume_ia', 'actions_detectees', 'echeances_detectees',
            'categorie_ia', 'score_urgence', 'risques_detectes', 'traite_par_ia',
            'archive_ged', 'document_ged',
            'cree_par', 'cree_par_detail', 'created_at', 'updated_at',
            'pieces_jointes', 'action_emails', 'etiquettes',
        ]
        read_only_fields = ['id', 'message_id', 'created_at', 'updated_at',
                            'resume_ia', 'actions_detectees', 'traite_par_ia']


class EmailCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ['id', 'compte', 'direction', 'sujet', 'corps_html', 'corps_texte',
                  'expediteur', 'expediteur_email', 'destinataires', 'destinataires_cc',
                  'destinataires_cci', 'priorite', 'date_envoi_differe', 'en_reponse_a',
                  'programme', 'projet', 'activite', 'reunion']
        read_only_fields = ['id']


class LienEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LienEmail
        fields = ['id', 'email', 'objet_type', 'objet_id', 'objet_libelle', 'note', 'cree_par', 'created_at']
        read_only_fields = ['id', 'cree_par', 'created_at']


class RegleClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegleClassification
        fields = ['id', 'nom', 'description', 'actif', 'priorite', 'operateur',
                  'conditions', 'action', 'parametres_action', 'nb_applications',
                  'cree_par', 'created_at', 'updated_at']
        read_only_fields = ['id', 'cree_par', 'nb_applications', 'created_at', 'updated_at']


class SignatureEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignatureEmail
        fields = [
            'id', 'utilisateur', 'compte', 'nom',
            'contenu_html', 'contenu_texte', 'est_principale',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'utilisateur', 'created_at', 'updated_at']


class TemplateReponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateReponse
        fields = [
            'id', 'titre', 'type_template', 'sujet_template',
            'corps_html', 'corps_texte', 'langue', 'variables',
            'est_global', 'cree_par', 'nb_utilisations', 'actif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'cree_par', 'nb_utilisations', 'created_at', 'updated_at']
