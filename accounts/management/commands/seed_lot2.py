"""
Seed Lot 2 : zones d'intervention, organisation démo, programme et projet exemples.
Usage : python manage.py seed_lot2
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_date


ZONES = [
    {'code': 'ABJ', 'nom': 'Abidjan', 'pays': "Côte d'Ivoire", 'region': 'Lagunes'},
    {'code': 'BKO', 'nom': 'Bouaké', 'pays': "Côte d'Ivoire", 'region': 'Vallée du Bandama'},
    {'code': 'MAN', 'nom': 'Man', 'pays': "Côte d'Ivoire", 'region': 'Montagnes'},
    {'code': 'KOR', 'nom': 'Korhogo', 'pays': "Côte d'Ivoire", 'region': 'Savanes'},
    {'code': 'SAN', 'nom': 'San Pedro', 'pays': "Côte d'Ivoire", 'region': 'Bas-Sassandra'},
    {'code': 'NAT', 'nom': 'National', 'pays': "Côte d'Ivoire", 'region': 'Tout le territoire'},
]


class Command(BaseCommand):
    help = 'Crée les données de démonstration pour le Lot 2'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._create_zones()
            self._create_demo_data()

    def _create_zones(self):
        from programmes_projets.models import ZoneIntervention
        for z in ZONES:
            obj, created = ZoneIntervention.objects.get_or_create(code=z['code'], defaults=z)
            status = 'Cree' if created else 'Existant'
            self.stdout.write(f'  Zone [{status}] : {obj.nom}')

    def _create_demo_data(self):
        from accounts.models import User
        from gouvernance.models import Organisation
        from programmes_projets.models import (
            ZoneIntervention, Programme, ObjectifProgramme, Projet,
            MembreEquipeProjet, LivrableProjet, JalonProjet
        )

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.WARNING('Aucun admin - skipping demo data'))
            return

        # Organisation de demo
        org, _ = Organisation.objects.get_or_create(
            sigle='ONG-DEMO',
            defaults={
                'nom': 'ONG Démonstration ERP',
                'type_organisation': 'ong',
                'pays': "Côte d'Ivoire",
                'ville': 'Abidjan',
                'email': 'contact@ong-demo.ci',
            }
        )
        self.stdout.write(f'  Organisation : {org}')

        # Programme de demo
        prog, created = Programme.objects.get_or_create(
            code='PROG-2026-001',
            defaults={
                'intitule': 'Programme de Renforcement des Capacités Communautaires',
                'acronyme': 'PRCC',
                'description': 'Programme visant le renforcement des capacités des communautés locales dans les domaines de la santé, l\'éducation et le développement économique.',
                'organisation': org,
                'coordonnateur': admin,
                'responsable': admin,
                'date_debut': parse_date('2026-01-01'),
                'date_fin': parse_date('2028-12-31'),
                'budget_total': 500000000,
                'devise': 'XOF',
                'statut': 'en_cours',
                'created_by': admin,
                'contexte': 'Contexte socio-économique nécessitant un renforcement des capacités locales.',
            }
        )
        if created:
            zones = ZoneIntervention.objects.filter(code__in=['ABJ', 'BKO', 'NAT'])
            prog.zones_intervention.set(zones)

            for i, (type_obj, libelle) in enumerate([
                ('strategique', 'Renforcer les capacités des communautés en matière de santé'),
                ('strategique', 'Améliorer l\'accès à l\'éducation de qualité'),
                ('specifique', 'Former 500 agents de santé communautaires'),
                ('resultat', 'Réduction de 20% de la mortalité infantile'),
            ], 1):
                ObjectifProgramme.objects.create(
                    programme=prog, type_objectif=type_obj,
                    code=f'OS-{i:02d}', libelle=libelle, ordre=i
                )

        self.stdout.write(f'  Programme : {prog.code}')

        # Projet de demo
        projet, created = Projet.objects.get_or_create(
            code='PROJ-2026-001',
            defaults={
                'titre': 'Projet Santé Communautaire Abidjan',
                'description': 'Renforcement du système de santé communautaire dans le district d\'Abidjan.',
                'programme': prog,
                'organisation': org,
                'chef_projet': admin,
                'date_debut': parse_date('2026-03-01'),
                'date_fin_prevue': parse_date('2027-02-28'),
                'budget_initial': 150000000,
                'devise': 'XOF',
                'priorite': 'haute',
                'statut': 'en_cours',
                'taux_avancement': 25,
                'created_by': admin,
            }
        )

        if created:
            from programmes_projets.models import ZoneIntervention
            projet.zones_intervention.set(ZoneIntervention.objects.filter(code='ABJ'))

            MembreEquipeProjet.objects.get_or_create(
                projet=projet, user=admin,
                defaults={'role_projet': 'chef_projet'}
            )
            LivrableProjet.objects.create(
                projet=projet, code='L-001',
                titre='Rapport de démarrage', type_livrable='rapport',
                date_prevue=parse_date('2026-04-30'), statut='valide',
            )
            LivrableProjet.objects.create(
                projet=projet, code='L-002',
                titre='Formation agents de santé', type_livrable='formation',
                date_prevue=parse_date('2026-09-30'), statut='planifie',
            )
            JalonProjet.objects.create(
                projet=projet, libelle='Démarrage effectif',
                date_prevue=parse_date('2026-03-01'), statut='atteint',
            )
            JalonProjet.objects.create(
                projet=projet, libelle='Première revue trimestrielle',
                date_prevue=parse_date('2026-06-30'), statut='a_venir',
            )

        self.stdout.write(f'  Projet : {projet.code}')
        self.stdout.write(self.style.SUCCESS('\nSeed Lot 2 termine avec succes !'))
