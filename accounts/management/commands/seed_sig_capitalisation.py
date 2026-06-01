"""
Seed SIG & Capitalisation — données enrichies
Usage : python manage.py seed_sig_capitalisation
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Données enrichies pour SIG (M41) et Capitalisation (M45)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._seed_sig()
            self._seed_capitalisation()
        self.stdout.write(self.style.SUCCESS("SIG + Capitalisation seedes avec succes !"))

    # -------------------------------------------------------------------------
    # SIG — M41
    # -------------------------------------------------------------------------

    def _seed_sig(self):
        from sig.models import (
            ZoneSIG, CoucheCartographique, PointCartographie,
            InfrastructureSIG, CarteSIG,
        )
        from accounts.models import User
        from programmes_projets.models import Projet, Programme

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.WARNING("  [SIG] Aucun admin — skipping"))
            return
        projet   = Projet.objects.first()
        programme = Programme.objects.first()

        # -- Zones géographiques ---------------------------------------------
        zones_data = [
            {"nom": "Côte d'Ivoire",   "code": "CI",   "type_zone": "pays",       "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("7.540"), "longitude_centre": Decimal("-5.547"), "superficie_km2": Decimal("322463")},
            {"nom": "Abidjan",          "code": "ABJ",  "type_zone": "commune",    "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("5.360"), "longitude_centre": Decimal("-4.008"), "population": 5000000},
            {"nom": "Bouaké",           "code": "BKO",  "type_zone": "commune",    "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("7.692"), "longitude_centre": Decimal("-5.031"), "population": 600000},
            {"nom": "Yamoussoukro",     "code": "YAM",  "type_zone": "commune",    "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("6.820"), "longitude_centre": Decimal("-5.274"), "population": 300000},
            {"nom": "Daloa",            "code": "DAL",  "type_zone": "commune",    "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("6.877"), "longitude_centre": Decimal("-6.450"), "population": 270000},
            {"nom": "San-Pédro",        "code": "SPD",  "type_zone": "commune",    "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("4.748"), "longitude_centre": Decimal("-6.636"), "population": 180000},
            {"nom": "Korhogo",          "code": "KHG",  "type_zone": "commune",    "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("9.458"), "longitude_centre": Decimal("-5.629"), "population": 250000},
            {"nom": "Zone Nord — PRCC", "code": "ZN-PRCC", "type_zone": "zone_intervention", "pays": "Côte d'Ivoire", "latitude_centre": Decimal("9.000"), "longitude_centre": Decimal("-5.500"), "superficie_km2": Decimal("45000")},
            {"nom": "Zone Sud — PRCC",  "code": "ZS-PRCC", "type_zone": "zone_intervention", "pays": "Côte d'Ivoire", "latitude_centre": Decimal("5.500"), "longitude_centre": Decimal("-4.200"), "superficie_km2": Decimal("12000")},
            {"nom": "Région des Lacs",  "code": "REG-LAC", "type_zone": "region",  "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("6.900"), "longitude_centre": Decimal("-4.700")},
            {"nom": "Région du Poro",   "code": "REG-POR", "type_zone": "region",  "pays": "Côte d'Ivoire",  "latitude_centre": Decimal("9.300"), "longitude_centre": Decimal("-5.700")},
        ]
        zones = {}
        for z in zones_data:
            obj, created = ZoneSIG.objects.get_or_create(code=z["code"], defaults=z)
            zones[z["code"]] = obj
            self.stdout.write(f"  Zone : {'C' if created else 'E'} — {obj.nom}")

        # -- Couches cartographiques ------------------------------------------
        couches_data = [
            {"nom": "Projets actifs",    "type_couche": "projets",        "style_affichage": "points",    "couleur": "#0ea5e9", "icone": "FolderKanban", "est_visible": True,  "est_publique": True,  "ordre": 1},
            {"nom": "Activités terrain", "type_couche": "activites",      "style_affichage": "points",    "couleur": "#10b981", "icone": "Zap",          "est_visible": True,  "est_publique": False, "ordre": 2},
            {"nom": "Bénéficiaires",     "type_couche": "beneficiaires",  "style_affichage": "cluster",   "couleur": "#f59e0b", "icone": "Users",        "est_visible": True,  "est_publique": False, "ordre": 3},
            {"nom": "Infrastructures",   "type_couche": "infrastructures","style_affichage": "points",    "couleur": "#6366f1", "icone": "Building2",    "est_visible": True,  "est_publique": True,  "ordre": 4},
            {"nom": "Zones d'intervention","type_couche":"zones",         "style_affichage": "polygones", "couleur": "#ec4899", "icone": "Map",          "est_visible": True,  "est_publique": True,  "ordre": 5},
            {"nom": "Risques identifiés","type_couche": "risques",        "style_affichage": "heatmap",   "couleur": "#ef4444", "icone": "AlertTriangle","est_visible": False, "est_publique": False, "ordre": 6},
        ]
        couches = {}
        for c in couches_data:
            obj, created = CoucheCartographique.objects.get_or_create(
                nom=c["nom"], defaults={**c, "cree_par": admin}
            )
            couches[c["nom"]] = obj
            self.stdout.write(f"  Couche : {'C' if created else 'E'} — {obj.nom}")

        # -- Points cartographiques ------------------------------------------
        couche_projets = couches.get("Projets actifs")
        couche_infras  = couches.get("Infrastructures")
        couche_activ   = couches.get("Activités terrain")

        points_data = [
            # Bureaux projets
            {"titre": "Bureau PRCC — Abidjan (siège)",  "type_point": "projet",         "latitude": Decimal("5.3599"),  "longitude": Decimal("-4.0083"), "description": "Siège principal du projet PRCC, Plateau", "couche": couche_projets, "couleur": "#0ea5e9"},
            {"titre": "Antenne PRCC — Bouaké",           "type_point": "projet",         "latitude": Decimal("7.6920"),  "longitude": Decimal("-5.0307"), "description": "Antenne régionale PRCC — Centre du pays", "couche": couche_projets, "couleur": "#0ea5e9"},
            {"titre": "Antenne PRCC — Korhogo",          "type_point": "projet",         "latitude": Decimal("9.4580"),  "longitude": Decimal("-5.6290"), "description": "Antenne régionale PRCC — Nord du pays",   "couche": couche_projets, "couleur": "#0ea5e9"},
            # Activités terrain
            {"titre": "Site formation agents — Yopougon","type_point": "activite",       "latitude": Decimal("5.3900"),  "longitude": Decimal("-4.0700"), "description": "Formation 45 agents en collecte de données", "couche": couche_activ, "couleur": "#10b981"},
            {"titre": "Campagne sensibilisation — Daloa","type_point": "activite",       "latitude": Decimal("6.8770"),  "longitude": Decimal("-6.4500"), "description": "Campagne IEC auprès de 3 200 ménages",       "couche": couche_activ, "couleur": "#10b981"},
            {"titre": "Distribution intrants — Korhogo", "type_point": "activite",       "latitude": Decimal("9.4700"),  "longitude": Decimal("-5.6100"), "description": "Distribution 500 kits agricoles",            "couche": couche_activ, "couleur": "#10b981"},
            # Infrastructures
            {"titre": "École primaire Songon (réhabilitée)","type_point": "infrastructure","latitude": Decimal("5.3100"), "longitude": Decimal("-4.3800"), "description": "6 classes, 320 élèves bénéficiaires",        "couche": couche_infras,"couleur": "#6366f1"},
            {"titre": "Centre de santé Abobo (équipé)",  "type_point": "infrastructure", "latitude": Decimal("5.4100"),  "longitude": Decimal("-4.0200"), "description": "Maternité et consultation prénatale",         "couche": couche_infras,"couleur": "#6366f1"},
            {"titre": "Forage Katiola (neuf)",           "type_point": "infrastructure", "latitude": Decimal("8.1300"),  "longitude": Decimal("-5.1000"), "description": "Forage + pompe solaire, 1 200 bénéficiaires", "couche": couche_infras,"couleur": "#6366f1"},
            {"titre": "Marché rénové — San-Pédro",       "type_point": "infrastructure", "latitude": Decimal("4.7480"),  "longitude": Decimal("-6.6360"), "description": "250 boutiques, hangar poisson réhabilité",    "couche": couche_infras,"couleur": "#6366f1"},
            # Points de collecte
            {"titre": "Point collecte données — Gagnoa", "type_point": "collecte",       "latitude": Decimal("6.1320"),  "longitude": Decimal("-5.9500"), "description": "Enquête ménage 600 foyers",                   "couche": couche_activ, "couleur": "#f59e0b"},
            {"titre": "Point collecte — Aboisso",        "type_point": "collecte",       "latitude": Decimal("5.4700"),  "longitude": Decimal("-3.2100"), "description": "Collecte indicateurs eau potable",           "couche": couche_activ, "couleur": "#f59e0b"},
        ]
        for p in points_data:
            obj, created = PointCartographie.objects.get_or_create(
                titre=p["titre"],
                defaults={**p, "projet": projet, "actif": True, "cree_par": admin}
            )
            self.stdout.write(f"  Point : {'C' if created else 'E'} — {obj.titre}")

        # -- Infrastructures SIG ---------------------------------------------
        infras_data = [
            {"nom": "École primaire Songon (réhabilitée)", "type_infrastructure": "ecole",    "statut": "operationnel",     "latitude": Decimal("5.3100"),  "longitude": Decimal("-4.3800"), "capacite": 320, "population_beneficiaire": 320, "date_mise_en_service": date.today() - timedelta(days=120), "cout_realisation": Decimal("18000000"), "description": "6 classes + bibliothèque scolaire réhabilitées"},
            {"nom": "Centre de santé Abobo (équipé)",       "type_infrastructure": "hopital",  "statut": "operationnel",     "latitude": Decimal("5.4100"),  "longitude": Decimal("-4.0200"), "capacite": 80,  "population_beneficiaire": 12000,  "date_mise_en_service": date.today() - timedelta(days=200), "cout_realisation": Decimal("35000000"), "description": "Maternité, CPN et consultation générale"},
            {"nom": "Forage solaire Katiola",                "type_infrastructure": "puits",    "statut": "operationnel",     "latitude": Decimal("8.1300"),  "longitude": Decimal("-5.1000"), "capacite": None,"population_beneficiaire": 1200,   "date_mise_en_service": date.today() - timedelta(days=90),  "cout_realisation": Decimal("8500000"),  "description": "Forage 80m + pompe solaire 3kWc"},
            {"nom": "Marché central rénové San-Pédro",       "type_infrastructure": "marche",   "statut": "operationnel",     "latitude": Decimal("4.7480"),  "longitude": Decimal("-6.6360"), "capacite": 250, "population_beneficiaire": 5000,   "date_mise_en_service": date.today() - timedelta(days=60),  "cout_realisation": Decimal("22000000"), "description": "250 boutiques + hangar poisson réhabilité"},
            {"nom": "Piste rurale Katiola–Niakaramandougou","type_infrastructure": "route",    "statut": "operationnel",     "latitude": Decimal("8.2000"),  "longitude": Decimal("-5.2000"), "capacite": None,"population_beneficiaire": 8000,   "date_mise_en_service": date.today() - timedelta(days=180), "cout_realisation": Decimal("47000000"), "description": "18 km de piste réhabilitée"},
            {"nom": "Bureau ONG terrain — Korhogo",          "type_infrastructure": "bureau",   "statut": "operationnel",     "latitude": Decimal("9.4600"),  "longitude": Decimal("-5.6200"), "capacite": 15,  "population_beneficiaire": None,   "date_mise_en_service": date.today() - timedelta(days=400), "cout_realisation": Decimal("5000000"),  "description": "Bureau antenne nord + logement équipe"},
            {"nom": "Pont rivière Comoé — Bondoukou",        "type_infrastructure": "pont",     "statut": "en_construction",  "latitude": Decimal("8.0400"),  "longitude": Decimal("-2.8000"), "capacite": None,"population_beneficiaire": 3000,   "date_mise_en_service": None,                                 "cout_realisation": Decimal("120000000"),"description": "Pont 45m préfabriqué, fin prévue T2 2026"},
            {"nom": "Entrepôt intrants Yamoussoukro",        "type_infrastructure": "entrepot", "statut": "operationnel",     "latitude": Decimal("6.8100"),  "longitude": Decimal("-5.2900"), "capacite": 500, "population_beneficiaire": None,   "date_mise_en_service": date.today() - timedelta(days=50),  "cout_realisation": Decimal("6500000"),  "description": "Entrepôt 500m² intrants agricoles"},
        ]
        for inf in infras_data:
            zone_code = None
            # Rattachement automatique à la zone la plus proche (simple approche par code)
            if float(inf["latitude"]) > 8:
                zone_code = "REG-POR"
            elif float(inf["latitude"]) > 6.5:
                zone_code = "REG-LAC"
            zone = zones.get(zone_code)
            obj, created = InfrastructureSIG.objects.get_or_create(
                nom=inf["nom"],
                defaults={**inf, "zone": zone, "projet": projet, "programme": programme, "cree_par": admin}
            )
            self.stdout.write(f"  Infra : {'C' if created else 'E'} — {obj.nom}")

        # -- Cartes SIG ------------------------------------------------------
        cartes_data = [
            {"nom": "Carte principale — PRCC",    "description": "Vue d'ensemble de toutes les interventions du programme PRCC",     "centre_lat": Decimal("7.540"), "centre_lon": Decimal("-5.547"), "zoom_defaut": 7, "est_publique": True,  "est_defaut": True},
            {"nom": "Carte infrastructures 2026","description": "Toutes les infrastructures réalisées, en cours et planifiées",     "centre_lat": Decimal("6.820"), "centre_lon": Decimal("-5.274"), "zoom_defaut": 8, "est_publique": True,  "est_defaut": False},
            {"nom": "Carte zone nord PRCC",       "description": "Interventions dans le Nord : Korhogo, Katiola, Poro",             "centre_lat": Decimal("9.000"), "centre_lon": Decimal("-5.500"), "zoom_defaut": 9, "est_publique": False, "est_defaut": False},
            {"nom": "Carte collecte terrain",     "description": "Points de collecte et zones d'enquête actives",                   "centre_lat": Decimal("5.360"), "centre_lon": Decimal("-4.008"), "zoom_defaut": 9, "est_publique": False, "est_defaut": False},
        ]
        for c in cartes_data:
            obj, created = CarteSIG.objects.get_or_create(
                nom=c["nom"],
                defaults={**c, "programme": programme, "cree_par": admin}
            )
            if created:
                # Ajouter toutes les couches
                obj.couches.set(list(couches.values()))
            self.stdout.write(f"  Carte : {'C' if created else 'E'} — {obj.nom}")

        self.stdout.write(self.style.SUCCESS("  [OK] SIG seede"))

    # -------------------------------------------------------------------------
    # Capitalisation — M45
    # -------------------------------------------------------------------------

    def _seed_capitalisation(self):
        from capitalisation.models import (
            FicheCapitalisation, EntreeBibliotheque, CommentaireFiche, CentreConnaissance,
        )
        from accounts.models import User
        from programmes_projets.models import Projet, Programme

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            return
        projet   = Projet.objects.first()
        programme = Programme.objects.first()

        # -- Fiches de capitalisation -----------------------------------------
        fiches_data = [
            {
                "titre": "Approche participative pour la collecte de données terrain",
                "type_fiche": "bonne_pratique", "domaine": "suivi_evaluation", "statut": "publiee",
                "contexte": "Collecte indicateurs projet PRCC en zone rurale Nord, résistance initiale des communautés.",
                "probleme_defi": "Taux de non-réponse de 55% lors des premières enquêtes ménage.",
                "solution_approche": "Co-conception des outils avec les chefs de village. Formation de 15 agents communautaires locaux comme relais. Sessions de sensibilisation préalables.",
                "resultats_obtenus": "Taux de participation passé de 45% à 87% en 3 mois. Qualité des données améliorée (erreurs < 3%).",
                "lecon_principale": "L'implication des leaders communautaires dès la phase de conception est déterminante pour l'acceptabilité.",
                "recommandation": "Prévoir systématiquement 2 semaines d'ateliers de co-construction en amont. Budget : 500 000 FCFA par zone.",
                "conditions_replicabilite": "Fonctionne dans toutes zones où les structures communautaires sont actives.",
                "indicateurs_succes": "Taux participation > 80%, Erreurs < 5%", "niveau_replicabilite": "eleve",
                "mots_cles": "participation communautaire, collecte données, enquête ménage, agents locaux",
                "periode_reference": "2025-2026", "zone_geographique": "Région Poro, Côte d'Ivoire",
                "public_cible": "Responsables S&E, Chefs de projet terrain", "nb_consultations": 24,
            },
            {
                "titre": "Protocole de rattrapage des retards d'activités en période festive",
                "type_fiche": "lecon_apprise", "domaine": "gestion_projet", "statut": "validee",
                "contexte": "Projet PRCC — retard de 3 semaines accumulé sur le volet formation (T4 2025).",
                "probleme_defi": "Obligations culturelles et fêtes religieuses non anticipées dans le calendrier.",
                "solution_approche": "Création d'un calendrier intégré des événements culturels/religieux locaux. Introduction de sessions de formation le samedi matin (5h additionnelles/semaine).",
                "resultats_obtenus": "Retards entièrement rattrapés en 6 semaines sans dépassement budgétaire.",
                "lecon_principale": "Intégrer systématiquement le calendrier culturel et religieux local dans la planification dès le démarrage.",
                "recommandation": "Prévoir des buffers de 15% sur les jalons critiques en zone rurale. Tenir un registre des périodes à risque.",
                "niveau_replicabilite": "eleve", "mots_cles": "planification, retard, calendrier culturel, buffer",
                "periode_reference": "T4 2025", "nb_consultations": 12,
            },
            {
                "titre": "Coordination multi-acteurs pour la réhabilitation d'écoles",
                "type_fiche": "etude_cas", "domaine": "gestion_projet", "statut": "publiee",
                "contexte": "Réhabilitation de 3 écoles primaires à Songon, Aboisso et Dabou en 8 mois.",
                "probleme_defi": "Coordination entre ONG, Ministère Éducation, mairies et communautés locales.",
                "solution_approche": "Mise en place d'un comité de pilotage mensuel réunissant tous les acteurs. Désignation d'un point focal dans chaque école. Plateforme de suivi partagée.",
                "resultats_obtenus": "3 écoles livrées dans les délais. 0 litige foncier. 960 élèves bénéficiaires.",
                "lecon_principale": "La désignation précoce d'un point focal unique dans chaque communauté élimine 80% des blocages administratifs.",
                "recommandation": "Systématiser les comités de pilotage multi-acteurs pour tous les travaux > 15M FCFA.",
                "niveau_replicabilite": "eleve", "mots_cles": "réhabilitation, coordination, écoles, multi-acteurs",
                "periode_reference": "2025", "nb_consultations": 18, "nb_favoris": 5,
            },
            {
                "titre": "Intégration des femmes dans les comités de gestion des points d'eau",
                "type_fiche": "innovation", "domaine": "participation",  "statut": "publiee",
                "contexte": "Gestion de 12 forages solaires dans la région du Poro.",
                "probleme_defi": "Panne des pompes dans les 6 mois suivant la livraison par manque d'entretien communautaire.",
                "solution_approche": "Formation de 24 femmes techniciens de base (2 par forage). Création de caisses de maintenance avec cotisations mensuelles de 500 FCFA/ménage.",
                "resultats_obtenus": "Taux de fonctionnalité des pompes : 92% à 18 mois (vs 40% historiquement). 8 réparations mineures effectuées par les femmes formées.",
                "lecon_principale": "L'autonomisation des femmes dans la maintenance est plus efficace que les contrats de prestataires externes.",
                "recommandation": "Prévoir au minimum 10 jours de formation maintenance pour chaque groupe de gestion.",
                "niveau_replicabilite": "eleve", "mots_cles": "genre, eau, maintenance, autonomisation, forage",
                "periode_reference": "2024-2026", "nb_consultations": 31, "nb_favoris": 8,
            },
            {
                "titre": "Difficultés de procurement des équipements médicaux — leçons tirées",
                "type_fiche": "echec_analyse", "domaine": "logistique", "statut": "validee",
                "contexte": "Équipement de 2 centres de santé — retard de 4 mois sur les équipements médicaux.",
                "probleme_defi": "Fournisseur local défaillant. Procédures douanières imprévues pour équipements importés.",
                "solution_approche": "Passation de marché refaite avec 3 fournisseurs en compétition. Anticipation des démarches douanières (12 semaines vs 4 prévues).",
                "resultats_obtenus": "Livraison finalement effectuée avec 4 mois de retard. Aucun dépassement budgétaire.",
                "lecon_principale": "Pour les équipements médicaux importés, toujours prévoir 12 semaines de délai douanier minimum.",
                "recommandation": "Recourir systématiquement au transitaire agréé. Inclure clause pénalité retard dans tous contrats équipements.",
                "niveau_replicabilite": "moyen", "mots_cles": "procurement, logistique, équipements médicaux, douane, retard",
                "periode_reference": "2025", "nb_consultations": 7,
            },
            {
                "titre": "Utilisation de l'application mobile pour le suivi S&E en temps réel",
                "type_fiche": "innovation", "domaine": "suivi_evaluation", "statut": "publiee",
                "contexte": "Déploiement de l'ERP mobile terrain pour 32 agents dans 4 régions.",
                "probleme_defi": "Collecte manuelle sur papier avec saisie différée causant 3 semaines de délai de remontée des données.",
                "solution_approche": "Formation 2 jours sur l'application. Mode hors-ligne pour les zones sans réseau. Synchronisation quotidienne automatique au bureau.",
                "resultats_obtenus": "Délai de remontée réduit de 21 jours à 48h. Erreurs de saisie réduites de 12% à 0,8%.",
                "lecon_principale": "Le mode hors-ligne est indispensable en zone rurale. Prévoir au moins 32 Go de stockage sur chaque appareil.",
                "recommandation": "Adopter l'application mobile pour tous les projets avec > 10 agents terrain.",
                "genere_par_ia": True, "niveau_replicabilite": "eleve",
                "mots_cles": "mobile, numérique, collecte terrain, hors-ligne, S&E",
                "periode_reference": "2025-2026", "nb_consultations": 42, "nb_favoris": 12,
            },
        ]
        fiches_creees = []
        for f in fiches_data:
            obj, created = FicheCapitalisation.objects.get_or_create(
                titre=f["titre"],
                defaults={**f, "projet": projet, "programme": programme,
                           "auteur": admin, "valide_par": admin}
            )
            fiches_creees.append(obj)
            self.stdout.write(f"  Fiche : {'C' if created else 'E'} — {obj.reference} {obj.titre[:50]}")

        # -- Commentaires ------------------------------------------------------
        if fiches_creees:
            commentaires = [
                (fiches_creees[0], "Excellente approche ! Nous l'avons adaptée dans notre projet en Guinée avec de bons résultats."),
                (fiches_creees[0], "Peut-on avoir le guide de formation des agents communautaires ?"),
                (fiches_creees[2], "La méthode de point focal est très efficace, on l'a répliquée sur 2 chantiers."),
                (fiches_creees[3], "Impact genre remarquable. Les femmes sont maintenant les garantes de la durabilité."),
                (fiches_creees[5], "L'application mobile a transformé notre suivi. Délai passé de 30j à 2j !"),
            ]
            for fiche, contenu in commentaires:
                CommentaireFiche.objects.get_or_create(
                    fiche=fiche, auteur=admin, contenu=contenu
                )
            self.stdout.write(f"  Commentaires : {len(commentaires)} créés/existants")

        # -- Bibliothèque ------------------------------------------------------
        entrees_data = [
            {"titre": "Guide PMI PMBOK 7e édition — Gestion de projet",          "categorie": "guide",      "domaine": "gestion_projet",    "auteur": "Project Management Institute",   "organisation": "PMI",    "annee_publication": 2021, "langue": "fr", "mots_cles": "pmbok, gestion projet, agile, livrables",         "nb_telechargements": 34},
            {"titre": "Manuel OCDE-CAD Suivi-Évaluation projets développement",   "categorie": "guide",      "domaine": "suivi_evaluation",  "auteur": "OCDE-CAD",                       "organisation": "OCDE",   "annee_publication": 2022, "langue": "fr", "mots_cles": "suivi, évaluation, RBM, indicateurs, résultats",  "nb_telechargements": 28},
            {"titre": "Guide comptabilité projets — ONG et secteur développement","categorie": "guide",      "domaine": "finance",           "auteur": "Expertise France",               "organisation": "ExFr",   "annee_publication": 2023, "langue": "fr", "mots_cles": "comptabilité ONG, justification bailleurs, FCFA",  "nb_telechargements": 19},
            {"titre": "Boîte à outils RH projets humanitaires",                   "categorie": "outil",      "domaine": "rh",                "auteur": "CHS Alliance",                   "organisation": "CHS",    "annee_publication": 2023, "langue": "fr", "mots_cles": "RH, recrutement, performance, consultants",        "nb_telechargements": 15},
            {"titre": "Rapport final évaluation — Programme Eau Potable CI 2023", "categorie": "rapport",    "domaine": "suivi_evaluation",  "auteur": "Bureau évaluation indépendant",  "organisation": "PRCC",   "annee_publication": 2023, "langue": "fr", "mots_cles": "évaluation finale, eau, Côte d'Ivoire, impact",    "nb_telechargements": 22},
            {"titre": "Guide passation des marchés publics — UEMOA 2024",         "categorie": "guide",      "domaine": "juridique",         "auteur": "UEMOA",                          "organisation": "UEMOA",  "annee_publication": 2024, "langue": "fr", "mots_cles": "marchés publics, DAO, appel offres, UEMOA",        "nb_telechargements": 41},
            {"titre": "Module formation gestion de projet (Niveau 1)",            "categorie": "formation",  "domaine": "gestion_projet",    "auteur": "PRCC / Équipe capitalisation",   "organisation": "PRCC",   "annee_publication": 2025, "langue": "fr", "mots_cles": "formation, planification, suivi, chef de projet",  "nb_telechargements": 17},
            {"titre": "Article — Impact des projets d'eau sur la scolarisation",  "categorie": "article",    "domaine": "participation",     "auteur": "Dr Konan Brou et al.",           "organisation": "ENSEA",  "annee_publication": 2024, "langue": "fr", "mots_cles": "eau, scolarisation, genre, impact social",         "nb_telechargements": 8},
            {"titre": "Template plan de travail annuel (PTA) — ONG",             "categorie": "outil",      "domaine": "gestion_projet",    "auteur": "Méthodes PRCC",                  "organisation": "PRCC",   "annee_publication": 2025, "langue": "fr", "mots_cles": "PTA, planification annuelle, activités, budget",   "nb_telechargements": 53},
            {"titre": "Guide logistique terrain projets humanitaires",            "categorie": "guide",      "domaine": "logistique",        "auteur": "Oxfam Logistics",                "organisation": "Oxfam",  "annee_publication": 2022, "langue": "fr", "mots_cles": "logistique, véhicules, stocks, chaîne approvisionnement", "nb_telechargements": 12},
        ]
        for e in entrees_data:
            obj, created = EntreeBibliotheque.objects.get_or_create(
                titre=e["titre"],
                defaults={**e, "est_public": True, "programme": programme, "ajoute_par": admin}
            )
            self.stdout.write(f"  Biblio : {'C' if created else 'E'} — {obj.titre[:55]}")

        # -- Centres de connaissances ------------------------------------------
        centres_data = [
            {"nom": "Centre Gestion de Projet",    "domaine": "gestion_projet",    "couleur": "#7e22ce", "icone": "BookOpen",    "description": "Ressources, fiches et outils pour la gestion de projets de développement"},
            {"nom": "Centre Suivi-Évaluation",     "domaine": "suivi_evaluation",  "couleur": "#0ea5e9", "icone": "BarChart2",   "description": "Méthodes S&E, RBM, outils de collecte et guides d'évaluation"},
            {"nom": "Centre Finance & Comptabilité","domaine": "finance",           "couleur": "#d97706", "icone": "DollarSign",  "description": "Comptabilité projets, justification bailleurs, rapports financiers"},
            {"nom": "Centre Ressources Humaines",  "domaine": "rh",                "couleur": "#ec4899", "icone": "Users",       "description": "Recrutement, gestion contractuels, évaluation de performance"},
            {"nom": "Centre Logistique",           "domaine": "logistique",        "couleur": "#f59e0b", "icone": "Package",     "description": "Gestion du parc véhicules, stocks et chaîne d'approvisionnement"},
            {"nom": "Centre Juridique & Conformité","domaine": "juridique",        "couleur": "#ef4444", "icone": "Shield",      "description": "Marchés publics, conventions, conformité UEMOA"},
        ]
        for c in centres_data:
            obj, created = CentreConnaissance.objects.get_or_create(
                nom=c["nom"],
                defaults={**c, "responsable": admin, "actif": True}
            )
            if created and fiches_creees:
                # Rattacher les fiches pertinentes au centre
                fiches_du_domaine = [f for f in fiches_creees if f.domaine == c["domaine"]]
                if fiches_du_domaine:
                    obj.fiches.set(fiches_du_domaine)
            self.stdout.write(f"  Centre : {'C' if created else 'E'} — {obj.nom}")

        self.stdout.write(self.style.SUCCESS("  [OK] Capitalisation seedee"))
