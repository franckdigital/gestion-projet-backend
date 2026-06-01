"""
Seed Gantt — alimente TOUS les projets actifs avec des activités et tâches
bien datées pour rendre le Gantt exploitable.

Usage :
  python manage.py seed_gantt            # Ajoute sans supprimer
  python manage.py seed_gantt --reset    # Supprime et recrée
  python manage.py seed_gantt --projet PROJ-2023-008  # Un projet précis
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# --- Templates d'activités (réutilisés par projet avec variation) -------------

TEMPLATES_ACTIVITES = [
    {
        'suffix': 'Démarrage et installation',
        'description': 'Phase de démarrage du projet : installation des équipes, mise en place des outils de gestion, signature des accords de collaboration.',
        'priorite': 'critique', 'debut_delta': -90, 'fin_delta': -60,
        'taux_min': 100, 'statut': 'terminee',
        'taches': [
            {'titre': 'Recrutement équipe projet',           'debut': -90, 'fin': -80, 'taux': 100, 'statut': 'terminee', 'priorite': 'critique'},
            {'titre': 'Installation bureau et équipements',  'debut': -85, 'fin': -75, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Ouverture compte bancaire projet',    'debut': -80, 'fin': -70, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Atelier de lancement',                'debut': -72, 'fin': -65, 'taux': 100, 'statut': 'terminee', 'priorite': 'normale'},
        ],
    },
    {
        'suffix': 'Diagnostic et étude de base',
        'description': 'Réalisation du diagnostic initial et de l\'étude de base pour définir les valeurs de référence des indicateurs.',
        'priorite': 'haute', 'debut_delta': -75, 'fin_delta': -40,
        'taux_min': 100, 'statut': 'terminee',
        'taches': [
            {'titre': 'Élaboration des outils de collecte',  'debut': -75, 'fin': -65, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Formation des enquêteurs',            'debut': -65, 'fin': -58, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Collecte des données terrain',        'debut': -58, 'fin': -45, 'taux': 100, 'statut': 'terminee', 'priorite': 'critique'},
            {'titre': 'Analyse et rédaction rapport baseline','debut': -45, 'fin': -40, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
        ],
    },
    {
        'suffix': 'Renforcement des capacités – Phase 1',
        'description': 'Sessions de formation et renforcement des capacités des acteurs cibles dans la première phase du projet.',
        'priorite': 'haute', 'debut_delta': -50, 'fin_delta': -15,
        'taux_min': 80, 'statut': 'en_cours',
        'taches': [
            {'titre': 'Conception du curriculum de formation', 'debut': -50, 'fin': -42, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Formation des formateurs',              'debut': -42, 'fin': -35, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Sessions de formation Groupe A',        'debut': -35, 'fin': -22, 'taux': 100, 'statut': 'terminee', 'priorite': 'critique'},
            {'titre': 'Sessions de formation Groupe B',        'debut': -22, 'fin': -10, 'taux': 75,  'statut': 'en_cours',  'priorite': 'critique'},
            {'titre': 'Évaluation des acquis',                 'debut': -10, 'fin': -3,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
        ],
    },
    {
        'suffix': 'Activités terrain – Composante principale',
        'description': 'Déploiement des activités principales sur le terrain : interventions directes auprès des bénéficiaires.',
        'priorite': 'critique', 'debut_delta': -35, 'fin_delta': 30,
        'taux_min': 40, 'statut': 'en_cours',
        'taches': [
            {'titre': 'Cartographie des zones intervention',   'debut': -35, 'fin': -28, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Mobilisation communautaire',            'debut': -28, 'fin': -15, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Interventions Site 1',                  'debut': -15, 'fin': 5,   'taux': 65,  'statut': 'en_cours',  'priorite': 'critique'},
            {'titre': 'Interventions Site 2',                  'debut': -10, 'fin': 15,  'taux': 30,  'statut': 'en_cours',  'priorite': 'critique'},
            {'titre': 'Interventions Site 3',                  'debut': 5,   'fin': 30,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Rapport d\'avancement terrain',         'debut': 25,  'fin': 30,  'taux': 0,   'statut': 'a_faire',   'priorite': 'normale'},
        ],
    },
    {
        'suffix': 'Acquisition et gestion des équipements',
        'description': 'Processus d\'acquisition, réception et gestion des équipements et matériels nécessaires au projet.',
        'priorite': 'normale', 'debut_delta': -20, 'fin_delta': 25,
        'taux_min': 30, 'statut': 'en_cours',
        'taches': [
            {'titre': 'Rédaction des spécifications techniques', 'debut': -20, 'fin': -12, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Appel d\'offres fournisseurs',             'debut': -12, 'fin': -2,  'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Analyse des offres et sélection',          'debut': -2,  'fin': 5,   'taux': 50,  'statut': 'en_cours',  'priorite': 'normale'},
            {'titre': 'Commande et livraison',                    'debut': 5,   'fin': 18,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Réception et enregistrement',              'debut': 18,  'fin': 25,  'taux': 0,   'statut': 'a_faire',   'priorite': 'normale'},
        ],
    },
    {
        'suffix': 'Suivi-évaluation et collecte de données',
        'description': 'Mise en place du système de suivi-évaluation et collecte périodique des données sur les indicateurs.',
        'priorite': 'haute', 'debut_delta': -25, 'fin_delta': 45,
        'taux_min': 35, 'statut': 'en_cours',
        'taches': [
            {'titre': 'Paramétrage formulaires KoboToolbox',   'debut': -25, 'fin': -18, 'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Collecte données Trimestre 1',          'debut': -18, 'fin': -5,  'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Analyse et validation données T1',      'debut': -5,  'fin': 3,   'taux': 60,  'statut': 'en_cours',  'priorite': 'haute'},
            {'titre': 'Collecte données Trimestre 2',          'debut': 10,  'fin': 30,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Analyse et validation données T2',      'debut': 30,  'fin': 45,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
        ],
    },
    {
        'suffix': 'Coordination et communication',
        'description': 'Réunions de coordination, communication avec les partenaires et bailleurs, gestion des relations.',
        'priorite': 'normale', 'debut_delta': -15, 'fin_delta': 60,
        'taux_min': 25, 'statut': 'en_cours',
        'taches': [
            {'titre': 'Réunion coordination mensuelle – Mois 1', 'debut': -15, 'fin': -14, 'taux': 100, 'statut': 'terminee', 'priorite': 'normale'},
            {'titre': 'Rapport mensuel M-1',                     'debut': -14, 'fin': -10, 'taux': 100, 'statut': 'terminee', 'priorite': 'normale'},
            {'titre': 'Réunion coordination mensuelle – Mois 2', 'debut': 15,  'fin': 16,  'taux': 0,   'statut': 'a_faire',   'priorite': 'normale'},
            {'titre': 'Rapport mensuel M-2',                     'debut': 16,  'fin': 20,  'taux': 0,   'statut': 'a_faire',   'priorite': 'normale'},
            {'titre': 'Rapport trimestriel Q2',                  'debut': 50,  'fin': 60,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
        ],
    },
    {
        'suffix': 'Travaux d\'infrastructure',
        'description': 'Travaux de construction, réhabilitation ou aménagement d\'infrastructures dans le cadre du projet.',
        'priorite': 'critique', 'debut_delta': -10, 'fin_delta': 75,
        'taux_min': 15, 'statut': 'en_cours',
        'taches': [
            {'titre': 'Études techniques et plans',            'debut': -10, 'fin': -2,  'taux': 100, 'statut': 'terminee', 'priorite': 'haute'},
            {'titre': 'Dossier appel d\'offres travaux',       'debut': -2,  'fin': 8,   'taux': 40,  'statut': 'en_cours',  'priorite': 'haute'},
            {'titre': 'Sélection entreprise',                  'debut': 8,   'fin': 18,  'taux': 0,   'statut': 'a_faire',   'priorite': 'critique'},
            {'titre': 'Travaux Site A',                        'debut': 18,  'fin': 50,  'taux': 0,   'statut': 'a_faire',   'priorite': 'critique'},
            {'titre': 'Travaux Site B',                        'debut': 25,  'fin': 60,  'taux': 0,   'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Réception et contrôle qualité',        'debut': 60,  'fin': 75,  'taux': 0,   'statut': 'a_faire',   'priorite': 'critique'},
        ],
    },
    {
        'suffix': 'Planification deuxième phase',
        'description': 'Préparation et planification de la deuxième phase du projet sur la base des leçons apprises.',
        'priorite': 'normale', 'debut_delta': 15, 'fin_delta': 60,
        'taux_min': 0, 'statut': 'en_attente',
        'taches': [
            {'titre': 'Revue des résultats Phase 1',          'debut': 15,  'fin': 22,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Ateliers de planification participative','debut': 22,  'fin': 32,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Rédaction plan d\'action Phase 2',     'debut': 32,  'fin': 45,  'taux': 0, 'statut': 'a_faire',   'priorite': 'normale'},
            {'titre': 'Validation plan avec bailleurs',       'debut': 45,  'fin': 60,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
        ],
    },
    {
        'suffix': 'Audit et évaluation finale',
        'description': 'Conduite de l\'audit financier final et de l\'évaluation externe du projet en vue de la clôture.',
        'priorite': 'haute', 'debut_delta': 45, 'fin_delta': 90,
        'taux_min': 0, 'statut': 'planifiee',
        'taches': [
            {'titre': 'TDR Audit et sélection auditeur',      'debut': 45,  'fin': 55,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Collecte pièces comptables',           'debut': 55,  'fin': 65,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Audit terrain',                        'debut': 65,  'fin': 78,  'taux': 0, 'statut': 'a_faire',   'priorite': 'critique'},
            {'titre': 'Rapport d\'audit provisoire',          'debut': 78,  'fin': 84,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
            {'titre': 'Rapport final et certification',       'debut': 84,  'fin': 90,  'taux': 0, 'statut': 'a_faire',   'priorite': 'haute'},
        ],
    },
]

# Dépendances entre activités (indices dans TEMPLATES_ACTIVITES)
DEPENDANCES = [
    (0, 1, 'FD', 0),   # Démarrage -> Diagnostic (Fin->Début)
    (1, 2, 'FD', 3),   # Diagnostic -> Formation (+3j)
    (2, 3, 'FD', 0),   # Formation -> Terrain
    (2, 5, 'DD', 0),   # Formation -> S&E (Début->Début)
    (3, 4, 'DD', 5),   # Terrain -> Équipements (+5j)
    (3, 6, 'DD', 0),   # Terrain -> Coordination
    (7, 8, 'FD', 5),   # Infra -> Planification Phase 2 (+5j)
    (8, 9, 'FD', 0),   # Planification -> Audit
]


class Command(BaseCommand):
    help = 'Seed activités et tâches Gantt pour tous les projets actifs'

    def add_arguments(self, parser):
        parser.add_argument('--reset',  action='store_true', help='Supprime et recrée les données Gantt')
        parser.add_argument('--projet', type=str,  default='', help='Code projet spécifique (ex: PROJ-2023-008)')

    def handle(self, *args, **options):
        from programmes_projets.models import Projet
        from accounts.models import User

        if options['reset']:
            self._reset(options['projet'])

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun super-utilisateur. Lancez seed_lot1 d\'abord.'))
            return

        users = list(User.objects.all()[:10])

        # Sélection des projets
        qs = Projet.objects.all()
        if options['projet']:
            qs = qs.filter(code=options['projet'])
        else:
            qs = qs.filter(statut__in=['en_cours', 'planifie', 'en_preparation', 'valide'])

        projets = list(qs)
        if not projets:
            self.stdout.write(self.style.WARNING('[AVERTISSEMENT] Aucun projet trouvé. Vérifie le code ou le statut.'))
            return

        self.stdout.write(f'\n>> Seed Gantt pour {len(projets)} projet(s)…\n')

        with transaction.atomic():
            for projet in projets:
                self.stdout.write(self.style.HTTP_INFO(f'\n-- Projet : [{projet.code}] {projet.titre} --'))
                activites = self._seed_activites(admin, users, projet)
                self._seed_dependances(activites)
                self._seed_taches(admin, users, activites)
                self.stdout.write(
                    self.style.SUCCESS(f'   [OK] {len(activites)} activités + tâches créées')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed Gantt terminé ! Actualisez la page Gantt.'))

    # --- Reset ----------------------------------------------------------------

    def _reset(self, code_projet=''):
        from execution.models import ActiviteExecution, Tache, DependanceActivite, DependanceTache
        from programmes_projets.models import Projet
        self.stdout.write(self.style.WARNING('[RESET] Suppression données Gantt…'))
        if code_projet:
            try:
                projet = Projet.objects.get(code=code_projet)
                DependanceTache.objects.filter(tache_source__activite__projet=projet).delete()
                DependanceActivite.objects.filter(activite_source__projet=projet).delete()
                Tache.objects.filter(activite__projet=projet).delete()
                ActiviteExecution.objects.filter(projet=projet).delete()
                self.stdout.write(f'   Projet {code_projet} nettoyé.')
            except Projet.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'   Projet {code_projet} introuvable.'))
        else:
            DependanceTache.objects.all().delete()
            DependanceActivite.objects.all().delete()
            Tache.objects.all().delete()
            ActiviteExecution.objects.all().delete()
            self.stdout.write('   Toutes les activités/tâches supprimées.')

    # --- Activités ------------------------------------------------------------

    def _seed_activites(self, admin, users, projet):
        from execution.models import ActiviteExecution
        today = date.today()
        programme = getattr(projet, 'programme', None)
        activites = []

        for i, tmpl in enumerate(TEMPLATES_ACTIVITES):
            # Variation légère des dates par projet (évite Gantt identique)
            variation = (projet.id % 5) * 2
            debut = today + timedelta(days=tmpl['debut_delta'] + variation)
            fin   = today + timedelta(days=tmpl['fin_delta']   + variation)

            # Taux d'avancement selon le statut
            taux = tmpl['taux_min']
            if tmpl['statut'] == 'en_cours':
                taux = random.randint(max(10, tmpl['taux_min']), 85)
            elif tmpl['statut'] == 'terminee':
                taux = 100

            responsable = users[(i + projet.id) % len(users)] if users else admin

            code = f"ACT-P{projet.id:03d}-{str(i + 1).zfill(3)}"

            act, created = ActiviteExecution.objects.update_or_create(
                code=code,
                defaults={
                    'intitule':        f"{tmpl['suffix']} -- {projet.titre[:40]}",
                    'description':     tmpl['description'],
                    'projet':          projet,
                    'programme':       programme,
                    'responsable':     responsable,
                    'priorite':        tmpl['priorite'],
                    'statut':          tmpl['statut'],
                    'date_debut_prevue': debut,
                    'date_fin_prevue':   fin,
                    'date_debut_reelle': debut if tmpl['statut'] in ('en_cours', 'terminee', 'suspendue') else None,
                    'date_fin_reelle':   fin   if tmpl['statut'] == 'terminee' else None,
                    'budget_prevu':    random.randint(2, 20) * 500_000,
                    'budget_realise':  random.randint(0, 10) * 500_000 if tmpl['statut'] in ('en_cours', 'terminee') else 0,
                    'taux_avancement': taux,
                    'ordre':           i + 1,
                    'created_by':      admin,
                },
            )
            flag = self.style.SUCCESS('créé') if created else self.style.WARNING('màj')
            self.stdout.write(f'   [{flag}] Activité {code} : {tmpl["suffix"][:50]}')
            activites.append(act)

        return activites

    # --- Dépendances ----------------------------------------------------------

    def _seed_dependances(self, activites):
        from execution.models import DependanceActivite
        created_count = 0
        for idx_src, idx_cible, type_dep, decalage in DEPENDANCES:
            if idx_src >= len(activites) or idx_cible >= len(activites):
                continue
            _, created = DependanceActivite.objects.get_or_create(
                activite_source=activites[idx_src],
                activite_cible=activites[idx_cible],
                defaults={'type_dependance': type_dep, 'decalage_jours': decalage},
            )
            if created:
                created_count += 1
        self.stdout.write(f'   [{self.style.SUCCESS("ok")}] {created_count} dépendances créées')

    # --- Tâches ---------------------------------------------------------------

    def _seed_taches(self, admin, users, activites):
        from execution.models import Tache, ChecklistItem
        today    = date.today()
        nb_total = 0

        CHECKLISTS = {
            'formation':    ['Préparer le matériel pédagogique', 'Réserver la salle', 'Envoyer les convocations', 'Préparer les attestations', 'Produire le rapport'],
            'terrain':      ['Cartographier la zone', 'Préparer les formulaires', 'Briefer l\'équipe', 'Collecter les données', 'Valider les données', 'Transmettre à la base'],
            'administratif':['Rédiger le document', 'Réviser et corriger', 'Valider en interne', 'Soumettre aux partenaires', 'Archiver la version finale'],
        }

        for i, (tmpl, activite) in enumerate(zip(TEMPLATES_ACTIVITES, activites)):
            for j, t_data in enumerate(tmpl.get('taches', [])):
                variation = (activite.projet.id % 3) * 1
                debut  = today + timedelta(days=t_data['debut'] + variation)
                fin    = today + timedelta(days=t_data['fin']   + variation)
                assignee = users[(i + j + activite.projet.id) % len(users)] if users else admin
                code  = f"TCH-{activite.code[4:]}-{str(j + 1).zfill(2)}"

                tache, created = Tache.objects.update_or_create(
                    code=code,
                    defaults={
                        'titre':             t_data['titre'],
                        'activite':          activite,
                        'assignee':          assignee,
                        'priorite':          t_data['priorite'],
                        'statut':            t_data['statut'],
                        'date_debut':        debut,
                        'date_echeance':     fin,
                        'date_completion':   fin if t_data['statut'] == 'terminee' else None,
                        'taux_avancement':   t_data['taux'],
                        'estimation_heures': random.randint(4, 40),
                        'heures_realisees':  int(t_data['taux'] / 100 * random.randint(4, 40)),
                        'ordre':             j + 1,
                        'created_by':        admin,
                    },
                )
                nb_total += 1

                # Checklist selon type d'activité
                if created:
                    if j == 0:
                        cl_key = 'administratif'
                    elif 'formation' in t_data['titre'].lower() or 'curriculum' in t_data['titre'].lower():
                        cl_key = 'formation'
                    elif 'collecte' in t_data['titre'].lower() or 'terrain' in t_data['titre'].lower():
                        cl_key = 'terrain'
                    else:
                        cl_key = 'administratif'

                    for k, item_txt in enumerate(CHECKLISTS[cl_key]):
                        est_coche = t_data['taux'] == 100 or (t_data['taux'] > 50 and k < 3)
                        ChecklistItem.objects.get_or_create(
                            tache=tache,
                            libelle=item_txt,
                            defaults={
                                'coche': est_coche,
                                'ordre': k + 1,
                                'coche_par': admin if est_coche else None,
                                'date_coche': timezone.now() if est_coche else None,
                            }
                        )

        self.stdout.write(f'   [{self.style.SUCCESS("ok")}] {nb_total} tâches créées')
