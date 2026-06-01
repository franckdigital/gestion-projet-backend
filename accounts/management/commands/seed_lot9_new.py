"""
Seed Lot 9 nouveaux modules : Diligences (M42), Evenements (M43), Qualite.
Usage : python manage.py seed_lot9_new
"""
from decimal import Decimal
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed Diligences, Evenements, Qualite"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._seed_diligences()
            self._seed_evenements()
            self._seed_qualite()
        self.stdout.write(self.style.SUCCESS("Lot 9 (nouveaux modules) seede avec succes !"))

    def _get_base(self):
        from accounts.models import User
        from programmes_projets.models import Projet, Programme
        admin = User.objects.filter(is_superuser=True).first()
        projet = Projet.objects.first()
        programme = Programme.objects.first()
        return admin, projet, programme

    # -------------------------------------------------------------------------
    # M42 -- Diligences Administratives
    # -------------------------------------------------------------------------
    def _seed_diligences(self):
        from diligences.models import Diligence, SuiviDiligence, RelanceDiligence
        admin, projet, programme = self._get_base()
        if not admin:
            return

        today = timezone.now().date()
        diligences_data = [
            {
                "titre": "Transmission rapport trimestriel Q1 2026 au bailleur",
                "type_source": "instruction_dg", "priorite": "haute", "statut": "cloturee",
                "source_reference": "NOTE-DG-2026-001",
                "instructions": "Préparer et transmettre le rapport Q1 2026 au bailleur AFD avant le 30 avril 2026. Inclure les données financières, les indicateurs et les photos terrain.",
                "resultat": "Rapport transmis le 28 avril 2026. Accusé de réception reçu.",
                "date_echeance": today - timedelta(days=30),
                "date_cloture": today - timedelta(days=32),
                "taux_avancement": 100,
            },
            {
                "titre": "Mise à jour du registre des risques — Revue mensuelle",
                "type_source": "reunion", "priorite": "normale", "statut": "en_cours",
                "source_reference": "PV-COPIL-2026-05",
                "instructions": "Mettre à jour le registre des risques suite aux décisions du COPIL de mai 2026. Identifier les nouveaux risques et mettre à jour les plans de mitigation existants.",
                "date_echeance": today + timedelta(days=5),
                "taux_avancement": 60,
            },
            {
                "titre": "Préparation audit mi-parcours — Documents à fournir",
                "type_source": "courrier", "priorite": "urgente", "statut": "affectee",
                "source_reference": "COURR-AFD-2026-044",
                "instructions": "Préparer le dossier complet pour l'audit mi-parcours : états financiers, rapports d'activités, PV COPIL, fiches de collecte indicateurs, photos et GPS points.",
                "date_echeance": today + timedelta(days=12),
                "taux_avancement": 25,
            },
            {
                "titre": "Intégration 3 nouveaux agents terrain — Base de données RH",
                "type_source": "note", "priorite": "normale", "statut": "cloturee",
                "source_reference": "NOTE-RH-2026-012",
                "instructions": "Créer les comptes utilisateurs pour les 3 nouveaux agents terrain recrutés (Korhogo, Daloa, Bouaké). Former à l'application mobile.",
                "resultat": "Comptes créés et formation effectuée le 15 mai 2026.",
                "date_echeance": today - timedelta(days=15),
                "date_cloture": today - timedelta(days=15),
                "taux_avancement": 100,
            },
            {
                "titre": "Négociation renouvellement convention ONG partenaire Santé+",
                "type_source": "instruction_dg", "priorite": "haute", "statut": "en_cours",
                "source_reference": "INST-DG-2026-008",
                "instructions": "Engager les négociations pour le renouvellement de la convention avec Santé+ pour la période 2027-2029. Inclure les nouvelles zones d'intervention et les indicateurs.",
                "date_echeance": today + timedelta(days=45),
                "taux_avancement": 30,
            },
            {
                "titre": "Transmission PV COPIL extraordinaire — Ministère tutelle",
                "type_source": "decision", "priorite": "haute", "statut": "cloturee",
                "source_reference": "DEC-COPIL-EXT-001",
                "instructions": "Transmettre le PV de la réunion COPIL extraordinaire du 20 mai 2026 au Ministère de tutelle dans les 5 jours ouvrables.",
                "resultat": "PV transmis et signé pour accusé de réception le 25 mai 2026.",
                "date_echeance": today - timedelta(days=7),
                "date_cloture": today - timedelta(days=6),
                "taux_avancement": 100,
            },
            {
                "titre": "Elaboration plan de communication externe S2 2026",
                "type_source": "instruction_dg", "priorite": "normale", "statut": "ouverte",
                "source_reference": "INST-DG-2026-010",
                "instructions": "Elaborer le plan de communication externe pour le second semestre 2026. Inclure les événements, publications web, rapports publics et relations médias.",
                "date_echeance": today + timedelta(days=30),
                "taux_avancement": 0,
            },
        ]

        for d_data in diligences_data:
            d, created = Diligence.objects.get_or_create(
                titre=d_data["titre"],
                defaults={**d_data, "projet": None, "programme": None,
                           "emetteur": admin, "responsable": admin, "created_by": admin}
            )
            if created and d.statut in ("en_cours", "affectee", "cloturee"):
                SuiviDiligence.objects.get_or_create(
                    diligence=d, auteur=admin,
                    defaults={
                        "date_suivi": today - timedelta(days=3),
                        "avancement": d.taux_avancement,
                        "observations": f"Suivi du {today - timedelta(days=3)} — avancement {d.taux_avancement}%",
                        "actions_realisees": "Vérification des documents requis",
                        "prochaines_etapes": "Finalisation et transmission" if d.statut != "cloturee" else "Clôturée",
                    }
                )
            self.stdout.write(f"  Diligence : {'C' if created else 'E'} -- {d.reference} {d.titre[:50]}")

        self.stdout.write(self.style.SUCCESS("  [OK] Diligences seedees"))

    # -------------------------------------------------------------------------
    # M43 -- Evenements
    # -------------------------------------------------------------------------
    def _seed_evenements(self):
        from evenements.models import Evenement, ParticipantEvenement, DepenseEvenement
        admin, projet, programme = self._get_base()
        if not admin:
            return

        now = timezone.now()
        evenements_data = [
            {
                "titre": "Atelier de lancement officiel PRCC — Phase 2",
                "type_evenement": "atelier", "statut": "termine",
                "description": "Atelier de lancement de la phase 2 du projet avec toutes les parties prenantes nationales et internationales.",
                "objectifs": "Presenter les objectifs de la phase 2, valider le plan de travail et les indicateurs.",
                "ordre_du_jour": "1. Bilan Phase 1\n2. Presentation Phase 2\n3. Plan de travail\n4. Questions-reponses",
                "lieu": "Hotel Ivoire — Abidjan, Salle Lagunes",
                "date_debut": now - timedelta(days=45),
                "date_fin": now - timedelta(days=44),
                "nombre_participants_prevu": 60,
                "budget_prevu": Decimal("4500000"),
                "budget_realise": Decimal("4200000"),
                "avec_inscription": True,
                "avec_evaluation": True,
                "compte_rendu": "Atelier concluant. 57 participants effectifs. Tous les objectifs atteints.",
            },
            {
                "titre": "Formation agents terrain — Application mobile collecte",
                "type_evenement": "formation", "statut": "termine",
                "description": "Formation de 32 agents terrain à l'utilisation de l'application mobile de collecte de données.",
                "objectifs": "Maîtriser l'application mobile, les formulaires KoboToolbox et la synchronisation.",
                "lieu": "Centre de formation ONG-DEMO — Abidjan",
                "date_debut": now - timedelta(days=20),
                "date_fin": now - timedelta(days=18),
                "nombre_participants_prevu": 35,
                "budget_prevu": Decimal("1800000"),
                "budget_realise": Decimal("1650000"),
                "avec_inscription": True,
                "avec_presence_qr": True,
                "avec_evaluation": True,
                "compte_rendu": "32/35 agents formés. Note moyenne évaluation: 8,2/10. Application maîtrisée.",
            },
            {
                "titre": "COPIL Trimestriel — Juin 2026",
                "type_evenement": "reunion", "statut": "confirme",
                "description": "Réunion du Comité de Pilotage trimestriel — bilan Q2 2026 et planification Q3.",
                "objectifs": "Valider les rapports Q2, approuver les ajustements budgétaires, planifier Q3.",
                "ordre_du_jour": "1. Approbation PV COPIL précédent\n2. Point financier Q2\n3. Avancement activités\n4. Points divers",
                "lieu": "Salle de réunion PRCC — Plateau Abidjan",
                "date_debut": now + timedelta(days=5),
                "date_fin": now + timedelta(days=5) + timedelta(hours=4),
                "nombre_participants_prevu": 15,
                "budget_prevu": Decimal("500000"),
                "avec_inscription": False,
            },
            {
                "titre": "Forum régional Eau & Assainissement — Côte d'Ivoire",
                "type_evenement": "forum", "statut": "planifie",
                "description": "Forum national réunissant les acteurs du secteur eau et assainissement.",
                "objectifs": "Partager les expériences, renforcer les partenariats et définir une feuille de route sectorielle 2027-2030.",
                "lieu": "Palais des Congrès — Yamoussoukro",
                "date_debut": now + timedelta(days=30),
                "date_fin": now + timedelta(days=32),
                "nombre_participants_prevu": 200,
                "budget_prevu": Decimal("12000000"),
                "avec_inscription": True,
            },
            {
                "titre": "Séminaire capitalisation — Leçons apprises PRCC",
                "type_evenement": "seminaire", "statut": "planifie",
                "description": "Séminaire interne de capitalisation des connaissances et leçons apprises sur 3 ans de mise en oeuvre.",
                "objectifs": "Documenter les bonnes pratiques, diffuser les leçons apprises, alimenter la bibliothèque institutionnelle.",
                "lieu": "Siège ONG-DEMO — Abidjan Plateau",
                "date_debut": now + timedelta(days=60),
                "date_fin": now + timedelta(days=61),
                "nombre_participants_prevu": 25,
                "budget_prevu": Decimal("2000000"),
                "avec_evaluation": True,
            },
            {
                "titre": "Mission de supervision terrain — Zone Nord",
                "type_evenement": "mission", "statut": "en_cours",
                "description": "Mission de supervision et d'appui technique aux équipes terrain de la zone Nord (Korhogo, Katiola, Bouaké).",
                "objectifs": "Vérifier l'avancement des activités, appuyer les agents, collecter des données photo.",
                "lieu": "Korhogo, Katiola, Bouaké",
                "date_debut": now - timedelta(days=2),
                "date_fin": now + timedelta(days=3),
                "nombre_participants_prevu": 4,
                "budget_prevu": Decimal("850000"),
                "budget_realise": Decimal("320000"),
            },
        ]

        for ev_data in evenements_data:
            ev, created = Evenement.objects.get_or_create(
                titre=ev_data["titre"],
                defaults={**ev_data, "programme": None, "projet": projet,
                           "organisateur": admin, "created_by": admin}
            )
            if created:
                # Ajouter l'admin comme participant
                ParticipantEvenement.objects.get_or_create(
                    evenement=ev, email=admin.email,
                    defaults={
                        "utilisateur": admin,
                        "nom": admin.last_name or "Admin",
                        "prenom": admin.first_name or "Super",
                        "organisation": "ONG-DEMO",
                        "fonction": "Directeur Général",
                        "statut": "present" if ev.statut == "termine" else "confirme",
                    }
                )
                # Ajouter dépenses pour les événements terminés
                if ev.statut == "termine" and ev.budget_realise and ev.budget_realise > 0:
                    DepenseEvenement.objects.get_or_create(
                        evenement=ev, description="Location salle + équipement",
                        defaults={
                            "categorie": "location_salle",
                            "montant": ev.budget_realise * Decimal("0.4"),
                            "fournisseur": "Prestataire événementiel",
                            "date_depense": ev.date_fin.date() if hasattr(ev.date_fin, 'date') else ev.date_fin,
                            "saisi_par": admin,
                        }
                    )
                    DepenseEvenement.objects.get_or_create(
                        evenement=ev, description="Restauration participants",
                        defaults={
                            "categorie": "restauration",
                            "montant": ev.budget_realise * Decimal("0.35"),
                            "fournisseur": "Traiteur local",
                            "date_depense": ev.date_fin.date() if hasattr(ev.date_fin, 'date') else ev.date_fin,
                            "saisi_par": admin,
                        }
                    )
            self.stdout.write(f"  Evenement : {'C' if created else 'E'} -- {ev.titre[:55]}")

        self.stdout.write(self.style.SUCCESS("  [OK] Evenements seedes"))

    # -------------------------------------------------------------------------
    # Qualite (Transverse)
    # -------------------------------------------------------------------------
    def _seed_qualite(self):
        from gestion_qualite.models import NonConformite, ActionQualite, AuditInterne, IndicateurQualite
        admin, projet, programme = self._get_base()
        if not admin:
            return

        today = timezone.now().date()

        # Non-conformites
        ncs_data = [
            {
                "titre": "Retard de transmission des données terrain — agents Zone Nord",
                "type_nc": "processus", "gravite": "majeure", "statut": "cloturee",
                "description": "4 agents de la zone nord ont transmis leurs données avec 7 à 14 jours de retard sur 3 collectes consécutives.",
                "cause_racine": "Manque de supervision directe et de retour de la coordinatrice locale.",
                "impact": "Délai de calcul des indicateurs. Retard dans la prise de décision.",
                "date_detection": today - timedelta(days=60),
                "date_echeance": today - timedelta(days=30),
                "date_cloture": today - timedelta(days=25),
            },
            {
                "titre": "Non-conformité documents financiers — Justificatifs manquants",
                "type_nc": "documentation", "gravite": "majeure", "statut": "en_traitement",
                "description": "Lors du contrôle interne Q1 2026, 12 dépenses (total: 4,2M FCFA) présentent des justificatifs insuffisants ou manquants.",
                "cause_racine": "Absence de procédure écrite pour les achats terrain inférieurs à 500 000 FCFA.",
                "impact": "Risque de rejet par l'auditeur externe. Non-conformité aux procédures AFD.",
                "date_detection": today - timedelta(days=45),
                "date_echeance": today + timedelta(days=15),
            },
            {
                "titre": "Indicateur eau potable — Méthode de mesure non standardisée",
                "type_nc": "processus", "gravite": "mineure", "statut": "cloturee",
                "description": "Deux agents de collecte utilisaient des méthodes différentes pour mesurer le taux d'accès à l'eau potable.",
                "cause_racine": "Guide de collecte pas assez précis sur la définition opérationnelle de l'indicateur.",
                "impact": "Données partiellement incomparables entre les deux zones concernées.",
                "date_detection": today - timedelta(days=90),
                "date_echeance": today - timedelta(days=60),
                "date_cloture": today - timedelta(days=65),
            },
            {
                "titre": "Logiciel de paie — Erreur de calcul cotisations CNPS",
                "type_nc": "service", "gravite": "critique", "statut": "verifiee",
                "description": "Une erreur de paramétrage dans le logiciel de paie a causé une sous-déclaration des cotisations CNPS pour 8 employés sur 3 mois.",
                "cause_racine": "Mise à jour du taux CNPS non répercutée dans le paramétrage logiciel.",
                "impact": "Risque de redressement fiscal. Montant concerné : 1 850 000 FCFA.",
                "date_detection": today - timedelta(days=30),
                "date_echeance": today - timedelta(days=5),
                "date_cloture": today - timedelta(days=3),
            },
        ]
        ncs = []
        for nc_data in ncs_data:
            nc, created = NonConformite.objects.get_or_create(
                titre=nc_data["titre"],
                defaults={**nc_data, "detecte_par": admin, "responsable": admin,
                           "projet": projet}
            )
            ncs.append(nc)
            self.stdout.write(f"  NC : {'C' if created else 'E'} -- {nc.reference} {nc.titre[:50]}")

        # Actions qualite
        if ncs:
            actions_data = [
                {
                    "titre": "Mise en place d'un tableau de bord de suivi des transmissions terrain",
                    "type_action": "corrective", "statut": "cloturee",
                    "description": "Créer un tableau de bord partagé permettant de suivre en temps réel les transmissions des données terrain.",
                    "date_prevue": today - timedelta(days=40),
                    "date_realisation": today - timedelta(days=38),
                    "resultat": "Tableau de bord créé sur Google Sheets, partagé avec toute l'équipe. Remontée des retards réduite à 0.",
                    "efficace": True,
                    "non_conformite": ncs[0] if ncs else None,
                },
                {
                    "titre": "Rédaction procédure achats terrain < 500 000 FCFA",
                    "type_action": "corrective", "statut": "en_cours",
                    "description": "Rédiger et diffuser une procédure claire pour les achats terrain inférieurs à 500 000 FCFA.",
                    "date_prevue": today + timedelta(days=5),
                    "non_conformite": ncs[1] if len(ncs) > 1 else None,
                },
                {
                    "titre": "Formation responsable paie — Paramétrage CNPS",
                    "type_action": "corrective", "statut": "verifiee",
                    "description": "Former le responsable administratif aux mises à jour de paramétrage du logiciel de paie.",
                    "date_prevue": today - timedelta(days=10),
                    "date_realisation": today - timedelta(days=8),
                    "resultat": "Formation effectuée. Corrections rétroactives des 3 mois concernés. Déclaration régularisée CNPS.",
                    "efficace": True,
                    "non_conformite": ncs[3] if len(ncs) > 3 else None,
                },
                {
                    "titre": "Mise à jour guide de collecte indicateurs eau",
                    "type_action": "preventive", "statut": "cloturee",
                    "description": "Mettre à jour le guide de collecte avec les définitions opérationnelles précises pour chaque indicateur.",
                    "date_prevue": today - timedelta(days=70),
                    "date_realisation": today - timedelta(days=72),
                    "resultat": "Guide mis à jour, validé en réunion d'équipe, distribué à tous les agents.",
                    "efficace": True,
                    "non_conformite": ncs[2] if len(ncs) > 2 else None,
                },
                {
                    "titre": "Audit annuel procédures administratives et financières",
                    "type_action": "preventive", "statut": "planifiee",
                    "description": "Planifier un audit interne annuel de toutes les procédures administratives et financières.",
                    "date_prevue": today + timedelta(days=90),
                },
            ]
            for a_data in actions_data:
                a, created = ActionQualite.objects.get_or_create(
                    titre=a_data["titre"],
                    defaults={**a_data, "responsable": admin, "created_by": admin}
                )
                self.stdout.write(f"  Action : {'C' if created else 'E'} -- {a.titre[:50]}")

        # Audits internes
        audits_data = [
            {
                "titre": "Audit des procédures de collecte de données terrain",
                "type_audit": "processus", "statut": "cloture",
                "date_planifiee": today - timedelta(days=90),
                "date_realisation": today - timedelta(days=85),
                "perimetre": "Processus de collecte, saisie et validation des données terrain pour les indicateurs.",
                "criteres": "ISO 9001 — Maîtrise des processus opérationnels.",
                "nb_nc_majeures": 1, "nb_nc_mineures": 2, "nb_observations": 4,
                "rapport": "Audit concluant. 1 NC majeure identifiée (retards transmission), 2 mineures (format données).",
                "conclusions": "Processus globalement maîtrisé. Plan d'action corrective validé.",
            },
            {
                "titre": "Audit financier interne — Exercice 2025",
                "type_audit": "conformite", "statut": "termine",
                "date_planifiee": today - timedelta(days=120),
                "date_realisation": today - timedelta(days=110),
                "perimetre": "Toutes les dépenses de l'exercice 2025 et leur conformité aux procédures bailleurs.",
                "criteres": "Procédures AFD — Manuel opérationnel des projets.",
                "nb_nc_majeures": 2, "nb_nc_mineures": 5, "nb_observations": 8,
                "rapport": "Conformité globalement satisfaisante. Recommandations sur les justificatifs pour petits achats.",
                "conclusions": "Recommandé : renforcer les contrôles sur les achats terrain < 500k FCFA.",
            },
            {
                "titre": "Audit interne système de management qualité — Q2 2026",
                "type_audit": "systeme", "statut": "planifie",
                "date_planifiee": today + timedelta(days=30),
                "perimetre": "Ensemble du SMQ : processus, documents, indicateurs et revues de direction.",
                "criteres": "ISO 9001:2015 — Exigences générales du SMQ.",
            },
        ]
        for aud_data in audits_data:
            aud, created = AuditInterne.objects.get_or_create(
                titre=aud_data["titre"],
                defaults={**aud_data, "auditeur_principal": admin, "projet": projet}
            )
            self.stdout.write(f"  Audit : {'C' if created else 'E'} -- {aud.reference} {aud.titre[:50]}")

        # Indicateurs qualite
        indicateurs_data = [
            {"code": "IQ-001", "intitule": "Taux de transmission données terrain dans les délais", "unite": "%",        "valeur_cible": Decimal("95"), "valeur_actuelle": Decimal("98"), "frequence_mesure": "mensuelle"},
            {"code": "IQ-002", "intitule": "Taux de NC critiques clôturées dans les délais",       "unite": "%",        "valeur_cible": Decimal("100"),"valeur_actuelle": Decimal("100"),"frequence_mesure": "trimestrielle"},
            {"code": "IQ-003", "intitule": "Taux de justificatifs financiers complets",             "unite": "%",        "valeur_cible": Decimal("100"),"valeur_actuelle": Decimal("88"), "frequence_mesure": "mensuelle"},
            {"code": "IQ-004", "intitule": "Satisfaction participants formations",                   "unite": "/10",      "valeur_cible": Decimal("8"),  "valeur_actuelle": Decimal("8.2"),"frequence_mesure": "trimestrielle"},
            {"code": "IQ-005", "intitule": "Nombre d'audits internes planifiés réalisés",           "unite": "audits",   "valeur_cible": Decimal("4"),  "valeur_actuelle": Decimal("2"),  "frequence_mesure": "annuelle"},
            {"code": "IQ-006", "intitule": "Délai moyen de clôture des NC (jours)",                 "unite": "jours",    "valeur_cible": Decimal("30"), "valeur_actuelle": Decimal("22"), "frequence_mesure": "trimestrielle"},
        ]
        for ind_data in indicateurs_data:
            ind, created = IndicateurQualite.objects.get_or_create(
                code=ind_data["code"],
                defaults={**ind_data, "actif": True, "responsable": admin}
            )
            self.stdout.write(f"  IQ : {'C' if created else 'E'} -- {ind.code} {ind.intitule[:45]}")

        self.stdout.write(self.style.SUCCESS("  [OK] Qualite seedee"))
