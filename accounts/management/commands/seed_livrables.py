"""
Seed enrichi pour M15 : Gestion des Livrables.

Crée des livrables réalistes de tous types et statuts avec :
  - Versions (historique)
  - Workflow de validation multi-étapes
  - Commentaires

Usage : python manage.py seed_livrables [--reset]
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


LIVRABLES = [
    # -- Rapports --------------------------------------------------------------
    {
        'code': 'LIV-RPT-001',
        'titre': 'Rapport annuel 2025 – Programme PRCC',
        'type': 'rapport', 'statut': 'publie',
        'description': (
            'Rapport annuel complet du Programme de Renforcement des Capacités Communautaires '
            'pour l\'exercice 2025. Couvre l\'ensemble des activités réalisées, les résultats '
            'atteints, l\'exécution budgétaire et les perspectives 2026.'
        ),
        'critere': 'Rapport validé par la Direction et approuvé par le bailleur (BM)',
        'date_delta': -120,
        'versions': [
            {'v': '0.1', 'desc': 'Premier jet – structure et données brutes', 'delta': -140},
            {'v': '0.5', 'desc': 'Version intermédiaire après revue technique', 'delta': -135},
            {'v': '1.0', 'desc': 'Version finale soumise au bailleur', 'delta': -125},
            {'v': '1.1', 'desc': 'Version corrigée suite aux commentaires BM', 'delta': -120},
        ],
        'validation_statuts': ['approuve', 'approuve', 'approuve', 'approuve'],
        'commentaires': [
            ('Section indicateurs à compléter avec données Q4', -138),
            ('Commentaires bailleur intégrés – version 1.1 OK', -119),
        ],
    },
    {
        'code': 'LIV-RPT-002',
        'titre': 'Rapport trimestriel Q1 2026 – Activités et résultats',
        'type': 'rapport', 'statut': 'valide',
        'description': (
            'Rapport d\'avancement du premier trimestre 2026 présentant les activités réalisées, '
            'les indicateurs atteints, les difficultés rencontrées et les actions correctives.'
        ),
        'critere': 'Rapport soumis dans les 30 jours suivant la fin du trimestre',
        'date_delta': -45,
        'versions': [
            {'v': '0.1', 'desc': 'Collecte des données – version brute', 'delta': -60},
            {'v': '1.0', 'desc': 'Version finale validée par le CP', 'delta': -46},
        ],
        'validation_statuts': ['approuve', 'approuve', 'approuve', 'en_attente'],
        'commentaires': [
            ('Données formation complétées. Avancement 68% confirmé.', -58),
        ],
    },
    {
        'code': 'LIV-RPT-003',
        'titre': 'Rapport trimestriel Q2 2026 – Bilan à mi-parcours',
        'type': 'rapport', 'statut': 'soumis',
        'description': (
            'Rapport du deuxième trimestre 2026 incluant le bilan semestriel S1 2026 '
            'et les perspectives pour le second semestre.'
        ),
        'critere': 'Transmission dans les 30 jours. Format bailleur respecté.',
        'date_delta': 5,
        'versions': [
            {'v': '0.1', 'desc': 'Version brouillon – en cours de rédaction', 'delta': -3},
        ],
        'validation_statuts': ['en_attente', 'en_attente', 'en_attente', 'en_attente'],
        'commentaires': [],
    },
    # -- Études / TDR ----------------------------------------------------------
    {
        'code': 'LIV-ETU-001',
        'titre': 'Étude de base – Analyse des conditions socio-économiques des ménages cibles',
        'type': 'etude', 'statut': 'publie',
        'description': (
            'Étude de référence quantitative et qualitative auprès de 1 200 ménages dans '
            '45 villages des régions Abidjan, Bouaké et Korhogo. Établit les valeurs de référence '
            'des 25 indicateurs du cadre logique.'
        ),
        'critere': 'Rapport certifié par l\'équipe S&E. Données saisies dans KoboToolbox.',
        'date_delta': -90,
        'versions': [
            {'v': '0.3', 'desc': 'Version préliminaire', 'delta': -110},
            {'v': '1.0', 'desc': 'Version finale', 'delta': -92},
        ],
        'validation_statuts': ['approuve', 'approuve', 'approuve', 'approuve'],
        'commentaires': [
            ('Données de nutrition vérifiées et cohérentes', -105),
        ],
    },
    {
        'code': 'LIV-TDR-001',
        'titre': 'TDR – Mission évaluation mi-parcours PRCC',
        'type': 'tdr', 'statut': 'valide',
        'description': (
            'Termes de référence pour la mission d\'évaluation à mi-parcours du programme PRCC. '
            'Définit la méthodologie, le profil des évaluateurs, le calendrier et les livrables '
            'attendus de la mission conjointe avec la Banque Mondiale.'
        ),
        'critere': 'TDR validé par la Direction et la BM avant publication de l\'appel',
        'date_delta': 8,
        'versions': [
            {'v': '0.1', 'desc': 'Première version soumise à la BM', 'delta': -5},
            {'v': '1.0', 'desc': 'Version finale après commentaires BM', 'delta': 6},
        ],
        'validation_statuts': ['approuve', 'approuve', 'en_attente', 'en_attente'],
        'commentaires': [
            ('Commentaires BM : inclure un volet genre dans la méthodologie', 0),
        ],
    },
    # -- Manuels / Guides ------------------------------------------------------
    {
        'code': 'LIV-MAN-001',
        'titre': 'Guide de l\'agent de santé communautaire – Module Nutrition',
        'type': 'manuel', 'statut': 'publie',
        'description': (
            'Manuel pratique destiné aux 500 agents de santé communautaires formés. '
            'Couvre : évaluation nutritionnelle MUAC, pratiques ANJE, messages clés, '
            'fiches conseils et outils de collecte terrain.'
        ),
        'critere': '500 exemplaires imprimés et distribués aux agents certifiés',
        'date_delta': -25,
        'versions': [
            {'v': '0.1', 'desc': 'Version brouillon – révision interne', 'delta': -50},
            {'v': '0.2', 'desc': 'Version testée sur le terrain avec 10 agents pilotes', 'delta': -40},
            {'v': '1.0', 'desc': 'Version finale validée', 'delta': -27},
        ],
        'validation_statuts': ['approuve', 'approuve', 'approuve', 'approuve'],
        'commentaires': [
            ('Illustrations à simplifier (retour agents pilotes)', -38),
            ('Simplifications effectuées. Validé par responsable médical.', -30),
        ],
    },
    {
        'code': 'LIV-MAN-002',
        'titre': 'Manuel de gestion financière – Coopératives agricoles',
        'type': 'manuel', 'statut': 'en_revision',
        'description': (
            'Guide pratique de gestion financière et comptable destiné aux comités de gestion '
            'des coopératives agricoles. Inclut les procédures de tenue de caisse, états financiers '
            'simplifiés et outils de suivi budgétaire.'
        ),
        'critere': 'Testé et validé par 3 coopératives pilotes avant diffusion large',
        'date_delta': 20,
        'versions': [
            {'v': '0.1', 'desc': 'Première version en cours de révision', 'delta': -10},
        ],
        'validation_statuts': ['en_attente', 'en_attente', 'en_attente', 'en_attente'],
        'commentaires': [
            ('Adapter les exemples au contexte des coopératives rurales ivoiriennes', -8),
        ],
    },
    # -- Techniques ------------------------------------------------------------
    {
        'code': 'LIV-TEC-001',
        'titre': 'Base de données bénéficiaires – KoboToolbox v1.0',
        'type': 'bdd', 'statut': 'valide',
        'description': (
            'Base de données consolidée des 6 000 bénéficiaires directs du programme. '
            'Collectée via KoboToolbox dans 45 villages, avec données socio-économiques, '
            'sanitaires, nutritionnelles et de scolarisation.'
        ),
        'critere': '6 000 fiches complètes. Taux de remplissage > 95%. Données vérifiées.',
        'date_delta': -20,
        'versions': [
            {'v': '0.5', 'desc': 'Export initial – 4 800 fiches', 'delta': -35},
            {'v': '1.0', 'desc': 'Version complète – 6 000 fiches validées', 'delta': -21},
        ],
        'validation_statuts': ['approuve', 'approuve', 'en_attente', 'en_attente'],
        'commentaires': [
            ('200 fiches à compléter (villages isolés)', -32),
            ('Complété – mission terrain effectuée', -22),
        ],
    },
    {
        'code': 'LIV-TEC-002',
        'titre': 'Application mobile suivi bénéficiaires – Version 2.0',
        'type': 'logiciel', 'statut': 'brouillon',
        'description': (
            'Version 2.0 de l\'application KoboCollect personnalisée pour le programme. '
            'Nouvelles fonctionnalités : collecte hors ligne, géolocalisation des visites '
            'et synchronisation automatique des données.'
        ),
        'critere': 'Tests réussis sur 10 tablettes. Déploiement validé par le responsable SIG.',
        'date_delta': 45,
        'versions': [],
        'validation_statuts': ['en_attente', 'en_attente', 'en_attente', 'en_attente'],
        'commentaires': [],
    },
    # -- Terrain ---------------------------------------------------------------
    {
        'code': 'LIV-TER-001',
        'titre': 'Rapport photographique – Travaux construction centres de santé S1 2026',
        'type': 'media', 'statut': 'valide',
        'description': (
            'Documentation photographique des travaux de construction et réhabilitation '
            'des 8 centres de santé. Couvre les états d\'avancement des 4 premiers sites '
            'à fin mai 2026.'
        ),
        'critere': '100 photos + vidéo de présentation de 5 min',
        'date_delta': -10,
        'versions': [
            {'v': '1.0', 'desc': 'Galerie complète 100 photos + 2 vidéos', 'delta': -11},
        ],
        'validation_statuts': ['approuve', 'en_attente', 'en_attente', 'en_attente'],
        'commentaires': [],
    },
    {
        'code': 'LIV-TER-002',
        'titre': 'Cartographie des 45 villages d\'intervention – SIG',
        'type': 'cartographie', 'statut': 'publie',
        'description': (
            'Cartographie SIG complète des 45 villages d\'intervention du programme. '
            'Inclut localisation des infrastructures, voies d\'accès, points d\'eau, '
            'centres de santé et écoles. Formats SHP et PDF.'
        ),
        'critere': 'Fichiers SIG validés par le SIG-iste. Carte imprimée format A0.',
        'date_delta': -70,
        'versions': [
            {'v': '1.0', 'desc': 'Cartographie initiale 45 villages', 'delta': -75},
            {'v': '1.1', 'desc': 'Mise à jour avec 3 nouveaux points d\'eau', 'delta': -71},
        ],
        'validation_statuts': ['approuve', 'approuve', 'approuve', 'approuve'],
        'commentaires': [],
    },
    # -- Infrastructure --------------------------------------------------------
    {
        'code': 'LIV-INF-001',
        'titre': 'Rapport réception provisoire – Centre de santé d\'Abobo-Est',
        'type': 'infrastructure', 'statut': 'rejete',
        'description': (
            'Procès-verbal de réception provisoire du centre de santé d\'Abobo-Est. '
            'Réception provisoire rejetée suite à des non-conformités techniques constatées '
            'lors de la visite d\'inspection : toiture insuffisante et système électrique non conforme.'
        ),
        'critere': 'PV signé par le chef de projet, l\'entreprise et le bureau de contrôle',
        'date_delta': -5,
        'versions': [
            {'v': '0.1', 'desc': 'Premier rapport de visite avec réserves', 'delta': -6},
        ],
        'validation_statuts': ['rejete', 'en_attente', 'en_attente', 'en_attente'],
        'commentaires': [
            ('Non-conformités : toiture et installation électrique à reprendre', -5),
            ('Entreprise notifiée – délai de reprise : 3 semaines', -4),
        ],
    },
    # -- Formation -------------------------------------------------------------
    {
        'code': 'LIV-FOR-001',
        'titre': 'Rapport formation alphabétisation – Promotion 1 (120 femmes)',
        'type': 'formation', 'statut': 'archive',
        'description': (
            'Rapport complet de la première promotion de formation en alphabétisation fonctionnelle. '
            '120 femmes rurales formées sur 4 mois. Résultats des évaluations, liste des certifiées '
            'et recommandations pour la Promotion 2.'
        ),
        'critere': 'Rapport validé. Certificats émis pour les participantes ayant le score >= 70%.',
        'date_delta': -150,
        'versions': [
            {'v': '1.0', 'desc': 'Rapport final Promotion 1', 'delta': -152},
        ],
        'validation_statuts': ['approuve', 'approuve', 'approuve', 'approuve'],
        'commentaires': [
            ('Excellent résultat : 94% des participantes certifiées', -148),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed enrichi M15 – Livrables (tous types, tous statuts, versions, workflow, commentaires)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les livrables existants')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            admin = self._get_admin()
            if not admin:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
                return
            projet = self._get_projet()
            if not projet:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun projet. Lancez seed_projets d\'abord.'))
                return

            count = self._seed_livrables(admin, projet)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Seed livrables terminé ! {count} livrables créés.'))

    def _reset(self):
        from execution.models import Livrable, VersionLivrable, ValidationLivrable, CommentaireLivrable
        self.stdout.write(self.style.WARNING('[RESET] Suppression livrables…'))
        CommentaireLivrable.objects.all().delete()
        ValidationLivrable.objects.all().delete()
        VersionLivrable.objects.all().delete()
        Livrable.objects.all().delete()
        self.stdout.write('   Terminé.')

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    def _seed_livrables(self, admin, projet):
        from execution.models import (
            Livrable, VersionLivrable, ValidationLivrable, CommentaireLivrable, ActiviteExecution
        )
        activites = list(ActiviteExecution.objects.filter(projet=projet)[:8])
        self.stdout.write('\n>> Livrables enrichis (M15)…')
        today = date.today()
        count = 0

        for i, data in enumerate(LIVRABLES):
            date_prevue  = today + timedelta(days=data['date_delta'])
            date_livr    = date_prevue if data['statut'] in ('valide', 'publie', 'archive') else None
            version_cur  = data['versions'][-1]['v'] if data['versions'] else '0.1'
            activite     = activites[i % len(activites)] if activites else None

            livrable, created = Livrable.objects.get_or_create(
                code=data['code'],
                defaults={
                    'titre':           data['titre'],
                    'description':     data['description'],
                    'type_livrable':   data['type'],
                    'projet':          projet,
                    'activite':        activite,
                    'responsable':     admin,
                    'date_prevue':     date_prevue,
                    'date_livraison':  date_livr,
                    'statut':          data['statut'],
                    'version_courante': version_cur,
                    'critere_acceptation': data.get('critere', ''),
                    'created_by':      admin,
                }
            )
            self._log('Livrable', livrable, created)
            count += 1 if created else 0

            if not created:
                continue

            # Versions
            for vd in data['versions']:
                date_v = today + timedelta(days=vd['delta'])
                est_cur = (vd['v'] == version_cur)
                VersionLivrable.objects.create(
                    livrable=livrable,
                    numero_version=vd['v'],
                    description_changements=vd['desc'],
                    uploaded_by=admin,
                    est_courante=est_cur,
                )
                if est_cur:
                    livrable.version_courante = vd['v']
                    livrable.save(update_fields=['version_courante'])
                self.stdout.write(f'    + Version {vd["v"]}: {vd["desc"][:50]}')

            # Workflow de validation (4 étapes)
            etapes = [
                ('chef_projet',           1),
                ('responsable_programme', 2),
                ('coordonnateur',         3),
                ('final',                 4),
            ]
            val_statuts = data.get('validation_statuts', ['en_attente'] * 4)
            for (etape, ordre), vs in zip(etapes, val_statuts):
                ValidationLivrable.objects.create(
                    livrable=livrable,
                    etape=etape,
                    ordre=ordre,
                    statut=vs,
                    validateur=admin if vs in ('approuve', 'rejete') else None,
                    date_validation=timezone.now() if vs in ('approuve', 'rejete') else None,
                    commentaire='Approuvé.' if vs == 'approuve' else ('Rejeté : non-conformités.' if vs == 'rejete' else ''),
                )

            # Commentaires
            for contenu, delta in data.get('commentaires', []):
                CommentaireLivrable.objects.create(
                    livrable=livrable,
                    auteur=admin,
                    contenu=contenu,
                )
                self.stdout.write(f'    + Commentaire: {contenu[:60]}')

        return count
