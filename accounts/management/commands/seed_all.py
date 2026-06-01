"""
Commande maître pour alimenter la base de données de démonstration en un seul appel.
Exécute tous les seeds dans le bon ordre (dépendances respectées).

Lots couverts :
  Lot 1  — Rôles système + Super Administrateur
  Users  — 9 utilisateurs de démonstration
  Lot 2  — Zones d'intervention, Organisation, Programme, Projet
  Lot 3  — Exécution (Activités, Tâches, Livrables, Réunions) + Planification
  Lot 4  — Suivi-Évaluation (Indicateurs, Formulaires, Enquêtes, Cadre résultats)
  Lot 5  — Gestion Financière (Budgets, Dépenses, Conventions, Trésorerie)
  Lot 6  — GED & Archivage (Documents, Dossiers, Boîtes, Bibliothèque)
  Lot 7  — Collaboration, Courrier administratif, Courrier intelligent
  Lot 8  — Risques, Mobile, IA, Business Intelligence
  Lot 9  — Marchés, RH, Logistique, Partenaires, SIG, Événements, Capitalisation
  Extra  — Courriers administratifs, Comptes email

Usage :
  python manage.py seed_all
  python manage.py seed_all --skip lot3 lot4
  python manage.py seed_all --only lot1 users lot2
  python manage.py seed_all --reset-all    (DANGER : vide les tables avant de seeder)
  python manage.py seed_all --dry-run      (affiche l'ordre sans exécuter)
"""
import sys
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


SEED_PIPELINE = [
    # (commande, description, options_extra)
    ('seed_lot1',           'Lot 1  — Rôles + Super Admin',                    {}),
    ('seed_users',          'Users  — Utilisateurs de démonstration',           {}),
    ('seed_lot2',           'Lot 2  — Zones, Organisation, Programme, Projet',  {}),
    ('seed_lot3',           'Lot 3  — Exécution + Planification',               {}),
    ('seed_lot4',           'Lot 4  — Suivi-Évaluation',                        {}),
    ('seed_lot5',           'Lot 5  — Gestion Financière',                      {}),
    ('seed_lot6',           'Lot 6  — GED & Archivage',                         {}),
    ('seed_lot7',           'Lot 7  — Collaboration + Courriers',               {}),
    ('seed_lot8',           'Lot 8  — Risques, Mobile, IA, BI',                 {}),
    ('seed_lot9',           'Lot 9  — Marchés, RH, Logistique, SIG...',         {}),
    ('seed_courrier',       'Extra  — Courriers administratifs (entrants/sortants)', {}),
    ('seed_comptes_email',  'Extra  — Comptes email courrier intelligent',       {}),
]

SEED_KEYS = [cmd for cmd, _, _ in SEED_PIPELINE]


class Command(BaseCommand):
    help = 'Initialise toute la base de données de démonstration (Lots 1 à 9 + extras)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip',
            nargs='+',
            metavar='SEED',
            help=f'Seeds à ignorer. Valeurs possibles : {", ".join(SEED_KEYS)}',
        )
        parser.add_argument(
            '--only',
            nargs='+',
            metavar='SEED',
            help='N\'exécuter que ces seeds (dans l\'ordre de la pipeline)',
        )
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Passe --reset à chaque seed qui le supporte (DANGER : supprime les données existantes)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche la pipeline sans exécuter aucune commande',
        )
        parser.add_argument(
            '--stop-on-error',
            action='store_true',
            default=True,
            help='Arrête la pipeline en cas d\'erreur (comportement par défaut)',
        )
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue la pipeline même en cas d\'erreur sur un seed',
        )

    def handle(self, *args, **options):
        skip  = set(options.get('skip') or [])
        only  = set(options.get('only') or [])
        reset = options['reset_all']
        dry   = options['dry_run']
        stop_on_err = not options.get('continue_on_error', False)

        # Validation des noms de seeds
        invalid = (skip | only) - set(SEED_KEYS)
        if invalid:
            raise CommandError(f'Seeds inconnus : {", ".join(sorted(invalid))}. Valides : {", ".join(SEED_KEYS)}')

        # Construction de la pipeline active
        pipeline = [
            (cmd, desc, opts) for cmd, desc, opts in SEED_PIPELINE
            if (not only or cmd in only) and cmd not in skip
        ]

        self._print_header(pipeline, dry, reset)

        if dry:
            return

        successes, failures = [], []

        for i, (cmd, desc, extra_opts) in enumerate(pipeline, 1):
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO(f'[{i}/{len(pipeline)}] {desc}'))
            self.stdout.write('─' * 60)

            call_kwargs = dict(extra_opts)
            if reset and cmd not in ('seed_lot1',):
                call_kwargs['reset'] = True

            try:
                call_command(cmd, **call_kwargs)
                successes.append(cmd)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {cmd} OK'))
            except Exception as exc:
                failures.append((cmd, str(exc)))
                self.stdout.write(self.style.ERROR(f'  ✗ {cmd} ERREUR : {exc}'))
                if stop_on_err:
                    self.stdout.write(self.style.ERROR('\n[ARRÊT] Pipeline interrompue.'))
                    self._print_summary(successes, failures)
                    sys.exit(1)

        self.stdout.write('')
        self._print_summary(successes, failures)

        if not failures:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('  BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS !'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write('')
            self.stdout.write('  Connexion admin :')
            self.stdout.write('    Email    : admin@erp-projets.ci')
            self.stdout.write('    Password : Admin@2026!')
            self.stdout.write('')
            self.stdout.write('  Utilisateurs démo (mot de passe : Demo@2026!) :')
            demo_users = [
                ('dg@ong-demo.ci',        'Jean-Baptiste Kouamé  — Directeur Général'),
                ('cp@ong-demo.ci',        'Aminata Traoré        — Chef de Projet'),
                ('se@ong-demo.ci',        'Emmanuel Kouassi      — Responsable S&E'),
                ('finance@ong-demo.ci',   'Fatoumata Bamba       — Contrôleur Financier'),
                ('ged@ong-demo.ci',       "Pierre N'Guessan      — Gestionnaire GED"),
                ('terrain1@ong-demo.ci',  'Mariam Koné           — Agente Terrain'),
                ('terrain2@ong-demo.ci',  'Ibrahim Coulibaly     — Agent Terrain'),
                ('logistique@ong-demo.ci','Seydou Diallo         — Responsable Logistique'),
                ('admin@ong-demo.ci',     'Fatou Touré           — Administratrice Système'),
            ]
            for email, label in demo_users:
                self.stdout.write(f'    {email:<30} {label}')
            self.stdout.write(self.style.WARNING('\n  ⚠  Changez les mots de passe en production !'))

    def _print_header(self, pipeline, dry, reset):
        mode = 'DRY-RUN' if dry else ('RESET + SEED' if reset else 'SEED')
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  SEED ALL — {mode}')
        self.stdout.write(f'  {len(pipeline)} seeds dans la pipeline :')
        self.stdout.write('=' * 60)
        for i, (cmd, desc, _) in enumerate(pipeline, 1):
            self.stdout.write(f'  {i:2d}. {desc}')
        self.stdout.write('')

    def _print_summary(self, successes, failures):
        self.stdout.write('')
        self.stdout.write('─' * 60)
        self.stdout.write(f'  RÉSUMÉ : {len(successes)} OK, {len(failures)} erreur(s)')
        if failures:
            self.stdout.write(self.style.ERROR('  Échecs :'))
            for cmd, err in failures:
                self.stdout.write(self.style.ERROR(f'    ✗ {cmd}: {err[:80]}'))
