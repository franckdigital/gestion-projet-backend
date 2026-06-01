"""
Seed données de démonstration pour le Lot 6 — GED & Archivage :
  M24 : Catégories, Documents, Dossiers, Workflow, Signatures
  M25 : Boîtes d'archives, Plan de conservation
  Bibliothèque, Modèles de documents

Usage : python manage.py seed_lot6 [--reset]
"""
import os
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- Catégories ----------------------------------------------------------------

CATEGORIES = [
    { 'nom': 'Documents projets', 'code': 'CAT-PROJ', 'domaine': 'projet', 'couleur': '#3b82f6', 'conservation': None },
    { 'nom': 'Termes de référence', 'code': 'CAT-TDR', 'domaine': 'projet', 'parent': 'CAT-PROJ', 'couleur': '#60a5fa', 'conservation': 10 },
    { 'nom': 'Rapports de mission', 'code': 'CAT-RPT', 'domaine': 'projet', 'parent': 'CAT-PROJ', 'couleur': '#93c5fd', 'conservation': 10 },
    { 'nom': 'Documents financiers', 'code': 'CAT-FIN', 'domaine': 'financier', 'couleur': '#10b981', 'conservation': None },
    { 'nom': 'Factures et contrats', 'code': 'CAT-FAC', 'domaine': 'financier', 'parent': 'CAT-FIN', 'couleur': '#34d399', 'conservation': 10 },
    { 'nom': 'Budgets', 'code': 'CAT-BUD', 'domaine': 'financier', 'parent': 'CAT-FIN', 'couleur': '#6ee7b7', 'conservation': 10 },
    { 'nom': 'Documents administratifs', 'code': 'CAT-ADM', 'domaine': 'administratif', 'couleur': '#f59e0b', 'conservation': None },
    { 'nom': 'Courriers officiels', 'code': 'CAT-COR', 'domaine': 'administratif', 'parent': 'CAT-ADM', 'couleur': '#fbbf24', 'conservation': 5 },
    { 'nom': 'Procès-verbaux', 'code': 'CAT-PV', 'domaine': 'administratif', 'parent': 'CAT-ADM', 'couleur': '#fcd34d', 'conservation': 10 },
    { 'nom': 'Documents RH', 'code': 'CAT-RH', 'domaine': 'rh', 'couleur': '#8b5cf6', 'conservation': None },
    { 'nom': 'Bibliothèque', 'code': 'CAT-BIBLIO', 'domaine': 'bibliotheque', 'couleur': '#06b6d4', 'conservation': None },
    { 'nom': 'Qualité & Procédures', 'code': 'CAT-QUAL', 'domaine': 'qualite', 'couleur': '#ef4444', 'conservation': None },
]

DOCUMENTS = [
    {
        'titre': 'Termes de Référence — Formation ASC District Abobo',
        'type': 'tdr', 'cat': 'CAT-TDR', 'version': '2.1',
        'conf': 'interne', 'langue': 'fr', 'statut': 'publie',
        'mots_cles': 'formation, ASC, santé, Abobo, TDR',
        'auteur_externe': 'Direction Santé',
        'description': 'TDR pour la formation de 85 agents de santé communautaires dans le district d\'Abobo. Inclut le curriculum, le calendrier et le budget prévisionnel.',
        'delta': -90,
    },
    {
        'titre': 'Rapport d\'activités PRCC — Semestre 1 2026',
        'type': 'rapport', 'cat': 'CAT-RPT', 'version': '1.0',
        'conf': 'interne', 'langue': 'fr', 'statut': 'approuve',
        'mots_cles': 'rapport, S1, 2026, PRCC, activités',
        'auteur_externe': 'Coordination PRCC',
        'description': 'Rapport semestriel d\'activités du Programme de Renforcement des Capacités Communautaires pour le premier semestre 2026.',
        'delta': -30,
    },
    {
        'titre': 'Contrat Cabinet EXPERTISE CONSEIL CI',
        'type': 'contrat', 'cat': 'CAT-FAC', 'version': '1.0',
        'conf': 'confidentiel', 'langue': 'fr', 'statut': 'publie',
        'mots_cles': 'contrat, consultant, expertise conseil',
        'auteur_externe': '',
        'description': 'Contrat de prestation pour consultation spécialisée en nutrition communautaire.',
        'delta': -60,
    },
    {
        'titre': 'Budget consolidé PRCC 2026',
        'type': 'budget', 'cat': 'CAT-BUD', 'version': '1.2',
        'conf': 'confidentiel', 'langue': 'fr', 'statut': 'publie',
        'mots_cles': 'budget, PRCC, 2026, consolidé',
        'auteur_externe': 'Direction Financière',
        'description': 'Budget consolidé de l\'exercice 2026 incluant toutes les composantes du programme.',
        'delta': -120,
    },
    {
        'titre': 'Note de service — Procédures paiement fournisseurs',
        'type': 'note_service', 'cat': 'CAT-ADM', 'version': '1.0',
        'conf': 'interne', 'langue': 'fr', 'statut': 'publie',
        'mots_cles': 'note de service, paiement, fournisseurs, procédure',
        'auteur_externe': 'Direction Générale',
        'description': 'Note de service définissant les nouvelles procédures de validation et de paiement des fournisseurs.',
        'delta': -45,
    },
    {
        'titre': 'PV Réunion Comité de Pilotage — Mars 2026',
        'type': 'pv', 'cat': 'CAT-PV', 'version': '1.0',
        'conf': 'interne', 'langue': 'fr', 'statut': 'publie',
        'mots_cles': 'PV, comité, pilotage, mars 2026',
        'auteur_externe': 'Secrétariat',
        'description': 'Procès-verbal de la réunion du comité de pilotage tenu le 15 mars 2026.',
        'delta': -75,
    },
    {
        'titre': 'Rapport évaluation mi-parcours PRCC',
        'type': 'rapport', 'cat': 'CAT-RPT', 'version': '2.0',
        'conf': 'public', 'langue': 'fr', 'statut': 'publie',
        'mots_cles': 'évaluation, mi-parcours, PRCC, 2026',
        'auteur_externe': 'Cabinet d\'évaluation externe',
        'description': 'Rapport d\'évaluation à mi-parcours du programme PRCC. Analyse des performances, recommandations et plan d\'amélioration.',
        'delta': -20,
    },
    {
        'titre': 'Manuel de procédures GED — Programme PRCC',
        'type': 'procedure', 'cat': 'CAT-QUAL', 'version': '1.0',
        'conf': 'interne', 'langue': 'fr', 'statut': 'soumis',
        'mots_cles': 'procédures, GED, manuel, classement',
        'auteur_externe': 'Équipe GED',
        'description': 'Manuel décrivant les procédures de gestion électronique des documents du programme.',
        'delta': -5,
    },
]

DOSSIERS = [
    { 'nom': 'Programme PRCC 2024-2028', 'description': 'Dossier principal programme', 'parent': None },
    { 'nom': 'Composante Santé', 'description': 'Tous les documents santé', 'parent': 'Programme PRCC 2024-2028' },
    { 'nom': 'Composante AGR', 'description': 'Documents AGR et coopératives', 'parent': 'Programme PRCC 2024-2028' },
    { 'nom': 'Administration', 'description': 'Documents administratifs et RH', 'parent': None },
    { 'nom': 'Finances 2026', 'description': 'Budgets et états financiers 2026', 'parent': None },
    { 'nom': 'Rapports', 'description': 'Tous les rapports produits', 'parent': 'Programme PRCC 2024-2028' },
    { 'nom': 'Formations', 'description': 'TDR et supports de formation', 'parent': 'Composante Santé' },
]

BOITES_ARCHIVES = [
    {
        'intitule': 'Archives Composante Santé 2024',
        'cat': 'CAT-PROJ', 'service': 'Direction Santé',
        'annee_debut': 2024, 'annee_fin': 2024,
        'statut': 'versee', 'localisation': 'Serveur NAS / Archives-Santé-2024',
        'delta_destruction': 10 * 365,
    },
    {
        'intitule': 'Archives Finances 2024-2025',
        'cat': 'CAT-FIN', 'service': 'Direction Financière',
        'annee_debut': 2024, 'annee_fin': 2025,
        'statut': 'fermee', 'localisation': 'Coffre-fort numérique / FIN-2024-2025',
        'delta_destruction': 10 * 365,
        'chiffree': True,
    },
    {
        'intitule': 'Archives Courriers 2023',
        'cat': 'CAT-COR', 'service': 'Secrétariat',
        'annee_debut': 2023, 'annee_fin': 2023,
        'statut': 'versee', 'localisation': 'Armoire physique A3 / Étagère 2',
        'delta_destruction': 5 * 365,
    },
    {
        'intitule': 'Archives PRCC Phase 1 — Permanent',
        'cat': 'CAT-PROJ', 'service': 'Coordination Générale',
        'annee_debut': 2020, 'annee_fin': 2023,
        'statut': 'versee', 'localisation': 'Serveur Archives / PRCC-Phase1',
        'delta_destruction': None,
    },
]

MODELES = [
    {
        'code': 'MOD-TDR-01', 'titre': 'Modèle TDR Formation Agents',
        'type': 'tdr', 'langue': 'fr', 'version': '2.0',
        'description': 'Modèle standard pour les termes de référence de formation d\'agents de terrain.',
        'instructions': '1. Remplacer les champs en [crochets]\n2. Adapter le budget à l\'activité\n3. Faire valider par la coordination avant diffusion',
    },
    {
        'code': 'MOD-RPT-01', 'titre': 'Modèle Rapport Mensuel d\'Activités',
        'type': 'rapport', 'langue': 'fr', 'version': '1.5',
        'description': 'Rapport mensuel standardisé pour le suivi des activités terrain.',
        'instructions': 'Compléter toutes les sections. Le tableau récapitulatif est obligatoire.',
    },
    {
        'code': 'MOD-RPT-EN', 'titre': 'Monthly Activity Report Template',
        'type': 'rapport', 'langue': 'en', 'version': '1.0',
        'description': 'Standard monthly activity report for donor reporting.',
        'instructions': 'Fill all sections. Submit before the 5th of each month.',
    },
    {
        'code': 'MOD-COR-01', 'titre': 'Modèle Lettre Officielle',
        'type': 'courrier', 'langue': 'fr', 'version': '1.0',
        'description': 'Modèle de lettre officielle avec en-tête standardisé.',
        'instructions': 'Utiliser le papier à en-tête officiel. Ne pas modifier les marges.',
    },
    {
        'code': 'MOD-CTR-01', 'titre': 'Modèle Contrat Consultant',
        'type': 'contrat', 'langue': 'fr', 'version': '3.1',
        'description': 'Contrat type pour consultants individuels et courts séjours.',
        'instructions': 'Faire valider par le service juridique avant signature. Durée max 30 jours.',
    },
    {
        'code': 'MOD-BUD-01', 'titre': 'Modèle Budget Activité',
        'type': 'budget', 'langue': 'fr', 'version': '2.0',
        'description': 'Tableau budgétaire standard pour la planification des activités.',
        'instructions': 'Respecter la nomenclature des lignes budgétaires (codes 611-624).',
    },
    {
        'code': 'MOD-SWOT-01', 'titre': 'Modèle Analyse SWOT',
        'type': 'swot', 'langue': 'fr', 'version': '1.0',
        'description': 'Canevas d\'analyse SWOT pour projets et programmes.',
        'instructions': 'Compléter avec l\'équipe. Minimum 3 éléments par quadrant.',
    },
    {
        'code': 'MOD-PA-01', 'titre': "Modèle Plan d'Action Trimestriel",
        'type': 'plan_action', 'langue': 'fr', 'version': '1.2',
        'description': "Plan d'action trimestriel avec indicateurs et responsables.",
        'instructions': "Relier chaque action aux résultats du cadre logique. Valider en réunion d'équipe.",
    },
]

BIBLIOTHEQUE = [
    {
        'titre': 'Guide de gestion du cycle de projet — OCDE/DAC',
        'cat': 'gestion_projet', 'sous_cat': 'Cycle de projet',
        'auteur': 'OCDE/DAC', 'org': 'OCDE', 'annee': 2018, 'langue': 'fr',
        'url': 'https://www.oecd.org',
        'mots_cles': 'cycle projet, PCM, planification, OCDE',
        'description': 'Guide complet sur le cycle de gestion de projet selon les standards DAC/OCDE.',
        'public': True,
    },
    {
        'titre': 'Manuel suivi-évaluation axé sur les résultats — PNUD',
        'cat': 'gestion_projet', 'sous_cat': 'Suivi-Évaluation',
        'auteur': 'PNUD', 'org': 'PNUD', 'annee': 2020, 'langue': 'fr',
        'url': '',
        'mots_cles': 'suivi, évaluation, résultats, PNUD, indicateurs',
        'description': 'Manuel pratique pour mettre en place un système de suivi-évaluation axé sur les résultats.',
        'public': True,
    },
    {
        'titre': 'Guide des procédures financières — Enabel',
        'cat': 'finance', 'sous_cat': 'Comptabilité',
        'auteur': 'Enabel', 'org': 'Enabel', 'annee': 2022, 'langue': 'fr',
        'url': '',
        'mots_cles': 'procédures financières, Enabel, comptabilité, justificatifs',
        'description': 'Procédures financières standard pour projets financés par la coopération belge.',
        'public': False,
    },
    {
        'titre': 'Guide pratique du droit du travail en Côte d\'Ivoire',
        'cat': 'rh', 'sous_cat': 'Droit du travail',
        'auteur': 'Ministère de l\'Emploi', 'org': "République de Côte d'Ivoire", 'annee': 2021, 'langue': 'fr',
        'url': '',
        'mots_cles': "droit du travail, Côte d'Ivoire, contrat, RH",
        'description': "Guide du droit du travail ivoirien : contrats, congés, licenciement, syndicats.",
        'public': True,
    },
    {
        'titre': 'ISO 15489 — Records Management Standard',
        'cat': 'qualite', 'sous_cat': 'Archivage',
        'auteur': 'ISO', 'org': 'ISO', 'annee': 2016, 'langue': 'en',
        'url': 'https://www.iso.org',
        'mots_cles': 'ISO 15489, archivage, records management, norme',
        'description': 'Norme internationale de gestion des documents d\'activité (Records Management).',
        'public': True,
    },
    {
        'titre': 'KoboToolbox Guide de l\'utilisateur',
        'cat': 'technique', 'sous_cat': 'Collecte de données',
        'auteur': 'KoboToolbox Team', 'org': 'Kobo Inc.', 'annee': 2023, 'langue': 'fr',
        'url': 'https://support.kobotoolbox.org',
        'mots_cles': 'KoboToolbox, collecte données, mobile, formulaires',
        'description': 'Guide complet d\'utilisation de KoboToolbox pour la collecte de données terrain.',
        'public': True,
    },
]


class Command(BaseCommand):
    help = 'Seed Lot 6 — GED & Archivage électronique (M24, M25 + Bibliothèque + Modèles)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les données GED existantes')

    def handle(self, *args, **options):
        admin = self._get_admin()
        if not admin:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
            return
        projet = self._get_projet()
        self.stdout.write(f'[INFO] Admin : {admin.email} | Projet : {projet.code if projet else "—"}')

        try:
            with transaction.atomic():
                if options['reset']:
                    self._reset()
                cats     = self._seed_categories()
                dossiers = self._seed_dossiers(admin, projet)
                docs     = self._seed_documents(admin, projet, cats)
                self._seed_boites(admin, projet, cats)
                self._seed_conservation(cats)
                self._seed_modeles(admin)
                self._seed_bibliotheque(admin)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'[ERREUR] : {exc}'))
            import traceback; traceback.print_exc()
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed Lot 6 terminé !'))

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    def _reset(self):
        from ged.models import (
            Categorie, Document, DossierDocument, BoiteArchive,
            ModeleDocument, EntreesBibliotheque, PlanConservation,
        )
        self.stdout.write(self.style.WARNING('[RESET] Suppression données GED…'))
        for M in [EntreesBibliotheque, ModeleDocument, PlanConservation, BoiteArchive, DossierDocument, Document, Categorie]:
            n = M.objects.all().delete()
            self.stdout.write(f'   {M.__name__}: {n[0]} supprimé(s)')

    def _seed_categories(self):
        from ged.models import Categorie
        self.stdout.write('\n>> Catégories GED…')
        result = {}

        # Créer en 2 passes (parents d'abord, enfants ensuite)
        for pass_num in range(2):
            for data in CATEGORIES:
                if pass_num == 0 and data.get('parent'):
                    continue
                if pass_num == 1 and not data.get('parent'):
                    continue
                parent = result.get(data.get('parent')) if data.get('parent') else None
                cat, created = Categorie.objects.get_or_create(
                    code=data['code'],
                    defaults={
                        'nom': data['nom'],
                        'domaine': data['domaine'],
                        'parent': parent,
                        'couleur': data.get('couleur', '#3388ff'),
                        'duree_conservation_ans': data.get('conservation'),
                        'actif': True,
                    }
                )
                result[data['code']] = cat
                self._log('Catégorie', cat, created)
        return result

    def _seed_dossiers(self, admin, projet):
        from ged.models import DossierDocument
        self.stdout.write('\n>> Dossiers…')
        result = {}
        for data in DOSSIERS:
            parent = result.get(data.get('parent')) if data.get('parent') else None
            d, created = DossierDocument.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'description': data.get('description', ''),
                    'parent': parent,
                    'projet': projet,
                    'created_by': admin,
                    'responsable': admin,
                }
            )
            result[data['nom']] = d
            self._log('Dossier', d, created)
        return result

    def _seed_documents(self, admin, projet, cats):
        from ged.models import Document
        self.stdout.write('\n>> Documents…')
        today = date.today()
        docs = []
        for data in DOCUMENTS:
            titre = data['titre']
            if Document.objects.filter(titre=titre).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {titre[:60]}'))
                continue
            cat = cats.get(data['cat'])
            doc = Document.objects.create(
                titre=titre,
                type_document=data['type'],
                categorie=cat,
                projet=projet,
                version=data['version'],
                confidentialite=data['conf'],
                langue=data['langue'],
                statut=data['statut'],
                mots_cles=data['mots_cles'],
                auteur_externe=data.get('auteur_externe', ''),
                description=data.get('description', ''),
                auteur=admin,
                valide_par=admin if data['statut'] in ('approuve', 'publie') else None,
                date_validation=timezone.now() if data['statut'] in ('approuve', 'publie') else None,
                horodatage=timezone.now() if data['statut'] == 'publie' else None,
                created_at=timezone.now() - timedelta(days=abs(data['delta'])),
            )
            # Simule un résumé IA
            doc.resume_auto = f"Ce document traite de : {data['mots_cles']}. Produit par {data['auteur_externe'] or 'l\'équipe interne'}."
            doc.mots_cles_auto = data['mots_cles']
            doc.save(update_fields=['resume_auto', 'mots_cles_auto'])
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Document: {titre[:60]}'))
            docs.append(doc)
        return docs

    def _seed_boites(self, admin, projet, cats):
        from ged.models import BoiteArchive
        self.stdout.write('\n>> Boîtes d\'archives…')
        today = date.today()
        for data in BOITES_ARCHIVES:
            ref = f"BA-{data['annee_debut']}-{data['cat'][-3:]}"
            if BoiteArchive.objects.filter(intitule=data['intitule']).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {data["intitule"][:60]}'))
                continue
            BoiteArchive.objects.create(
                intitule=data['intitule'],
                categorie=cats.get(data['cat']),
                projet=projet,
                service_producteur=data['service'],
                annee_debut=data['annee_debut'],
                annee_fin=data['annee_fin'],
                statut=data['statut'],
                localisation=data['localisation'],
                date_destruction_prevue=today + timedelta(days=data['delta_destruction']) if data.get('delta_destruction') else None,
                chiffree=data.get('chiffree', False),
                created_by=admin,
            )
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Boîte: {data["intitule"][:60]}'))

    def _seed_conservation(self, cats):
        from ged.models import PlanConservation
        self.stdout.write('\n>> Plans de conservation…')
        plans = [
            { 'cat': 'CAT-FAC', 'active': 5, 'inter': 5, 'total': 10, 'sort': 'destruction', 'base': 'Code OHADA — art. 137 (10 ans)' },
            { 'cat': 'CAT-BUD', 'active': 5, 'inter': 5, 'total': 10, 'sort': 'destruction', 'base': 'Réglementation financière interne' },
            { 'cat': 'CAT-COR', 'active': 2, 'inter': 3, 'total': 5,  'sort': 'tri',         'base': 'Politique archivage organisationnelle' },
            { 'cat': 'CAT-RPT', 'active': 5, 'inter': None, 'total': None, 'sort': 'conservation', 'base': 'Valeur historique — conservation permanente' },
            { 'cat': 'CAT-PV',  'active': 5, 'inter': 5, 'total': 10, 'sort': 'conservation', 'base': 'Documents officiels' },
        ]
        for data in plans:
            cat = cats.get(data['cat'])
            if not cat:
                continue
            p, created = PlanConservation.objects.get_or_create(
                categorie=cat,
                defaults={
                    'duree_active_ans': data['active'],
                    'duree_intermediaire_ans': data['inter'] or 0,
                    'duree_totale_ans': data['total'],
                    'sort_final': data['sort'],
                    'base_legale': data['base'],
                }
            )
            self._log('Plan de conservation', p, created)

    def _seed_modeles(self, admin):
        from ged.models import ModeleDocument
        self.stdout.write('\n>> Modèles de documents…')
        for data in MODELES:
            m, created = ModeleDocument.objects.get_or_create(
                code=data['code'],
                defaults={
                    'titre': data['titre'],
                    'type_modele': data['type'],
                    'langue': data['langue'],
                    'version': data['version'],
                    'description': data['description'],
                    'instructions': data['instructions'],
                    'actif': True,
                    'cree_par': admin,
                }
            )
            self._log('Modèle', m, created)

    def _seed_bibliotheque(self, admin):
        from ged.models import EntreesBibliotheque
        self.stdout.write('\n>> Bibliothèque…')
        for data in BIBLIOTHEQUE:
            e, created = EntreesBibliotheque.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'categorie': data['cat'],
                    'sous_categorie': data['sous_cat'],
                    'auteur': data['auteur'],
                    'organisation': data['org'],
                    'annee_publication': data['annee'],
                    'langue': data['langue'],
                    'url_externe': data['url'],
                    'mots_cles': data['mots_cles'],
                    'description': data['description'],
                    'est_public': data['public'],
                    'ajoute_par': admin,
                }
            )
            self._log('Bibliothèque', e, created)
