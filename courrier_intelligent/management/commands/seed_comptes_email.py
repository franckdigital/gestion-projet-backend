"""
Seed : Creation des comptes email depuis les variables d'environnement .env
       - Gmail : numerix.digital@gmail.com
       - Hostinger : contact@numerix.digital

Usage : python manage.py seed_comptes_email
Prerequis : seed_lot1 (superuser)
"""
from decouple import config as env_config, UndefinedValueError
from django.core.management.base import BaseCommand
from django.db import transaction


def safe_env(key, default=''):
    try:
        return env_config(key) or default
    except UndefinedValueError:
        return default


class Command(BaseCommand):
    help = "Cree / met a jour les comptes email depuis les variables d'environnement"

    def handle(self, *args, **options):
        from accounts.models import User
        from courrier_intelligent.models import CompteEmail

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stderr.write("Aucun superuser — lancez d'abord seed_lot1")
            return

        comptes_config = [
            # ── Gmail ──────────────────────────────────────────────────────────
            {
                'env_address':  'GMAIL_ADDRESS',
                'env_password': 'GMAIL_APP_PASSWORD',
                'env_nom':      'GMAIL_NOM_AFFICHAGE',
                'defaults': {
                    'type_compte':     'gmail',
                    'nom_affichage':   'Numerix Digital - ERP Gestion Projets',
                    'serveur_entrant': 'imap.gmail.com',
                    'port_entrant':    993,
                    'ssl_entrant':     True,
                    'serveur_sortant': 'smtp.gmail.com',
                    'port_sortant':    587,
                    'ssl_sortant':     False,  # STARTTLS
                    'est_principal':   True,
                    'statut':          'actif',
                },
            },
            # ── Hostinger (contact@numerix.digital) ────────────────────────────
            {
                'env_address':  'HOSTINGER_ADDRESS',
                'env_password': 'HOSTINGER_PASSWORD',
                'env_nom':      'HOSTINGER_NOM_AFFICHAGE',
                'defaults': {
                    'type_compte':     'imap',
                    'nom_affichage':   'Contact Numerix Digital',
                    'serveur_entrant': 'imap.hostinger.com',
                    'port_entrant':    993,
                    'ssl_entrant':     True,
                    'serveur_sortant': 'smtp.hostinger.com',
                    'port_sortant':    587,
                    'ssl_sortant':     False,  # STARTTLS
                    'est_principal':   False,
                    'statut':          'actif',
                },
            },
        ]

        nb_crees = 0
        nb_maj   = 0

        with transaction.atomic():
            for cfg in comptes_config:
                address  = safe_env(cfg['env_address'])
                password = safe_env(cfg['env_password'])
                nom      = safe_env(cfg['env_nom'], cfg['defaults']['nom_affichage'])

                if not address:
                    self.stdout.write(
                        self.style.WARNING(f"  [IGNORE] {cfg['env_address']} non defini dans .env")
                    )
                    continue

                if not password:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [ATTENTION] Mot de passe manquant pour {address} "
                            f"({cfg['env_password']} dans .env)"
                        )
                    )

                compte, created = CompteEmail.objects.get_or_create(
                    adresse_email=address,
                    utilisateur=admin,
                    defaults={
                        **cfg['defaults'],
                        'nom_affichage': nom,
                        'identifiant':   address,
                        'mot_de_passe':  password,
                    }
                )

                if not created:
                    # Mise a jour des champs (sauf si mot de passe vide)
                    for k, v in cfg['defaults'].items():
                        setattr(compte, k, v)
                    compte.nom_affichage = nom
                    compte.identifiant   = address
                    if password:
                        compte.mot_de_passe = password
                    compte.save()

                if created:
                    self.stdout.write(self.style.SUCCESS(f"  [CREE]    {address}"))
                    nb_crees += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  [MAJ]     {address}"))
                    nb_maj += 1

                # Afficher la config
                d = cfg['defaults']
                tls_mode = "STARTTLS" if not d['ssl_sortant'] else "SSL direct"
                self.stdout.write(f"            IMAP : {d['serveur_entrant']}:{d['port_entrant']} (SSL)")
                self.stdout.write(f"            SMTP : {d['serveur_sortant']}:{d['port_sortant']} ({tls_mode})")
                if password:
                    self.stdout.write(f"            Pwd  : {'*' * len(password)}")

        self.stdout.write("")
        self.stdout.write(f"  Comptes crees : {nb_crees}  |  Mis a jour : {nb_maj}")
        self.stdout.write("")
        self.stdout.write("Pour tester toutes les connexions :")
        self.stdout.write("  python manage.py test_email_connexion")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Configuration terminee !"))
