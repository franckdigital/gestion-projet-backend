"""
Seed Lot 8 : Donnees de demonstration pour M29 a M35
Usage : python manage.py seed_lot8
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Cree les donnees de demonstration pour le Lot 8 (M29-M35)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._seed_m29_risques()
            self._seed_m30_mobile()
            self._seed_m31_m33_ia()
            self._seed_m34_m35_bi()
        self.stdout.write(self.style.SUCCESS("Lot 8 seede avec succes !"))

    # --- M29 : Risques -------------------------------------------------------

    def _seed_m29_risques(self):
        from suivi_evaluation.models import RegistreRisque, PlanMitigation, AlerteRisque
        from accounts.models import User
        from programmes_projets.models import Projet, Programme

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.WARNING("  [M29] Aucun admin trouve — skipping"))
            return

        projet = Projet.objects.first()
        programme = Programme.objects.first()

        risques_data = [
            {
                "intitule": "Retard de financement du bailleur principal",
                "description": "Le bailleur pourrait retarder le decaissement du 2e trimestre.",
                "categorie": "financier",
                "probabilite": 3, "impact": 4,
                "statut": "identifie",
                "tendance": "croissant",
                "causes": "Contraintes budgetaires du bailleur, revue interne en cours.",
                "consequences": "Arret des activites sur le terrain, impossibilite de payer les prestataires.",
                "indicateurs_declenchement": "Absence de virement au 15 du mois, communication formelle de retard.",
            },
            {
                "intitule": "Instabilite politique dans la zone d'intervention",
                "description": "Des tensions politiques dans la region pourraient entraver les deplacements.",
                "categorie": "securitaire",
                "probabilite": 2, "impact": 5,
                "statut": "surveille",
                "tendance": "stable",
                "causes": "Elections locales, mouvements sociaux.",
                "consequences": "Suspension des missions terrain, impossibilite de collecter les donnees.",
                "indicateurs_declenchement": "Alertes securitaires officielles, restrictions de deplacement.",
            },
            {
                "intitule": "Indisponibilite des ressources humaines cles",
                "description": "Le depart non planifie de membres cles pourrait ralentir l'execution.",
                "categorie": "operationnel",
                "probabilite": 3, "impact": 3,
                "statut": "en_cours_traitement",
                "tendance": "stable",
                "causes": "Offres concurrentes, conditions de travail, problemes personnels.",
                "consequences": "Retard dans la realisation des activites, perte de savoir-faire.",
                "indicateurs_declenchement": "Lettres de demission, absenteisme eleve.",
            },
            {
                "intitule": "Perte de donnees suite a une panne serveur",
                "description": "Une defaillance technique majeure du serveur pourrait entrainer une perte de donnees.",
                "categorie": "technique",
                "probabilite": 2, "impact": 4,
                "statut": "mitige",
                "tendance": "decroissant",
                "causes": "Materiel vetuste, coupures d'electricite, absence de maintenance preventive.",
                "consequences": "Perte irreversible des donnees de collecte, interruption des services ERP.",
                "indicateurs_declenchement": "Alertes SMART sur les disques, surchauffe serveur.",
            },
            {
                "intitule": "Changement de reglementation nationale",
                "description": "De nouvelles lois pourraient modifier les conditions d'execution du projet.",
                "categorie": "reglementaire",
                "probabilite": 2, "impact": 3,
                "statut": "identifie",
                "tendance": "stable",
                "causes": "Reforme gouvernementale, nouvelles directives sectorielles.",
                "consequences": "Revision obligatoire des documents contractuels, delais supplementaires.",
            },
        ]

        for data in risques_data:
            risque, created = RegistreRisque.objects.get_or_create(
                intitule=data["intitule"],
                defaults={
                    **data,
                    "programme": programme,
                    "projet": projet,
                    "responsable": admin,
                    "created_by": admin,
                    "date_revue": date.today() + timedelta(days=30),
                }
            )
            label = "Cree" if created else "Existant"
            self.stdout.write(f"  [M29] Risque [{label}] : {risque.reference} — {risque.intitule[:60]}")

            if created:
                PlanMitigation.objects.create(
                    risque=risque,
                    type_mitigation="prevention",
                    description=f"Plan de prevention pour : {risque.intitule[:80]}",
                    responsable=admin,
                    date_debut=date.today(),
                    date_fin=date.today() + timedelta(days=90),
                    cout_estime=500000,
                    statut="en_cours",
                )
                if risque.score_risque >= 12:
                    AlerteRisque.objects.create(
                        risque=risque,
                        niveau="critique",
                        message=(
                            f"ALERTE CRITIQUE: Le risque '{risque.intitule[:60]}'"
                            f" a un score de {risque.score_risque}/25."
                        ),
                        destinataire=admin,
                    )

    # --- M30 : Mobile terrain ------------------------------------------------

    def _seed_m30_mobile(self):
        from mobile_terrain.models import SessionTerrain, CollecteTerrain, PointageTerrain
        from accounts.models import User
        from programmes_projets.models import Projet

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            return

        projet = Projet.objects.first()

        session, created = SessionTerrain.objects.get_or_create(
            agent=admin,
            statut="synchronisee",
            defaults={
                "projet": projet,
                "appareil": "Samsung Galaxy A54",
                "version_app": "2.1.0",
                "mode_hors_ligne": False,
                "nb_collectes": 3,
                "latitude_debut": Decimal("5.3599"),
                "longitude_debut": Decimal("-4.0083"),
                "date_fin": timezone.now() - timedelta(hours=2),
                "date_synchronisation": timezone.now() - timedelta(hours=1),
                "notes": "Session de collecte terrain — Zone Abidjan",
            }
        )
        self.stdout.write(f"  [M30] Session terrain : {'Creee' if created else 'Existante'} — {session}")

        if created:
            collectes = [
                {
                    "type_collecte": "observation",
                    "titre": "Observation beneficiaires zone Cocody",
                    "donnees": {"nb_beneficiaires": 45, "type": "formation", "duree_heures": 3},
                    "valeur_numerique": Decimal("45"),
                    "latitude": Decimal("5.3599"),
                    "longitude": Decimal("-4.0083"),
                    "statut": "synchronise",
                },
                {
                    "type_collecte": "photo",
                    "titre": "Documentation activite terrain",
                    "donnees": {"description": "Photos de la session de formation"},
                    "latitude": Decimal("5.3600"),
                    "longitude": Decimal("-4.0090"),
                    "statut": "synchronise",
                },
                {
                    "type_collecte": "mesure",
                    "titre": "Mesure taux de participation",
                    "donnees": {"inscrits": 50, "presents": 45, "taux": 90},
                    "valeur_numerique": Decimal("90"),
                    "latitude": Decimal("5.3601"),
                    "longitude": Decimal("-4.0085"),
                    "statut": "valide",
                },
            ]
            for c_data in collectes:
                CollecteTerrain.objects.create(
                    session=session,
                    date_collecte_locale=timezone.now() - timedelta(hours=3),
                    **c_data,
                )
            self.stdout.write(f"  [M30] {len(collectes)} collectes creees")

            PointageTerrain.objects.get_or_create(
                agent=admin,
                type_pointage="presence",
                defaults={
                    "projet": projet,
                    "date_heure": timezone.now() - timedelta(hours=4),
                    "latitude": Decimal("5.3599"),
                    "longitude": Decimal("-4.0083"),
                    "precision_gps": Decimal("5.5"),
                    "adresse_geo": "Cocody, Abidjan, Cote d'Ivoire",
                    "valide": True,
                    "valide_par": admin,
                    "notes": "Pointage debut de mission terrain",
                }
            )
            self.stdout.write("  [M30] Pointage terrain cree")

    # --- M31-M33 : Intelligence Artificielle ---------------------------------

    def _seed_m31_m33_ia(self):
        from intelligence_artificielle.models import (
            ConversationIA, MessageIA, GenerationDocument,
            ModeleIA, AnalyseIAPredictive, AlerteIA, RecommandationIA, JournalIA,
        )
        from accounts.models import User
        from programmes_projets.models import Projet, Programme

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            return

        projet = Projet.objects.first()
        programme = Programme.objects.first()

        # Conversation de demo
        conv, created = ConversationIA.objects.get_or_create(
            utilisateur=admin,
            titre="Analyse performance programmes — Demo",
            defaults={
                "contexte": "projet",
                "projet": projet,
                "programme": programme,
            }
        )
        if created:
            MessageIA.objects.create(
                conversation=conv, role="user",
                contenu="Quels sont les projets en retard ?",
            )
            MessageIA.objects.create(
                conversation=conv, role="assistant",
                contenu=(
                    "Selon les donnees actuelles, 2 projets presentent des retards. "
                    "Je vous recommande de consulter le tableau de bord Execution pour les details."
                ),
                tokens_utilises=45, duree_traitement_ms=120, confiance=88,
            )
        self.stdout.write(f"  [M31] Conversation IA : {'Creee' if created else 'Existante'}")

        # Modeles IA predefinis
        modeles_data = [
            {
                "nom": "Prevision Budgetaire ERP",
                "type_modele": "prevision_budget",
                "description": "Modele de prevision des consommations budgetaires par regression lineaire.",
                "version": "1.2", "precision": Decimal("87.5"),
            },
            {
                "nom": "Detecteur de Retards",
                "type_modele": "detection_retard",
                "description": "Detecte les activites a risque de depassement de delai.",
                "version": "2.0", "precision": Decimal("92.3"),
            },
            {
                "nom": "Detecteur d'Anomalies Financieres",
                "type_modele": "detection_anomalie",
                "description": "Identifie les transactions suspectes ou incoherentes.",
                "version": "1.1", "precision": Decimal("78.9"),
            },
            {
                "nom": "Prevision Indicateurs S&E",
                "type_modele": "prevision_indicateur",
                "description": "Predit l'evolution future des indicateurs de performance.",
                "version": "1.0", "precision": Decimal("81.0"),
            },
        ]
        for m_data in modeles_data:
            modele, created = ModeleIA.objects.get_or_create(
                nom=m_data["nom"],
                defaults={**m_data, "statut": "actif", "nb_executions": 0}
            )
            self.stdout.write(
                f"  [M33] Modele IA : {'Cree' if created else 'Existant'} — {modele.nom}"
            )

        # Generation documentaire de demo
        gen, created = GenerationDocument.objects.get_or_create(
            titre="TDR Evaluation Mi-Parcours — PRCC",
            defaults={
                "type_document": "tdr",
                "mode": "generation",
                "langue": "fr",
                "projet": projet,
                "programme": programme,
                "instructions": "Generer les termes de reference pour l'evaluation mi-parcours du programme.",
                "statut": "complete",
                "score_qualite": Decimal("78.0"),
                "tokens_utilises": 1250,
                "contenu_genere": (
                    "TERMES DE REFERENCE\n\n"
                    "1. CONTEXTE\nLe programme vise le renforcement des capacites.\n\n"
                    "2. OBJECTIFS\nEvaluer la pertinence, l'efficacite et l'efficience.\n\n"
                    "3. METHODOLOGIE\nRevue documentaire, entretiens, visites terrain.\n\n"
                    "4. LIVRABLES\nRapport d'evaluation, recommandations, plan d'action."
                ),
                "demande_par": admin,
                "completed_at": timezone.now() - timedelta(days=5),
            }
        )
        self.stdout.write(f"  [M32] Generation doc : {'Creee' if created else 'Existante'}")

        # Analyse predictive de demo
        analyse, created = AnalyseIAPredictive.objects.get_or_create(
            type_analyse="detection_retard",
            projet=projet,
            statut="complete",
            defaults={
                "previsions": [
                    {
                        "activites_en_retard": 3,
                        "details": [{"titre": "Formation agents", "date_fin_prevue": str(date.today() - timedelta(days=15))}],
                    }
                ],
                "anomalies": [],
                "suggestions_ia": "3 activites sont en retard. Revision du planning recommandee.",
                "score_confiance": Decimal("85.0"),
                "demande_par": admin,
                "completed_at": timezone.now() - timedelta(days=2),
            }
        )
        if created:
            AlerteIA.objects.create(
                analyse=analyse,
                type_alerte="retard_prevu",
                niveau="warning",
                titre="3 activites en retard detectees",
                message="L'analyse predictive a identifie 3 activites depassant leur date de fin prevue.",
                destinataire=admin,
            )
            RecommandationIA.objects.create(
                analyse=analyse,
                type_recommandation="revision_calendrier",
                titre="Reviser le planning des activites en retard",
                description=(
                    "Reprogrammer les 3 activites en retard "
                    "et allouer des ressources supplementaires."
                ),
                justification=(
                    "Un retard de plus de 15 jours sur des activites critiques "
                    "affecte le taux d'avancement global."
                ),
                priorite=3,
                projet=projet,
            )
        self.stdout.write(f"  [M33] Analyse predictive : {'Creee' if created else 'Existante'}")

        JournalIA.objects.get_or_create(
            type_action="analyse_predictive",
            utilisateur=admin,
            objet_type="AnalyseIAPredictive",
            defaults={
                "description": "Analyse predictive de demonstration",
                "resultats_sortie": {"nb_retards": 3},
                "tokens_utilises": 500,
                "duree_ms": 1200,
                "succes": True,
            }
        )

    # --- M34-M35 : Business Intelligence -------------------------------------

    def _seed_m34_m35_bi(self):
        from business_intelligence.models import (
            TableauBord, WidgetTableauBord,
            RapportBI, ConnecteurBI, KPIPersonnalise,
        )
        from accounts.models import User
        from programmes_projets.models import Projet, Programme

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            return

        projet = Projet.objects.first()
        programme = Programme.objects.first()

        tableaux_bord_data = [
            {
                "nom": "Dashboard Direction Generale",
                "type_dashboard": "direction_generale",
                "description": "Vue 360 pour la direction — KPIs strategiques, risques, alertes.",
                "est_public": True, "est_defaut": True,
            },
            {
                "nom": "Dashboard Chef de Projet",
                "type_dashboard": "chef_projet",
                "description": "Vue operationnelle — activites, taches, livrables, reunions.",
                "est_public": True, "est_defaut": True,
            },
            {
                "nom": "Dashboard Finance",
                "type_dashboard": "finance",
                "description": "Suivi budgetaire — depenses, decaissements, tresorerie.",
                "est_public": True, "est_defaut": True,
            },
            {
                "nom": "Dashboard Suivi & Evaluation",
                "type_dashboard": "suivi_evaluation",
                "description": "Performance indicateurs — resultats, effets, impact.",
                "est_public": True, "est_defaut": True,
            },
        ]

        for tb_data in tableaux_bord_data:
            tb, created = TableauBord.objects.get_or_create(
                nom=tb_data["nom"],
                defaults={**tb_data, "proprietaire": admin, "actif": True}
            )
            self.stdout.write(f"  [M34] Tableau de bord : {'Cree' if created else 'Existant'} — {tb.nom}")
            if created:
                self._creer_widgets_defaut(tb, tb_data["type_dashboard"], projet, programme)

        # Connecteurs BI
        connecteurs_data = [
            {
                "nom": "Power BI Corporate",
                "type_outil": "powerbi",
                "url_endpoint": "https://api.powerbi.com/v1.0/myorg/",
                "statut": "actif",
            },
            {
                "nom": "Metabase Analytics",
                "type_outil": "metabase",
                "url_endpoint": "http://metabase.ong-demo.ci",
                "statut": "inactif",
            },
        ]
        for c_data in connecteurs_data:
            conn, created = ConnecteurBI.objects.get_or_create(
                nom=c_data["nom"],
                defaults={**c_data, "cree_par": admin}
            )
            self.stdout.write(f"  [M35] Connecteur BI : {'Cree' if created else 'Existant'} — {conn.nom}")

        # KPIs personnalises
        kpis_data = [
            {
                "nom": "Projets actifs",
                "description": "Nombre de projets actuellement en cours",
                "formule": "Projet.objects.filter(statut='en_cours').count()",
                "source_donnees": "programmes_projets",
                "unite": "nombre",
                "icone": "FolderKanban",
                "couleur": "#0ea5e9",
            },
            {
                "nom": "Programmes actifs",
                "description": "Nombre de programmes en cours",
                "formule": "Programme.objects.filter(statut='en_cours').count()",
                "source_donnees": "programmes_projets",
                "unite": "nombre",
                "icone": "Layers",
                "couleur": "#6366f1",
            },
            {
                "nom": "Taux execution global",
                "description": "Taux moyen d'avancement de tous les projets actifs",
                "formule": "Projet.objects.filter(statut='en_cours').count()",
                "source_donnees": "programmes_projets",
                "unite": "pourcentage",
                "icone": "TrendingUp",
                "couleur": "#10b981",
            },
        ]
        for kpi_data in kpis_data:
            kpi, created = KPIPersonnalise.objects.get_or_create(
                nom=kpi_data["nom"],
                defaults={**kpi_data, "cree_par": admin, "actif": True}
            )
            self.stdout.write(f"  [M35] KPI : {'Cree' if created else 'Existant'} — {kpi.nom}")

        # Rapport BI de demo
        rapport, created = RapportBI.objects.get_or_create(
            titre="Rapport Executif Mensuel — Juin 2026",
            defaults={
                "type_rapport": "rapport_executif",
                "periode": "mensuel",
                "format_export": "pdf",
                "statut": "publie",
                "date_debut_periode": date(2026, 6, 1),
                "date_fin_periode": date(2026, 6, 30),
                "programme": programme,
                "genere_par": admin,
                "genere_par_ia": True,
                "donnees_calculees": {
                    "programmes_actifs": 1,
                    "projets_actifs": 1,
                    "taux_realisation_moyen": 68.5,
                    "risques_critiques": 2,
                    "genere_le": str(timezone.now()),
                }
            }
        )
        self.stdout.write(f"  [M35] Rapport BI : {'Cree' if created else 'Existant'} — {rapport.titre}")

    def _creer_widgets_defaut(self, tb, role, projet, programme):
        from business_intelligence.models import WidgetTableauBord

        widgets_par_role = {
            "direction_generale": [
                {
                    "titre": "Programmes actifs", "type_widget": "kpi_card",
                    "source_donnees": "programmes_projets",
                    "configuration": {"metrique": "projets_actifs", "icone": "Shield", "couleur": "#6366f1"},
                    "colonne": 0, "ligne": 0, "largeur": 3, "hauteur": 2,
                },
                {
                    "titre": "Risques critiques", "type_widget": "kpi_card",
                    "source_donnees": "risques",
                    "configuration": {"metrique": "risques_critiques", "icone": "AlertTriangle", "couleur": "#ef4444"},
                    "colonne": 3, "ligne": 0, "largeur": 3, "hauteur": 2,
                },
                {
                    "titre": "Performance indicateurs", "type_widget": "graphique_barres",
                    "source_donnees": "suivi_evaluation",
                    "configuration": {"metrique": "taux_realisation_moyen"},
                    "colonne": 6, "ligne": 0, "largeur": 6, "hauteur": 4,
                },
                {
                    "titre": "Matrice des risques", "type_widget": "risques",
                    "source_donnees": "risques",
                    "configuration": {},
                    "colonne": 0, "ligne": 2, "largeur": 6, "hauteur": 4,
                },
            ],
            "chef_projet": [
                {
                    "titre": "Activites en cours", "type_widget": "kpi_card",
                    "source_donnees": "execution",
                    "configuration": {"icone": "Zap", "couleur": "#f59e0b"},
                    "colonne": 0, "ligne": 0, "largeur": 3, "hauteur": 2,
                },
                {
                    "titre": "Taches et Livrables", "type_widget": "liste_taches",
                    "source_donnees": "execution",
                    "configuration": {},
                    "colonne": 0, "ligne": 2, "largeur": 6, "hauteur": 5,
                },
                {
                    "titre": "Diagramme Gantt", "type_widget": "gantt",
                    "source_donnees": "planification",
                    "configuration": {},
                    "colonne": 6, "ligne": 0, "largeur": 6, "hauteur": 6,
                },
            ],
            "finance": [
                {
                    "titre": "Budget prevu", "type_widget": "kpi_card",
                    "source_donnees": "gestion_financiere",
                    "configuration": {"metrique": "budget_total", "icone": "DollarSign", "couleur": "#ef4444"},
                    "colonne": 0, "ligne": 0, "largeur": 4, "hauteur": 2,
                },
                {
                    "titre": "Evolution budgetaire", "type_widget": "graphique_lignes",
                    "source_donnees": "gestion_financiere",
                    "configuration": {"metrique": "evolution_mensuelle"},
                    "colonne": 0, "ligne": 2, "largeur": 12, "hauteur": 4,
                },
            ],
            "suivi_evaluation": [
                {
                    "titre": "Indicateurs atteints", "type_widget": "kpi_card",
                    "source_donnees": "suivi_evaluation",
                    "configuration": {"metrique": "indicateurs_atteints", "icone": "BarChart2", "couleur": "#8b5cf6"},
                    "colonne": 0, "ligne": 0, "largeur": 4, "hauteur": 2,
                },
                {
                    "titre": "Taux de realisation moyen", "type_widget": "graphique_jauge",
                    "source_donnees": "suivi_evaluation",
                    "configuration": {"metrique": "taux_realisation_moyen"},
                    "colonne": 4, "ligne": 0, "largeur": 4, "hauteur": 3,
                },
                {
                    "titre": "Carte des interventions", "type_widget": "carte_sig",
                    "source_donnees": "suivi_evaluation",
                    "configuration": {},
                    "colonne": 0, "ligne": 3, "largeur": 12, "hauteur": 5,
                },
            ],
        }

        widgets = widgets_par_role.get(role, [])
        for i, w_data in enumerate(widgets):
            WidgetTableauBord.objects.get_or_create(
                tableau_bord=tb,
                titre=w_data["titre"],
                defaults={
                    **w_data,
                    "filtre_projet": projet,
                    "filtre_programme": programme,
                    "ordre": i,
                    "actif": True,
                }
            )
        self.stdout.write(f"    -> {len(widgets)} widget(s) cree(s) pour {tb.nom}")
