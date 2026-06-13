from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    Budget, RevisionBudgetaire, LigneBudgetaire,
    BudgetProjet, LigneBudgetaireLegacy, DepenseLegacy,
    Fournisseur, Depense, Avance,
    Engagement, Convention, TrancheFinancement, Cofinancement,
    RapportBailleur, PlanTresorerie, LigneTresorerie, RapportFinancier,
    CompteBancaire, MouvementBancaire, RapprochementBancaire,
)


# ─── M21 : Budget ────────────────────────────────────────────────────────────

class RevisionBudgetaireSerializer(serializers.ModelSerializer):
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RevisionBudgetaire
        fields = ['id', 'budget', 'numero_revision', 'date_revision', 'motif',
                  'montant_avant', 'montant_apres', 'valide_par', 'valide_par_detail',
                  'fichier', 'created_at']
        read_only_fields = ['id', 'date_revision', 'created_at']


class LigneBudgetaireSerializer(serializers.ModelSerializer):
    solde_disponible = serializers.ReadOnlyField()
    taux_consommation = serializers.ReadOnlyField()
    est_depassee = serializers.ReadOnlyField()

    class Meta:
        model = LigneBudgetaire
        fields = ['id', 'budget', 'activite', 'composante', 'code', 'libelle',
                  'description', 'categorie', 'unite', 'quantite', 'cout_unitaire',
                  'montant_prevu', 'montant_engage', 'montant_depense', 'ordre', 'notes',
                  'solde_disponible', 'taux_consommation', 'est_depassee', 'created_at']
        read_only_fields = ['id', 'montant_engage', 'montant_depense', 'created_at']


class BudgetListSerializer(serializers.ModelSerializer):
    montant_actuel = serializers.ReadOnlyField()
    solde_disponible = serializers.ReadOnlyField()
    taux_execution = serializers.ReadOnlyField()
    taux_engagement = serializers.ReadOnlyField()
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'reference', 'type_budget', 'exercice', 'intitule',
                  'statut', 'devise', 'projet', 'programme',
                  'montant_initial', 'montant_revise', 'montant_engage', 'montant_depense',
                  'montant_actuel', 'solde_disponible', 'taux_execution', 'taux_engagement',
                  'created_by', 'created_by_detail', 'created_at']


class BudgetDetailSerializer(serializers.ModelSerializer):
    montant_actuel = serializers.ReadOnlyField()
    solde_disponible = serializers.ReadOnlyField()
    taux_execution = serializers.ReadOnlyField()
    taux_engagement = serializers.ReadOnlyField()
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    approuve_par_detail = UserMinimalSerializer(source='approuve_par', read_only=True)
    lignes = LigneBudgetaireSerializer(many=True, read_only=True)
    revisions = RevisionBudgetaireSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'reference', 'type_budget', 'exercice', 'intitule', 'statut',
            'devise', 'projet', 'programme',
            'montant_initial', 'montant_revise', 'montant_engage', 'montant_depense',
            'montant_actuel', 'solde_disponible', 'taux_execution', 'taux_engagement',
            'soumis_par', 'date_soumission', 'valide_finance_par', 'date_validation_finance',
            'approuve_par', 'approuve_par_detail', 'date_approbation', 'motif_rejet', 'notes',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'lignes', 'revisions', 'stats',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at',
                            'montant_engage', 'montant_depense']

    def get_stats(self, obj):
        lignes = obj.lignes.all()
        return {
            'nb_lignes': lignes.count(),
            'lignes_depassees': lignes.filter(montant_engage__gt=models.F('montant_prevu')).count()
            if hasattr(lignes, 'filter') else 0,
        }


# ─── M22 : Fournisseurs ───────────────────────────────────────────────────────

class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ['id', 'code', 'nom', 'type_fournisseur', 'numero_contribuable',
                  'adresse', 'pays', 'email', 'telephone', 'contact_principal',
                  'rib', 'banque', 'actif', 'notes', 'created_at']
        read_only_fields = ['id', 'code', 'created_at']


class FournisseurMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ['id', 'code', 'nom', 'type_fournisseur']


# ─── M22 : Dépenses ───────────────────────────────────────────────────────────

class DepenseListSerializer(serializers.ModelSerializer):
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True)
    saisi_par_detail = UserMinimalSerializer(source='saisi_par', read_only=True)

    class Meta:
        model = Depense
        fields = ['id', 'reference', 'libelle', 'type_depense', 'statut',
                  'montant', 'devise', 'date_depense', 'date_paiement', 'mode_paiement',
                  'projet', 'activite', 'fournisseur', 'fournisseur_nom',
                  'saisi_par', 'saisi_par_detail', 'created_at']


class DepenseDetailSerializer(serializers.ModelSerializer):
    fournisseur_detail = FournisseurMinimalSerializer(source='fournisseur', read_only=True)
    saisi_par_detail = UserMinimalSerializer(source='saisi_par', read_only=True)
    approuve_par_detail = UserMinimalSerializer(source='approuve_par', read_only=True)

    class Meta:
        model = Depense
        fields = [
            'id', 'reference', 'libelle', 'description', 'type_depense', 'statut',
            'montant', 'devise', 'taux_change', 'montant_base',
            'date_depense', 'date_paiement', 'mode_paiement', 'type_piece', 'numero_piece',
            'justificatif', 'ligne_budgetaire', 'projet', 'activite',
            'fournisseur', 'fournisseur_detail',
            'saisi_par', 'saisi_par_detail',
            'valide_responsable_par', 'valide_finance_par',
            'approuve_par', 'approuve_par_detail', 'date_approbation',
            'motif_rejet', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'montant_base', 'created_at', 'updated_at']


# ─── Avances ─────────────────────────────────────────────────────────────────

class AvanceSerializer(serializers.ModelSerializer):
    beneficiaire_detail = UserMinimalSerializer(source='beneficiaire', read_only=True)
    fournisseur_detail = FournisseurMinimalSerializer(source='fournisseur', read_only=True)
    accorde_par_detail = UserMinimalSerializer(source='accorde_par', read_only=True)
    solde_a_justifier = serializers.ReadOnlyField()

    class Meta:
        model = Avance
        fields = ['id', 'reference', 'type_avance', 'statut',
                  'beneficiaire', 'beneficiaire_detail',
                  'fournisseur', 'fournisseur_detail',
                  'projet', 'ligne_budgetaire',
                  'montant', 'devise', 'montant_justifie', 'montant_rembourse',
                  'solde_a_justifier', 'date_accord', 'date_limite_justification', 'motif',
                  'accorde_par', 'accorde_par_detail', 'notes', 'created_at']
        read_only_fields = ['id', 'reference', 'created_at']


# ─── Engagements ─────────────────────────────────────────────────────────────

class EngagementListSerializer(serializers.ModelSerializer):
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True)
    solde_engage = serializers.ReadOnlyField()

    class Meta:
        model = Engagement
        fields = ['id', 'reference', 'type_engagement', 'libelle', 'statut',
                  'montant', 'montant_liquide', 'solde_engage', 'devise',
                  'date_engagement', 'date_echeance',
                  'fournisseur', 'fournisseur_nom', 'created_at']


class EngagementDetailSerializer(serializers.ModelSerializer):
    fournisseur_detail = FournisseurMinimalSerializer(source='fournisseur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    approuve_par_detail = UserMinimalSerializer(source='approuve_par', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    solde_engage = serializers.ReadOnlyField()

    class Meta:
        model = Engagement
        fields = [
            'id', 'reference', 'type_engagement', 'libelle', 'description', 'statut',
            'ligne_budgetaire', 'fournisseur', 'fournisseur_detail',
            'montant', 'devise', 'montant_liquide', 'solde_engage',
            'date_engagement', 'date_echeance',
            'valide_par', 'valide_par_detail',
            'approuve_par', 'approuve_par_detail', 'date_approbation',
            'motif_annulation', 'fichier', 'notes',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'montant_liquide', 'created_at', 'updated_at']


# ─── M23 : Conventions ────────────────────────────────────────────────────────

class CofinancementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cofinancement
        fields = ['id', 'convention', 'bailleur', 'montant', 'devise',
                  'pourcentage', 'montant_recu', 'notes']


class TrancheFinancementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrancheFinancement
        fields = ['id', 'convention', 'numero', 'libelle', 'montant_prevu', 'montant_recu',
                  'date_prevue', 'date_reception', 'pourcentage', 'statut',
                  'conditions', 'notes', 'fichier', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConventionListSerializer(serializers.ModelSerializer):
    montant_restant = serializers.ReadOnlyField()
    taux_decaissement = serializers.ReadOnlyField()

    class Meta:
        model = Convention
        fields = ['id', 'reference', 'type_convention', 'intitule', 'statut',
                  'bailleur', 'projet', 'programme', 'devise',
                  'montant_total', 'montant_recu', 'montant_restant', 'taux_decaissement',
                  'date_debut', 'date_fin', 'date_signature', 'created_at']


class ConventionDetailSerializer(serializers.ModelSerializer):
    montant_restant = serializers.ReadOnlyField()
    taux_decaissement = serializers.ReadOnlyField()
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    tranches = TrancheFinancementSerializer(many=True, read_only=True)
    cofinancements = CofinancementSerializer(many=True, read_only=True)

    class Meta:
        model = Convention
        fields = [
            'id', 'reference', 'type_convention', 'intitule', 'statut',
            'bailleur', 'programme', 'projet',
            'date_signature', 'date_debut', 'date_fin',
            'montant_total', 'devise', 'montant_recu',
            'montant_restant', 'taux_decaissement',
            'responsable', 'responsable_detail',
            'conditions_particulieres', 'rapport_exige', 'frequence_rapport',
            'notes', 'fichier_convention',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'tranches', 'cofinancements',
        ]
        read_only_fields = ['id', 'reference', 'montant_recu', 'created_at', 'updated_at']


# ─── Rapport bailleur ─────────────────────────────────────────────────────────

class RapportBailleurSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RapportBailleur
        fields = ['id', 'convention', 'reference', 'type_rapport', 'titre',
                  'periode_debut', 'periode_fin',
                  'date_soumission_prevue', 'date_soumission_reelle',
                  'statut', 'contenu', 'montant_depense_periode', 'taux_execution',
                  'observations', 'redacteur', 'redacteur_detail',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'fichier', 'created_at']
        read_only_fields = ['id', 'reference', 'created_at']


# ─── Trésorerie ───────────────────────────────────────────────────────────────

class LigneTresorerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneTresorerie
        fields = ['id', 'plan', 'type_flux', 'categorie', 'libelle',
                  'mois', 'annee', 'montant_prevu', 'montant_realise', 'notes']


class PlanTresorerieSerializer(serializers.ModelSerializer):
    lignes = LigneTresorerieSerializer(many=True, read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    tableau = serializers.SerializerMethodField()

    class Meta:
        model = PlanTresorerie
        fields = ['id', 'projet', 'programme', 'exercice', 'periode', 'devise',
                  'notes', 'created_by', 'created_by_detail', 'created_at', 'updated_at',
                  'lignes', 'tableau']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tableau(self, obj):
        lignes = obj.lignes.all()
        mois_range = range(1, 13)
        tableau = []
        solde_cumule = 0
        for mois in mois_range:
            entrees = sum(
                float(l.montant_prevu) for l in lignes
                if l.mois == mois and l.type_flux == 'entrant'
            )
            sorties = sum(
                float(l.montant_prevu) for l in lignes
                if l.mois == mois and l.type_flux == 'sortant'
            )
            solde = entrees - sorties
            solde_cumule += solde
            tableau.append({'mois': mois, 'entrees': entrees, 'sorties': sorties,
                            'solde': solde, 'solde_cumule': solde_cumule})
        return tableau


# ─── Rapport financier ────────────────────────────────────────────────────────

class RapportFinancierSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RapportFinancier
        fields = ['id', 'reference', 'titre', 'type_rapport', 'periode',
                  'projet', 'programme',
                  'date_debut_periode', 'date_fin_periode', 'date_rapport',
                  'contenu', 'donnees_json',
                  'montant_budget', 'montant_depense', 'montant_engage', 'taux_execution',
                  'statut', 'redacteur', 'redacteur_detail',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'fichier', 'genere_par_ia', 'created_at', 'updated_at']
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']



# ─── Trésorerie avancée — Comptes bancaires ───────────────────────────────────

class CompteBancaireSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    solde_actuel = serializers.ReadOnlyField()

    class Meta:
        model = CompteBancaire
        fields = [
            'id', 'code', 'intitule', 'type_compte', 'banque',
            'numero_compte', 'rib', 'devise',
            'solde_initial', 'solde_actuel', 'date_ouverture', 'actif',
            'programme', 'projet',
            'responsable', 'responsable_detail',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'code', 'solde_actuel', 'created_at']


class MouvementBancaireSerializer(serializers.ModelSerializer):
    saisi_par_detail = UserMinimalSerializer(source='saisi_par', read_only=True)

    class Meta:
        model = MouvementBancaire
        fields = [
            'id', 'compte', 'date_operation', 'date_valeur',
            'type_mouvement', 'libelle', 'montant', 'solde_apres',
            'reference_externe', 'rapproche',
            'depense', 'convention',
            'notes', 'saisi_par', 'saisi_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class RapprochementBancaireSerializer(serializers.ModelSerializer):
    effectue_par_detail = UserMinimalSerializer(source='effectue_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RapprochementBancaire
        fields = [
            'id', 'compte',
            'periode_debut', 'periode_fin',
            'solde_releve', 'solde_comptable', 'ecart',
            'nb_mouvements_rapproches', 'nb_mouvements_non_rapproches',
            'statut', 'observations',
            'effectue_par', 'effectue_par_detail',
            'valide_par', 'valide_par_detail', 'date_validation',
            'created_at',
        ]
        read_only_fields = [
            'id', 'solde_comptable', 'ecart',
            'nb_mouvements_rapproches', 'nb_mouvements_non_rapproches',
            'created_at',
        ]


class LigneBudgetaireLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneBudgetaireLegacy
        fields = [
            'id', 'budget', 'code', 'libelle', 'categorie',
            'montant_prevu', 'montant_engage', 'montant_depense', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class BudgetProjetListSerializer(serializers.ModelSerializer):
    projet_titre = serializers.CharField(source='projet.titre', read_only=True)
    nb_lignes = serializers.SerializerMethodField()

    class Meta:
        model = BudgetProjet
        fields = [
            'id', 'projet', 'projet_titre', 'exercice',
            'montant_initial', 'montant_revise', 'statut',
            'date_approbation', 'nb_lignes', 'created_at',
        ]

    def get_nb_lignes(self, obj):
        return obj.lignes.count()


class BudgetProjetDetailSerializer(serializers.ModelSerializer):
    projet_titre = serializers.CharField(source='projet.titre', read_only=True)
    lignes = LigneBudgetaireLegacySerializer(many=True, read_only=True)
    approuve_par_detail = serializers.SerializerMethodField()

    class Meta:
        model = BudgetProjet
        fields = [
            'id', 'projet', 'projet_titre', 'exercice',
            'montant_initial', 'montant_revise', 'statut',
            'date_approbation', 'approuve_par', 'approuve_par_detail',
            'notes', 'lignes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_approuve_par_detail(self, obj):
        if not obj.approuve_par:
            return None
        return {'id': obj.approuve_par.id, 'email': obj.approuve_par.email}


class DepenseLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = DepenseLegacy
        fields = [
            'id', 'ligne', 'reference', 'libelle', 'montant',
            'date_depense', 'fournisseur', 'numero_facture', 'statut',
            'justificatif', 'saisi_par', 'approuve_par', 'date_approbation',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'reference', 'saisi_par', 'date_approbation', 'created_at']
