"""
Commande de seed pour le Lot 1 : rôles système + super administrateur.
Usage : python manage.py seed_lot1 [--email admin@erp.ci] [--password Admin@1234]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Role, Permission, User, MODULE


SYSTEM_ROLES = [
    {
        'code': 'super_administrateur',
        'nom': 'Super Administrateur',
        'type_role': 'super_administrateur',
        'est_systeme': True,
        'all_permissions': True,
    },
    {
        'code': 'administrateur',
        'nom': 'Administrateur',
        'type_role': 'administrateur',
        'est_systeme': True,
        'permissions': {
            MODULE.GOUVERNANCE: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                  'peut_valider': True, 'peut_supprimer': True, 'peut_exporter': True, 'peut_imprimer': True},
        },
        'global_read': True,
    },
    {
        'code': 'direction_generale',
        'nom': 'Direction Générale',
        'type_role': 'direction_generale',
        'est_systeme': True,
        'permissions': {
            MODULE.GOUVERNANCE: {'peut_lire': True, 'peut_modifier': False, 'peut_creer': False,
                                  'peut_valider': True, 'peut_supprimer': False, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.PROGRAMMES_PROJETS: {'peut_lire': True, 'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.PLANIFICATION: {'peut_lire': True, 'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.SUIVI_EVALUATION: {'peut_lire': True, 'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.FINANCES: {'peut_lire': True, 'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.BI: {'peut_lire': True, 'peut_exporter': True, 'peut_imprimer': True},
        },
    },
    {
        'code': 'chef_projet',
        'nom': 'Chef Projet',
        'type_role': 'chef_projet',
        'est_systeme': True,
        'permissions': {
            MODULE.PROGRAMMES_PROJETS: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                         'peut_exporter': True, 'peut_imprimer': True},
            MODULE.PLANIFICATION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                    'peut_valider': False, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.EXECUTION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.SUIVI_EVALUATION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                       'peut_exporter': True, 'peut_imprimer': True},
            MODULE.FINANCES: {'peut_lire': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.GED: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True, 'peut_exporter': True},
            MODULE.COLLABORATION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True},
        },
    },
    {
        'code': 'agent_terrain',
        'nom': 'Agent Terrain',
        'type_role': 'agent_terrain',
        'est_systeme': True,
        'permissions': {
            MODULE.EXECUTION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True},
            MODULE.SUIVI_EVALUATION: {'peut_lire': True, 'peut_creer': True},
            MODULE.MOBILE: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True},
            MODULE.GED: {'peut_lire': True},
            MODULE.COLLABORATION: {'peut_lire': True, 'peut_creer': True},
        },
    },
    {
        'code': 'controleur_financier',
        'nom': 'Contrôleur Financier',
        'type_role': 'controleur_financier',
        'est_systeme': True,
        'permissions': {
            MODULE.FINANCES: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                               'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.PROGRAMMES_PROJETS: {'peut_lire': True},
            MODULE.PLANIFICATION: {'peut_lire': True},
            MODULE.MARCHES_PUBLICS: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                      'peut_valider': True},
            MODULE.BI: {'peut_lire': True, 'peut_exporter': True},
        },
    },
    {
        'code': 'responsable_se',
        'nom': 'Responsable S&E',
        'type_role': 'responsable_se',
        'est_systeme': True,
        'permissions': {
            MODULE.SUIVI_EVALUATION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                       'peut_valider': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.PROGRAMMES_PROJETS: {'peut_lire': True},
            MODULE.PLANIFICATION: {'peut_lire': True},
            MODULE.BI: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                        'peut_exporter': True, 'peut_imprimer': True},
            MODULE.CAPITALISATION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True},
        },
    },
    {
        'code': 'gestionnaire_ged',
        'nom': 'Gestionnaire GED',
        'type_role': 'gestionnaire_ged',
        'est_systeme': True,
        'permissions': {
            MODULE.GED: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                          'peut_valider': True, 'peut_supprimer': True, 'peut_exporter': True, 'peut_imprimer': True},
            MODULE.COURRIER_ADMINISTRATIF: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                             'peut_valider': True},
            MODULE.CAPITALISATION: {'peut_lire': True, 'peut_creer': True, 'peut_modifier': True},
        },
    },
    {
        'code': 'lecteur',
        'nom': 'Lecteur',
        'type_role': 'personnalise',
        'est_systeme': True,
        'global_read': True,
    },
]

DEFAULT_PERM = {'peut_lire': False, 'peut_creer': False, 'peut_modifier': False,
                'peut_valider': False, 'peut_supprimer': False, 'peut_exporter': False,
                'peut_imprimer': False}


class Command(BaseCommand):
    help = 'Initialise les rôles système et crée le super-administrateur'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='admin@erp-projets.ci')
        parser.add_argument('--password', default='Admin@2026!')
        parser.add_argument('--force', action='store_true', help='Réinitialiser les permissions')

    def handle(self, *args, **options):
        with transaction.atomic():
            self._create_roles(options['force'])
            self._create_superuser(options['email'], options['password'])

    def _create_roles(self, force):
        for role_data in SYSTEM_ROLES:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'nom': role_data['nom'],
                    'type_role': role_data['type_role'],
                    'est_systeme': role_data.get('est_systeme', False),
                    'actif': True,
                },
            )
            if not created and not force:
                self.stdout.write(f'  Rôle existant : {role.nom}')
                continue

            if force:
                role.permissions.all().delete()

            if role_data.get('all_permissions'):
                for module_code, _ in MODULE.choices:
                    Permission.objects.get_or_create(
                        role=role, module=module_code,
                        defaults={**DEFAULT_PERM,
                                  'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                                  'peut_valider': True, 'peut_supprimer': True,
                                  'peut_exporter': True, 'peut_imprimer': True},
                    )
            elif role_data.get('global_read'):
                for module_code, _ in MODULE.choices:
                    specific = role_data.get('permissions', {}).get(module_code, {})
                    perm = {**DEFAULT_PERM, 'peut_lire': True, **specific}
                    Permission.objects.get_or_create(role=role, module=module_code, defaults=perm)
            else:
                for module_code, perm_data in role_data.get('permissions', {}).items():
                    perm = {**DEFAULT_PERM, **perm_data}
                    Permission.objects.get_or_create(role=role, module=module_code, defaults=perm)

            action = 'Créé' if created else 'Mis à jour'
            self.stdout.write(self.style.SUCCESS(f'  {action} : {role.nom}'))

    def _create_superuser(self, email, password):
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'Super admin existant : {email}')
            return

        super_role = Role.objects.get(code='super_administrateur')
        user = User.objects.create_superuser(
            email=email,
            username='admin',
            first_name='Super',
            last_name='Administrateur',
            password=password,
        )
        user.roles.add(super_role)
        self.stdout.write(self.style.SUCCESS(
            f'\nSuper-administrateur créé :\n  Email    : {email}\n  Password : {password}'
        ))
        self.stdout.write(self.style.WARNING('  [!] Changez ce mot de passe en production !'))
