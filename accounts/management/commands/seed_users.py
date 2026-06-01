"""
Seed utilisateurs de démonstration pour le programme PRCC.
Crée 9 profils réalistes avec rôles, assignation projet et données de base.

Usage : python manage.py seed_users [--reset]
"""
from django.core.management.base import BaseCommand
from django.db import transaction


DEMO_USERS = [
    {
        'email': 'dg@ong-demo.ci',
        'username': 'dg_kouan',
        'first_name': 'Jean-Baptiste',
        'last_name': 'Kouamé',
        'password': 'Demo@2026!',
        'role_code': 'direction_generale',
        'telephone': '+225 07 07 11 22 33',
        'poste': 'Directeur Général',
        'departement': 'Direction Générale',
        'role_projet': 'superviseur',
    },
    {
        'email': 'cp@ong-demo.ci',
        'username': 'traore_aminata',
        'first_name': 'Aminata',
        'last_name': 'Traoré',
        'password': 'Demo@2026!',
        'role_code': 'chef_projet',
        'telephone': '+225 07 07 44 55 66',
        'poste': 'Chef de Projet PRCC',
        'departement': 'Coordination de Projet',
        'role_projet': 'chef_projet',
    },
    {
        'email': 'se@ong-demo.ci',
        'username': 'kouassi_emmanuel',
        'first_name': 'Emmanuel',
        'last_name': 'Kouassi',
        'password': 'Demo@2026!',
        'role_code': 'responsable_se',
        'telephone': '+225 07 07 77 88 99',
        'poste': 'Responsable Suivi-Évaluation',
        'departement': 'Suivi-Évaluation',
        'role_projet': 'responsable_se',
    },
    {
        'email': 'finance@ong-demo.ci',
        'username': 'bamba_fatoumata',
        'first_name': 'Fatoumata',
        'last_name': 'Bamba',
        'password': 'Demo@2026!',
        'role_code': 'controleur_financier',
        'telephone': '+225 07 07 00 11 22',
        'poste': 'Contrôleur Financier',
        'departement': 'Direction Financière',
        'role_projet': 'membre',
    },
    {
        'email': 'ged@ong-demo.ci',
        'username': 'nguessan_pierre',
        'first_name': 'Pierre',
        'last_name': "N'Guessan",
        'password': 'Demo@2026!',
        'role_code': 'gestionnaire_ged',
        'telephone': '+225 07 07 33 44 55',
        'poste': 'Gestionnaire GED & Archives',
        'departement': 'Gestion de l\'Information',
        'role_projet': 'membre',
    },
    {
        'email': 'terrain1@ong-demo.ci',
        'username': 'kone_mariam',
        'first_name': 'Mariam',
        'last_name': 'Koné',
        'password': 'Demo@2026!',
        'role_code': 'agent_terrain',
        'telephone': '+225 07 07 66 77 88',
        'poste': 'Agente de Terrain — Composante Santé',
        'departement': 'Terrain & Opérations',
        'role_projet': 'membre',
    },
    {
        'email': 'terrain2@ong-demo.ci',
        'username': 'coulibaly_ibrahim',
        'first_name': 'Ibrahim',
        'last_name': 'Coulibaly',
        'password': 'Demo@2026!',
        'role_code': 'agent_terrain',
        'telephone': '+225 07 07 99 00 11',
        'poste': 'Agent de Terrain — Composante AGR',
        'departement': 'Terrain & Opérations',
        'role_projet': 'membre',
    },
    {
        'email': 'logistique@ong-demo.ci',
        'username': 'diallo_seydou',
        'first_name': 'Seydou',
        'last_name': 'Diallo',
        'password': 'Demo@2026!',
        'role_code': 'lecteur',
        'telephone': '+225 07 07 22 33 44',
        'poste': 'Responsable Logistique',
        'departement': 'Logistique & Approvisionnement',
        'role_projet': 'membre',
    },
    {
        'email': 'admin@ong-demo.ci',
        'username': 'toure_fatou',
        'first_name': 'Fatou',
        'last_name': 'Touré',
        'password': 'Demo@2026!',
        'role_code': 'administrateur',
        'telephone': '+225 07 07 55 66 77',
        'poste': 'Administratrice Système',
        'departement': 'Direction des Systèmes d\'Information',
        'role_projet': 'membre',
    },
]


class Command(BaseCommand):
    help = 'Crée les utilisateurs de démonstration avec leurs rôles'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les utilisateurs démo avant de re-seeder')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            users = self._create_users()
            self._assign_to_project(users)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(users)} utilisateurs créés/vérifiés !'))
        self.stdout.write('  Mot de passe commun : Demo@2026! (à changer en production)')

    def _reset(self):
        from accounts.models import User
        emails = [u['email'] for u in DEMO_USERS]
        n, _ = User.objects.filter(email__in=emails).delete()
        self.stdout.write(self.style.WARNING(f'[RESET] {n} utilisateurs supprimés'))

    def _create_users(self):
        from accounts.models import User, Role
        result = []
        for data in DEMO_USERS:
            if User.objects.filter(email=data['email']).exists():
                user = User.objects.get(email=data['email'])
                self.stdout.write(self.style.WARNING(f'  [Existe] {data["email"]}'))
            else:
                user = User.objects.create_user(
                    email=data['email'],
                    username=data['username'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    password=data['password'],
                    telephone=data.get('telephone', ''),
                    poste=data.get('poste', ''),
                    fonction=data.get('departement', ''),
                    is_active=True,
                )
                try:
                    role = Role.objects.get(code=data['role_code'])
                    user.roles.add(role)
                except Role.DoesNotExist:
                    pass
                self.stdout.write(self.style.SUCCESS(f'  [Créé] {user.get_full_name()} ({data["email"]}) — {data["role_code"]}'))
            result.append(user)
        return result

    def _assign_to_project(self, users):
        from programmes_projets.models import Projet, MembreEquipeProjet
        projet = Projet.objects.filter(statut='en_cours').first()
        if not projet:
            return
        for user, data in zip(users, DEMO_USERS):
            MembreEquipeProjet.objects.get_or_create(
                projet=projet,
                user=user,
                defaults={'role_projet': data.get('role_projet', 'membre')},
            )
        self.stdout.write(f'  Membres affectés au projet : {projet.code}')
