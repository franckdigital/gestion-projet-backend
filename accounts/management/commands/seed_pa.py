"""
Seed M12 : Programme d'Activités (ProgrammeActivites + ActivitePA).

Crée 2 programmes d'activités (annuel + trimestriel) avec leurs activités
PA hiérarchisées, liées au cadre logique, avec budgets, indicateurs et statuts variés.

Usage : python manage.py seed_pa [--reset]
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


PROGRAMMES_ACTIVITES = [
    # -- Programme Annuel 2026 -------------------------------------------------
    {
        'reference': 'PA-2026-PRCC-001',
        'titre': 'Programme d\'Activités Annuel 2026 – PRCC',
        'periode': 'annuel',
        'annee': 2026,
        'semestre': None, 'trimestre': None, 'mois': None,
        'budget_total': 85000000,
        'statut': 'en_cours',
        'notes': 'Programme annuel principal du PRCC. Couvre les 4 composantes : Santé, Education, AGR, Gouvernance.',
        'activites': [
            # Composante Santé
            {
                'code': 'PA-S01',
                'libelle': 'Renforcement du système de santé communautaire',
                'description': 'Ensemble des activités visant à améliorer les capacités des structures de santé communautaires et des agents de terrain.',
                'statut': 'en_cours',
                'debut_delta': -90, 'fin_delta': 180,
                'budget': 22500000,
                'taux': 42,
                'indicateur': 'Nombre d\'agents de santé formés et opérationnels',
                'cible': '500',
                'unite': 'Agents',
                'valeur': '210',
                'sous_activites': [
                    {
                        'code': 'PA-S01.1',
                        'libelle': 'Formation des agents de santé communautaires – Module Nutrition',
                        'statut': 'en_cours',
                        'debut_delta': -30, 'fin_delta': 15,
                        'budget': 4500000, 'taux': 65,
                        'indicateur': 'Agents formés module nutrition',
                        'cible': '85', 'unite': 'Agents', 'valeur': '55',
                    },
                    {
                        'code': 'PA-S01.2',
                        'libelle': 'Déploiement système de suivi numérique KoboToolbox',
                        'statut': 'terminee',
                        'debut_delta': -60, 'fin_delta': -10,
                        'budget': 3200000, 'taux': 100,
                        'indicateur': 'Districts couverts par le système numérique',
                        'cible': '5', 'unite': 'Districts', 'valeur': '5',
                    },
                    {
                        'code': 'PA-S01.3',
                        'libelle': 'Campagne de vaccination DTP3 – 45 villages',
                        'statut': 'planifiee',
                        'debut_delta': 5, 'fin_delta': 25,
                        'budget': 2800000, 'taux': 0,
                        'indicateur': 'Couverture vaccinale DTP3 (%)',
                        'cible': '90', 'unite': '%', 'valeur': '0',
                    },
                    {
                        'code': 'PA-S01.4',
                        'libelle': 'Construction et réhabilitation de 8 centres de santé',
                        'statut': 'en_cours',
                        'debut_delta': -45, 'fin_delta': 45,
                        'budget': 12000000, 'taux': 48,
                        'indicateur': 'Centres de santé réceptionnés',
                        'cible': '8', 'unite': 'Centres', 'valeur': '0',
                    },
                ],
            },
            # Composante Éducation
            {
                'code': 'PA-E01',
                'libelle': 'Amélioration de l\'accès à l\'éducation et alphabétisation',
                'description': 'Activités de scolarisation et d\'alphabétisation en faveur des enfants déscolarisés et des femmes adultes.',
                'statut': 'en_cours',
                'debut_delta': -60, 'fin_delta': 240,
                'budget': 18000000,
                'taux': 28,
                'indicateur': 'Personnes ayant bénéficié de formations éducatives',
                'cible': '6500',
                'unite': 'Personnes',
                'valeur': '1820',
                'sous_activites': [
                    {
                        'code': 'PA-E01.1',
                        'libelle': 'Programme alphabétisation fonctionnelle – 500 femmes rurales',
                        'statut': 'suspendue',
                        'debut_delta': -20, 'fin_delta': 40,
                        'budget': 7200000, 'taux': 25,
                        'indicateur': 'Femmes ayant achevé le programme',
                        'cible': '500', 'unite': 'Femmes', 'valeur': '125',
                    },
                    {
                        'code': 'PA-E01.2',
                        'libelle': 'Construction et équipement de 5 salles de classe',
                        'statut': 'planifiee',
                        'debut_delta': 30, 'fin_delta': 120,
                        'budget': 6500000, 'taux': 0,
                        'indicateur': 'Salles de classe construites et opérationnelles',
                        'cible': '5', 'unite': 'Salles', 'valeur': '0',
                    },
                    {
                        'code': 'PA-E01.3',
                        'libelle': 'Distribution de kits scolaires – 2000 enfants',
                        'statut': 'terminee',
                        'debut_delta': -55, 'fin_delta': -45,
                        'budget': 4300000, 'taux': 100,
                        'indicateur': 'Enfants ayant reçu un kit scolaire',
                        'cible': '2000', 'unite': 'Enfants', 'valeur': '2000',
                    },
                ],
            },
            # Composante AGR
            {
                'code': 'PA-A01',
                'libelle': 'Développement des activités génératrices de revenus (AGR)',
                'description': 'Structuration des coopératives, formation en entrepreneuriat et appui à l\'accès au financement pour les femmes et les jeunes.',
                'statut': 'en_attente',
                'debut_delta': 10, 'fin_delta': 200,
                'budget': 28500000,
                'taux': 0,
                'indicateur': 'Membres de coopératives ayant amélioré leurs revenus',
                'cible': '1500',
                'unite': 'Personnes',
                'valeur': '0',
                'sous_activites': [
                    {
                        'code': 'PA-A01.1',
                        'libelle': 'Mise en place de 10 coopératives agricoles – Zone Nord',
                        'statut': 'en_attente',
                        'debut_delta': 10, 'fin_delta': 70,
                        'budget': 5800000, 'taux': 0,
                        'indicateur': 'Coopératives opérationnelles',
                        'cible': '10', 'unite': 'Coopératives', 'valeur': '0',
                    },
                    {
                        'code': 'PA-A01.2',
                        'libelle': 'Formation en entrepreneuriat féminin – 300 femmes',
                        'statut': 'planifiee',
                        'debut_delta': 20, 'fin_delta': 80,
                        'budget': 8500000, 'taux': 0,
                        'indicateur': 'Femmes formées en entrepreneuriat',
                        'cible': '300', 'unite': 'Femmes', 'valeur': '0',
                    },
                    {
                        'code': 'PA-A01.3',
                        'libelle': 'Fonds de garantie – 150 micro-crédits accordés',
                        'statut': 'planifiee',
                        'debut_delta': 45, 'fin_delta': 150,
                        'budget': 14200000, 'taux': 0,
                        'indicateur': 'Micro-crédits accordés et remboursés',
                        'cible': '150', 'unite': 'Crédits', 'valeur': '0',
                    },
                ],
            },
            # Composante Gouvernance
            {
                'code': 'PA-G01',
                'libelle': 'Renforcement de la gouvernance locale',
                'description': 'Appui aux collectivités locales et renforcement des capacités des structures communautaires de gouvernance.',
                'statut': 'en_cours',
                'debut_delta': -30, 'fin_delta': 180,
                'budget': 16000000,
                'taux': 15,
                'indicateur': 'Communes bénéficiant d\'un appui à la gouvernance',
                'cible': '45',
                'unite': 'Communes',
                'valeur': '8',
                'sous_activites': [
                    {
                        'code': 'PA-G01.1',
                        'libelle': 'Formation des élus locaux – gouvernance participative',
                        'statut': 'en_cours',
                        'debut_delta': -25, 'fin_delta': 30,
                        'budget': 6000000, 'taux': 35,
                        'indicateur': 'Élus formés à la gouvernance participative',
                        'cible': '180', 'unite': 'Élus', 'valeur': '63',
                    },
                    {
                        'code': 'PA-G01.2',
                        'libelle': 'Appui à l\'élaboration de 15 PDL communaux',
                        'statut': 'planifiee',
                        'debut_delta': 15, 'fin_delta': 120,
                        'budget': 10000000, 'taux': 0,
                        'indicateur': 'Plans de développement locaux adoptés',
                        'cible': '15', 'unite': 'PDL', 'valeur': '0',
                    },
                ],
            },
        ],
    },
    # -- Programme Trimestriel Q2 2026 -----------------------------------------
    {
        'reference': 'PA-2026-Q2-001',
        'titre': 'Programme d\'Activités Q2 2026 – Priorités Opérationnelles',
        'periode': 'trimestriel',
        'annee': 2026,
        'semestre': None, 'trimestre': 2, 'mois': None,
        'budget_total': 24000000,
        'statut': 'en_cours',
        'notes': 'Programme trimestriel centré sur les activités terrain prioritaires du Q2 2026.',
        'activites': [
            {
                'code': 'Q2-01',
                'libelle': 'Finalisation formation agents de santé – 38 agents session 2',
                'description': 'Deuxième session de formation pour les agents des districts Adjamé et Yopougon.',
                'statut': 'planifiee',
                'debut_delta': 8, 'fin_delta': 15,
                'budget': 2200000, 'taux': 0,
                'indicateur': 'Agents formés session 2',
                'cible': '38', 'unite': 'Agents', 'valeur': '0',
                'sous_activites': [],
            },
            {
                'code': 'Q2-02',
                'libelle': 'Conduite campagne vaccination DTP3 – 45 villages',
                'description': 'Déploiement des équipes mobiles de vaccination dans les 45 villages cibles.',
                'statut': 'planifiee',
                'debut_delta': 5, 'fin_delta': 25,
                'budget': 2800000, 'taux': 0,
                'indicateur': 'Villages ayant atteint la couverture cible',
                'cible': '40', 'unite': 'Villages', 'valeur': '0',
                'sous_activites': [],
            },
            {
                'code': 'Q2-03',
                'libelle': 'Supervision construction 8 centres – Visite mi-parcours',
                'description': 'Mission de supervision technique mi-parcours des travaux de construction et réhabilitation.',
                'statut': 'en_cours',
                'debut_delta': -10, 'fin_delta': 20,
                'budget': 3500000, 'taux': 40,
                'indicateur': 'Sites supervisés et conformes',
                'cible': '8', 'unite': 'Sites', 'valeur': '3',
                'sous_activites': [],
            },
            {
                'code': 'Q2-04',
                'libelle': 'Enquête de suivi S1 2026 – 45 villages',
                'description': 'Collecte des données de suivi intermédiaires pour les indicateurs du cadre logique.',
                'statut': 'en_cours',
                'debut_delta': -5, 'fin_delta': 10,
                'budget': 1500000, 'taux': 60,
                'indicateur': 'Fiches bénéficiaires mises à jour',
                'cible': '6000', 'unite': 'Fiches', 'valeur': '3600',
                'sous_activites': [],
            },
            {
                'code': 'Q2-05',
                'libelle': 'Revue à mi-parcours – Préparation et logistique',
                'description': 'Organisation et logistique de la mission de revue à mi-parcours avec la Banque Mondiale.',
                'statut': 'planifiee',
                'debut_delta': 15, 'fin_delta': 25,
                'budget': 8000000, 'taux': 0,
                'indicateur': 'Revue réalisée et rapport disponible',
                'cible': '1', 'unite': 'Rapport', 'valeur': '0',
                'sous_activites': [],
            },
            {
                'code': 'Q2-06',
                'libelle': 'Rapport trimestriel Q2 2026',
                'description': 'Rédaction, validation et transmission du rapport trimestriel Q2 au bailleur.',
                'statut': 'planifiee',
                'debut_delta': 25, 'fin_delta': 35,
                'budget': 500000, 'taux': 0,
                'indicateur': 'Rapport soumis dans les délais',
                'cible': '1', 'unite': 'Rapport', 'valeur': '0',
                'sous_activites': [],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed M12 — Programme d\'Activités (ProgrammeActivites + ActivitePA hierarchisées)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les PA existants avant de re-seeder')

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
            programme = projet.programme

            counts = self._seed_pa(admin, projet, programme)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Seed PA terminé ! {counts[0]} programmes, {counts[1]} activités PA créés.'))

    def _reset(self):
        from planification.models import ProgrammeActivites, ActivitePA
        self.stdout.write(self.style.WARNING('[RESET] Suppression programmes d\'activités…'))
        ActivitePA.objects.all().delete()
        ProgrammeActivites.objects.all().delete()
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

    def _seed_pa(self, admin, projet, programme):
        from planification.models import ProgrammeActivites, ActivitePA
        self.stdout.write('\n>> Programmes d\'activités (M12)…')
        today = date.today()
        nb_pa = nb_act = 0

        for pa_data in PROGRAMMES_ACTIVITES:
            pa, created = ProgrammeActivites.objects.get_or_create(
                reference=pa_data['reference'],
                defaults={
                    'titre':        pa_data['titre'],
                    'periode':      pa_data['periode'],
                    'annee':        pa_data['annee'],
                    'semestre':     pa_data.get('semestre'),
                    'trimestre':    pa_data.get('trimestre'),
                    'mois':         pa_data.get('mois'),
                    'budget_total': pa_data['budget_total'],
                    'statut':       pa_data['statut'],
                    'notes':        pa_data.get('notes', ''),
                    'projet':       projet,
                    'programme':    programme,
                    'valide_par':   admin if pa_data['statut'] not in ('brouillon', 'soumis') else None,
                    'date_validation': timezone.now() if pa_data['statut'] not in ('brouillon', 'soumis') else None,
                    'created_by':   admin,
                }
            )
            self._log('Programme d\'activités', pa, created)
            nb_pa += 1 if created else 0

            if not created:
                continue

            for i, act_data in enumerate(pa_data['activites']):
                d_debut = today + timedelta(days=act_data['debut_delta'])
                d_fin   = today + timedelta(days=act_data['fin_delta'])

                act = ActivitePA.objects.create(
                    programme_activites=pa,
                    code=act_data['code'],
                    libelle=act_data['libelle'],
                    description=act_data.get('description', ''),
                    responsable=admin,
                    date_debut_prevue=d_debut,
                    date_fin_prevue=d_fin,
                    date_debut_reelle=d_debut if act_data['statut'] in ('en_cours', 'terminee', 'suspendue') else None,
                    date_fin_reelle=d_fin if act_data['statut'] == 'terminee' else None,
                    budget_prevu=act_data['budget'],
                    statut=act_data['statut'],
                    taux_avancement=act_data['taux'],
                    indicateur=act_data.get('indicateur', ''),
                    cible=act_data.get('cible', ''),
                    unite_mesure=act_data.get('unite', ''),
                    valeur_realisee=act_data.get('valeur', ''),
                    ordre=i,
                )
                self.stdout.write(f'    + Activité PA: {act.code} — {act.libelle[:55]}')
                nb_act += 1

                for j, sa_data in enumerate(act_data.get('sous_activites', [])):
                    d2 = today + timedelta(days=sa_data['debut_delta'])
                    f2 = today + timedelta(days=sa_data['fin_delta'])
                    sa = ActivitePA.objects.create(
                        programme_activites=pa,
                        parent=act,
                        code=sa_data['code'],
                        libelle=sa_data['libelle'],
                        description='',
                        responsable=admin,
                        date_debut_prevue=d2,
                        date_fin_prevue=f2,
                        date_debut_reelle=d2 if sa_data['statut'] in ('en_cours', 'terminee', 'suspendue') else None,
                        date_fin_reelle=f2 if sa_data['statut'] == 'terminee' else None,
                        budget_prevu=sa_data['budget'],
                        statut=sa_data['statut'],
                        taux_avancement=sa_data['taux'],
                        indicateur=sa_data.get('indicateur', ''),
                        cible=sa_data.get('cible', ''),
                        unite_mesure=sa_data.get('unite', ''),
                        valeur_realisee=sa_data.get('valeur', ''),
                        ordre=j,
                    )
                    self.stdout.write(f'       +-- Sous-act PA: {sa.code} — {sa.libelle[:45]}')
                    nb_act += 1

        return nb_pa, nb_act
