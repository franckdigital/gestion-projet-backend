"""
Seed Lot 9 : Donnees de demonstration pour M36-M45
Usage : python manage.py seed_lot9
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Cree les donnees de demonstration pour le Lot 9 (M36-M45)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._seed_m36_marches()
            self._seed_m37_rh()
            self._seed_m38_logistique()
            self._seed_m39_m40_partenaires()
            self._seed_m41_sig()
            self._seed_m43_evenements()
            self._seed_m45_capitalisation()
        self.stdout.write(self.style.SUCCESS("Lot 9 seede avec succes !"))

    def _get_admin_projet_programme(self):
        from accounts.models import User
        from programmes_projets.models import Projet, Programme
        admin = User.objects.filter(is_superuser=True).first()
        projet = Projet.objects.first()
        programme = Programme.objects.first()
        return admin, projet, programme

    # --- M36 : Marches Publics -----------------------------------------------

    def _seed_m36_marches(self):
        from marches_publics.models import (
            PlanPassationMarche, DemandeAchat, AppelOffre,
            SoumissionnaireOffre, ContratMarche,
        )
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        plan, created = PlanPassationMarche.objects.get_or_create(
            annee=2026, titre="Plan de Passation des Marches 2026",
            defaults={
                "programme": programme, "projet": projet,
                "description": "Plan annuel de passation des marches du programme PRCC",
                "statut": "valide",
                "budget_total_prevu": Decimal("75000000"),
                "cree_par": admin, "valide_par": admin,
                "date_validation": date.today(),
            }
        )
        self.stdout.write(f"  [M36] Plan PPM : {'Cree' if created else 'Existant'}")

        da, created = DemandeAchat.objects.get_or_create(
            titre="Acquisition vehicules 4x4 mission terrain",
            defaults={
                "description": "Acquisition de 3 vehicules 4x4 pour les missions terrain",
                "type_marche": "fournitures",
                "priorite": "haute",
                "statut": "validee",
                "programme": programme, "projet": projet,
                "plan_passation": plan,
                "budget_estime": Decimal("45000000"),
                "date_besoin": date.today() + timedelta(days=60),
                "justification": "Renouvellement du parc automobile vieillissant",
                "demandeur": admin, "valideur": admin,
            }
        )
        self.stdout.write(f"  [M36] Demande achat : {'Creee' if created else 'Existante'} — {da.reference}")

        ao, created = AppelOffre.objects.get_or_create(
            titre="AO Acquisition vehicules 4x4",
            defaults={
                "description": "Appel d'offres ouvert pour l'acquisition de 3 vehicules 4x4",
                "type_marche": "appel_offres_ouvert",
                "statut": "evaluation",
                "demande_achat": da, "plan_passation": plan,
                "programme": programme, "projet": projet,
                "budget_estime": Decimal("45000000"),
                "date_publication": date.today() - timedelta(days=30),
                "date_limite_soumission": date.today() - timedelta(days=5),
                "lieu_depot": "Siege ONG-DEMO, Abidjan",
                "criteres_evaluation": "70% technique, 30% financier",
                "responsable": admin,
            }
        )
        self.stdout.write(f"  [M36] AO : {'Cree' if created else 'Existant'} — {ao.reference}")

        for i, (nom, montant, note_tech, note_fin) in enumerate([
            ("Auto Import CI SARL", Decimal("43500000"), Decimal("85"), Decimal("78")),
            ("West Africa Motors", Decimal("44200000"), Decimal("79"), Decimal("82")),
            ("Afrique Distribution Auto", Decimal("42800000"), Decimal("72"), Decimal("90")),
        ]):
            soum, created = SoumissionnaireOffre.objects.get_or_create(
                appel_offre=ao, nom_entreprise=nom,
                defaults={
                    "montant_offre": montant, "statut": "qualifie",
                    "note_technique": note_tech, "note_financiere": note_fin,
                    "date_soumission": timezone.now() - timedelta(days=6),
                }
            )
            if created:
                soum.calculer_note_globale()
            self.stdout.write(f"  [M36] Soumissionnaire : {nom} — note={soum.note_globale}")

        contrat, created = ContratMarche.objects.get_or_create(
            titre="Contrat fourniture vehicules 4x4",
            defaults={
                "type_contrat": "fournitures",
                "statut": "signe",
                "appel_offre": ao,
                "programme": programme, "projet": projet,
                "prestataire_nom": "Auto Import CI SARL",
                "prestataire_email": "contact@autoimportci.ci",
                "montant_ttc": Decimal("43500000"),
                "montant_realise": Decimal("0"),
                "date_signature": date.today() - timedelta(days=2),
                "date_debut": date.today(),
                "date_fin_prevue": date.today() + timedelta(days=90),
                "objet": "Fourniture de 3 vehicules 4x4 Toyota Land Cruiser",
                "gestionnaire": admin,
            }
        )
        self.stdout.write(f"  [M36] Contrat : {'Cree' if created else 'Existant'} — {contrat.reference}")

    # --- M37 : RH Projet -----------------------------------------------------

    def _seed_m37_rh(self):
        from rh_projet.models import EmployeProjet, AffectationRH, FeuilleTemps, BesoinFormation
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        employes_data = [
            {"nom": "KONAN", "prenom": "Adjoua", "type_personnel": "employe",
             "poste": "Coordinatrice de Projet", "specialite": "Gestion de projets",
             "niveau_expertise": "senior", "email": "adjoua.konan@ong-demo.ci",
             "taux_journalier": Decimal("50000")},
            {"nom": "TRAORE", "prenom": "Ibrahima", "type_personnel": "consultant",
             "poste": "Expert S&E", "specialite": "Suivi-evaluation",
             "niveau_expertise": "expert", "email": "ibrahima.traore@consultant.ci",
             "taux_journalier": Decimal("80000")},
            {"nom": "BAMBA", "prenom": "Fatoumata", "type_personnel": "employe",
             "poste": "Assistante Financiere", "specialite": "Finance et comptabilite",
             "niveau_expertise": "intermediaire", "email": "fatoumata.bamba@ong-demo.ci",
             "taux_journalier": Decimal("35000")},
        ]
        for e_data in employes_data:
            emp, created = EmployeProjet.objects.get_or_create(
                email=e_data["email"],
                defaults={**e_data, "devise": "XOF", "statut": "actif"}
            )
            self.stdout.write(f"  [M37] Employe : {'Cree' if created else 'Existant'} — {emp.nom_complet}")

            if created and projet:
                AffectationRH.objects.create(
                    employe=emp, projet=projet, programme=programme,
                    role=e_data["poste"],
                    taux_affectation=80 if e_data["type_personnel"] == "consultant" else 100,
                    date_debut=date.today() - timedelta(days=30),
                    statut="active",
                )
                if e_data["type_personnel"] == "consultant":
                    BesoinFormation.objects.create(
                        employe=emp, projet=projet,
                        intitule="Formation Gestion Axee sur les Resultats (GAR)",
                        domaine="suivi_evaluation",
                        priorite="haute",
                        statut="planifie",
                        cout_estime=Decimal("350000"),
                        duree_jours=3,
                    )

    # --- M38 : Logistique ----------------------------------------------------

    def _seed_m38_logistique(self):
        from logistique.models import Vehicule, Equipement, Magasin, ArticleStock, LigneStock
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        vehicules_data = [
            {"immatriculation": "CI-2024-AAB-01", "type_vehicule": "4x4",
             "marque": "Toyota", "modele": "Land Cruiser", "annee": 2024,
             "couleur": "Blanc", "statut": "disponible",
             "date_expiration_assurance": date.today() + timedelta(days=180)},
            {"immatriculation": "CI-2023-AAB-02", "type_vehicule": "voiture",
             "marque": "Renault", "modele": "Duster", "annee": 2023,
             "couleur": "Gris", "statut": "disponible",
             "date_expiration_assurance": date.today() + timedelta(days=90)},
        ]
        for v_data in vehicules_data:
            v, created = Vehicule.objects.get_or_create(
                immatriculation=v_data["immatriculation"],
                defaults={**v_data, "projet": projet, "programme": programme,
                           "kilometrage_actuel": 15000}
            )
            self.stdout.write(f"  [M38] Vehicule : {'Cree' if created else 'Existant'} — {v}")

        equipements_data = [
            {"nom": "Ordinateur portable HP EliteBook", "type_equipement": "informatique",
             "marque": "HP", "modele": "EliteBook 840", "statut": "affecte"},
            {"nom": "Imprimante Canon PIXMA", "type_equipement": "informatique",
             "marque": "Canon", "modele": "PIXMA G3411", "statut": "disponible"},
            {"nom": "GPS Garmin Montana", "type_equipement": "terrain",
             "marque": "Garmin", "modele": "Montana 700", "statut": "disponible"},
        ]
        for eq_data in equipements_data:
            eq, created = Equipement.objects.get_or_create(
                nom=eq_data["nom"],
                defaults={**eq_data, "projet": projet, "programme": programme,
                           "valeur_acquisition": Decimal("500000")}
            )
            self.stdout.write(f"  [M38] Equipement : {'Cree' if created else 'Existant'} — {eq.code_inventaire}")

        magasin, created = Magasin.objects.get_or_create(
            nom="Magasin Central Abidjan",
            defaults={
                "code": "MAG-ABJ-01",
                "adresse": "Zone industrielle Yopougon, Abidjan",
                "responsable": admin, "programme": programme,
            }
        )
        self.stdout.write(f"  [M38] Magasin : {'Cree' if created else 'Existant'} — {magasin}")

        articles_data = [
            {"nom": "Rames de papier A4", "unite": "rame", "categorie": "Fournitures bureau",
             "stock_alerte": Decimal("10"), "prix_unitaire": Decimal("3500")},
            {"nom": "Stylos bille bleu", "unite": "boite", "categorie": "Fournitures bureau",
             "stock_alerte": Decimal("5"), "prix_unitaire": Decimal("2500")},
            {"nom": "Carburant essence", "unite": "litre", "categorie": "Carburant",
             "stock_alerte": Decimal("100"), "prix_unitaire": Decimal("700")},
        ]
        for art_data in articles_data:
            art, created = ArticleStock.objects.get_or_create(
                nom=art_data["nom"],
                defaults=art_data
            )
            if created:
                LigneStock.objects.get_or_create(
                    magasin=magasin, article=art,
                    defaults={"quantite": art_data["stock_alerte"] * 3,
                              "valeur_totale": art_data["stock_alerte"] * 3 * art_data["prix_unitaire"]}
                )
            self.stdout.write(f"  [M38] Article : {'Cree' if created else 'Existant'} — {art.code}")

    # --- M39+M40+M44 : Partenaires, Conventions, Portail ---------------------

    def _seed_m39_m40_partenaires(self):
        from partenaires_bailleurs.models import (
            Partenaire, Convention, LiaisonProjetPartenaire,
        )
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        partenaires_data = [
            {"nom": "Union Europeenne", "sigle": "UE", "type_partenaire": "bailleur",
             "pays": "Belgique", "email": "ue-delegation@ec.europa.eu",
             "secteurs_intervention": ["education", "sante", "gouvernance"]},
            {"nom": "PNUD Cote d'Ivoire", "sigle": "PNUD-CI", "type_partenaire": "institution_publique",
             "pays": "Cote d'Ivoire", "email": "pnud-ci@undp.org",
             "secteurs_intervention": ["developpement", "environnement"]},
            {"nom": "Caritas Cote d'Ivoire", "sigle": "CARITAS-CI", "type_partenaire": "ong",
             "pays": "Cote d'Ivoire", "email": "caritas@caritas-ci.org",
             "secteurs_intervention": ["social", "humanitaire"]},
        ]
        for p_data in partenaires_data:
            part, created = Partenaire.objects.get_or_create(
                sigle=p_data["sigle"],
                defaults={**p_data, "statut": "actif", "cree_par": admin}
            )
            self.stdout.write(f"  [M39] Partenaire : {'Cree' if created else 'Existant'} — {part}")

            if created and projet:
                LiaisonProjetPartenaire.objects.get_or_create(
                    partenaire=part, projet=projet,
                    defaults={
                        "role": "bailleur_principal" if part.sigle == "UE" else "partenaire_execution",
                        "montant_finance": Decimal("200000000") if part.sigle == "UE" else Decimal("50000000"),
                        "date_debut": date.today() - timedelta(days=180),
                    }
                )

            if created and part.type_partenaire == "bailleur":
                conv, c2 = Convention.objects.get_or_create(
                    intitule=f"Convention de financement PRCC — {part.nom}",
                    defaults={
                        "type_convention": "convention",
                        "statut": "actif",
                        "partenaire": part,
                        "programme": programme,
                        "objet": "Financement du programme PRCC pour la periode 2026-2028",
                        "montant": Decimal("200000000"),
                        "devise": "EUR",
                        "date_signature": date.today() - timedelta(days=90),
                        "date_debut": date.today() - timedelta(days=90),
                        "date_fin": date.today() + timedelta(days=900),
                        "date_expiration_alerte": date.today() + timedelta(days=840),
                        "responsable": admin,
                    }
                )
                self.stdout.write(f"  [M40] Convention : {'Creee' if c2 else 'Existante'} — {conv.reference}")

    # --- M41 : SIG -----------------------------------------------------------

    def _seed_m41_sig(self):
        from sig.models import ZoneSIG, CoucheCartographique, PointCartographie, InfrastructureSIG, CarteSIG
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        zones_data = [
            {"nom": "Cote d'Ivoire", "code": "CI", "type_zone": "pays", "pays": "Cote d'Ivoire",
             "latitude_centre": Decimal("7.539989"), "longitude_centre": Decimal("-5.547080")},
            {"nom": "Abidjan", "code": "ABJ", "type_zone": "commune", "pays": "Cote d'Ivoire",
             "latitude_centre": Decimal("5.359952"), "longitude_centre": Decimal("-4.008256"),
             "population": 5000000},
            {"nom": "Bouake", "code": "BKO", "type_zone": "commune", "pays": "Cote d'Ivoire",
             "latitude_centre": Decimal("7.692014"), "longitude_centre": Decimal("-5.030744"),
             "population": 600000},
        ]
        zone_ci = None
        for z_data in zones_data:
            zone, created = ZoneSIG.objects.get_or_create(
                code=z_data["code"],
                defaults=z_data
            )
            if z_data["code"] == "CI":
                zone_ci = zone
            self.stdout.write(f"  [M41] Zone SIG : {'Creee' if created else 'Existante'} — {zone}")

        couche, created = CoucheCartographique.objects.get_or_create(
            nom="Projets actifs",
            defaults={
                "type_couche": "projets",
                "style_affichage": "points",
                "couleur": "#0ea5e9",
                "icone": "FolderKanban",
                "est_visible": True,
                "est_publique": True,
                "cree_par": admin,
            }
        )
        self.stdout.write(f"  [M41] Couche : {'Creee' if created else 'Existante'} — {couche}")

        points_data = [
            {"titre": "Bureau Projet PRCC Abidjan", "type_point": "projet",
             "latitude": Decimal("5.359952"), "longitude": Decimal("-4.008256"),
             "description": "Bureau principal du projet PRCC"},
            {"titre": "Site formation Bouake", "type_point": "activite",
             "latitude": Decimal("7.692014"), "longitude": Decimal("-5.030744"),
             "description": "Site de formation des agents terrain"},
            {"titre": "Centre de sante beneficiaire Yopougon", "type_point": "infrastructure",
             "latitude": Decimal("5.390000"), "longitude": Decimal("-4.070000"),
             "description": "Centre de sante refabrique par le projet"},
        ]
        for pt_data in points_data:
            pt, created = PointCartographie.objects.get_or_create(
                titre=pt_data["titre"],
                defaults={**pt_data, "couche": couche, "projet": projet,
                           "couleur": "#0ea5e9", "actif": True, "cree_par": admin}
            )
            self.stdout.write(f"  [M41] Point SIG : {'Cree' if created else 'Existant'} — {pt.titre}")

        infra, created = InfrastructureSIG.objects.get_or_create(
            nom="Ecole primaire refabrilquee Songon",
            defaults={
                "type_infrastructure": "ecole",
                "statut": "operationnel",
                "latitude": Decimal("5.310000"), "longitude": Decimal("-4.380000"),
                "description": "Ecole primaire de 6 classes refabrilquee par le projet",
                "capacite": 300, "population_beneficiaire": 250,
                "date_mise_en_service": date.today() - timedelta(days=120),
                "cout_realisation": Decimal("18000000"),
                "projet": projet, "programme": programme,
                "cree_par": admin,
            }
        )
        self.stdout.write(f"  [M41] Infrastructure : {'Creee' if created else 'Existante'} — {infra}")

        carte, created = CarteSIG.objects.get_or_create(
            nom="Carte des interventions PRCC",
            defaults={
                "description": "Carte principale des zones d'intervention du programme",
                "centre_lat": Decimal("7.539989"), "centre_lon": Decimal("-5.547080"),
                "zoom_defaut": 7,
                "est_publique": True, "est_defaut": True,
                "programme": programme, "cree_par": admin,
            }
        )
        if created:
            carte.couches.add(couche)
        self.stdout.write(f"  [M41] Carte SIG : {'Creee' if created else 'Existante'} — {carte}")

    # --- M43 : Evenements ----------------------------------------------------

    def _seed_m43_evenements(self):
        from collaboration.models import Evenement, ParticipantEvenement
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        evenements_data = [
            {
                "titre": "Atelier de lancement du projet PRCC",
                "type_evenement": "atelier",
                "statut": "termine",
                "description": "Atelier de lancement officiel du projet avec toutes les parties prenantes",
                "objectifs": "Presenter les objectifs, la methodologie et le plan d'action du projet",
                "lieu": "Hotel Ivoire, Abidjan",
                "date_debut": timezone.now() - timedelta(days=60),
                "date_fin": timezone.now() - timedelta(days=59),
                "nb_participants_attendus": 50,
                "budget_prevu": Decimal("3500000"),
                "budget_realise": Decimal("3200000"),
                "inscription_requise": True,
            },
            {
                "titre": "Formation collecte de donnees terrain",
                "type_evenement": "formation",
                "statut": "planifie",
                "description": "Formation des agents terrain a l'utilisation de l'application mobile",
                "objectifs": "Maitriser l'application mobile de collecte et les protocoles terrain",
                "lieu": "Salle de conference ONG-DEMO, Abidjan",
                "date_debut": timezone.now() + timedelta(days=15),
                "date_fin": timezone.now() + timedelta(days=17),
                "nb_participants_attendus": 20,
                "budget_prevu": Decimal("1500000"),
                "inscription_requise": True,
                "date_limite_inscription": (timezone.now() + timedelta(days=10)).date(),
            },
        ]
        for ev_data in evenements_data:
            ev, created = Evenement.objects.get_or_create(
                titre=ev_data["titre"],
                defaults={**ev_data, "programme": programme, "projet": projet, "organisateur": admin}
            )
            if created and ev_data["statut"] == "termine":
                ParticipantEvenement.objects.get_or_create(
                    evenement=ev, utilisateur=admin,
                    defaults={"statut": "present", "qr_code_scan": True}
                )
            self.stdout.write(f"  [M43] Evenement : {'Cree' if created else 'Existant'} — {ev.titre}")

    # --- M45 : Capitalisation -------------------------------------------------

    def _seed_m45_capitalisation(self):
        from capitalisation.models import FicheCapitalisation, EntreeBibliotheque, CentreConnaissance
        admin, projet, programme = self._get_admin_projet_programme()
        if not admin:
            return

        fiches_data = [
            {
                "titre": "Approche participative pour la collecte de donnees terrain",
                "type_fiche": "bonne_pratique",
                "domaine": "suivi_evaluation",
                "statut": "publiee",
                "contexte": "Dans le cadre de la collecte de donnees pour les indicateurs de resultat",
                "probleme_defi": "Resistance des communautes a partager les informations",
                "solution_approche": "Implication des leaders communautaires des la phase de conception",
                "resultats_obtenus": "Taux de participation passe de 45% a 87% sur 3 mois",
                "lecon_principale": "L'implication des parties prenantes locales est determinante",
                "recommandation": "Prevoir un atelier de co-construction avec les communautes",
                "niveau_replicabilite": "eleve",
                "mots_cles": "participation, communaute, collecte, indicateurs",
                "genere_par_ia": False,
                "nb_consultations": 15,
            },
            {
                "titre": "Gestion des retards d'activites : protocole de rattrapage",
                "type_fiche": "lecon_apprise",
                "domaine": "gestion_projet",
                "statut": "validee",
                "contexte": "Projet PRCC, retard de 3 semaines sur le volet formation",
                "probleme_defi": "Retards cumules dus aux periodes de fetes et aux obligations culturelles",
                "solution_approche": "Creation d'un calendrier d'evenements culturels et religieux",
                "resultats_obtenus": "Planification ajustee, retards combles en 6 semaines",
                "lecon_principale": "Integrer le calendrier culturel/religieux local dans la planification",
                "recommandation": "Prevoir des buffers de 15% sur les jalons critiques en zone rurale",
                "niveau_replicabilite": "eleve",
                "mots_cles": "retard, planning, culture, buffer",
                "genere_par_ia": False,
                "nb_consultations": 8,
            },
        ]
        for f_data in fiches_data:
            fiche, created = FicheCapitalisation.objects.get_or_create(
                titre=f_data["titre"],
                defaults={**f_data, "projet": projet, "programme": programme,
                           "auteur": admin, "valide_par": admin}
            )
            self.stdout.write(f"  [M45] Fiche : {'Creee' if created else 'Existante'} — {fiche.reference}")

        entrees_data = [
            {"titre": "Guide de gestion de projet PMI PMBOK 7e edition",
             "categorie": "guide", "domaine": "gestion_projet",
             "auteur": "Project Management Institute",
             "organisation": "PMI", "annee_publication": 2021, "langue": "fr",
             "mots_cles": "pmbok, gestion projet, methodologie"},
            {"titre": "Manuel de suivi-evaluation des projets de developpement",
             "categorie": "guide", "domaine": "suivi_evaluation",
             "auteur": "OCDE-CAD",
             "organisation": "OCDE", "annee_publication": 2022, "langue": "fr",
             "mots_cles": "suivi, evaluation, indicateurs, rbm"},
        ]
        for e_data in entrees_data:
            entree, created = EntreeBibliotheque.objects.get_or_create(
                titre=e_data["titre"],
                defaults={**e_data, "est_public": True, "programme": programme, "ajoute_par": admin}
            )
            self.stdout.write(f"  [M45] Entree bibliotheque : {'Creee' if created else 'Existante'} — {entree.titre[:50]}")

        centre, created = CentreConnaissance.objects.get_or_create(
            nom="Centre Gestion de Projet",
            defaults={
                "description": "Ressources et capitalisation sur la gestion de projets de developpement",
                "domaine": "gestion_projet",
                "responsable": admin,
                "icone": "BookOpen",
                "couleur": "#7e22ce",
                "actif": True,
            }
        )
        self.stdout.write(f"  [M45] Centre connaissance : {'Cree' if created else 'Existant'} — {centre}")
