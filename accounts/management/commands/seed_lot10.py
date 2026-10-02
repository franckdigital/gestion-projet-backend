"""
Seed Lot 10 — Complète les tables métier restées vides après les lots 1 à 9.

Couvre : structure organisationnelle (directions, services, sites, partenaires, comité),
RH (congés, absences, feuilles de temps, évaluations), finance (comptes et mouvements
bancaires, cofinancements), logistique (missions véhicules, entretiens, stocks),
marchés (avenants), diligences, exécution (commentaires, ordres de mission, rapports),
partenaires (contacts, renouvellements), collaboration, risques, courrier (visas).

Usage : python manage.py seed_lot10
Idempotent : relançable sans doublons. Chaque bloc est isolé : un échec n'arrête pas les autres.
"""
from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


def M(label):
    return apps.get_model(label)


def make(model, lookup, **values):
    """get_or_create qui ignore les champs inexistants sur le modèle."""
    names = {f.name for f in model._meta.get_fields() if getattr(f, 'concrete', False)}
    values = {k: v for k, v in values.items() if k in names}
    obj, _ = model.objects.get_or_create(**lookup, defaults=values)
    return obj


class Command(BaseCommand):
    help = 'Complète les tables métier vides (structure, RH, finance, logistique, etc.)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        now = timezone.now()
        User = M('accounts.User')
        self.admin = User.objects.filter(is_superuser=True).first() or User.objects.first()
        self.users = list(User.objects.filter(is_active=True)[:10])
        self.today, self.now = today, now

        blocks = [
            self.structure, self.rh, self.finance, self.logistique, self.marches,
            self.diligences, self.execution, self.partenaires, self.collaboration,
            self.risques, self.courrier,
        ]
        ok = 0
        for block in blocks:
            try:
                with transaction.atomic():
                    n = block()
                self.stdout.write(f'  [ok] {block.__name__:<14} {n} objets')
                ok += 1
            except Exception as exc:  # un bloc en échec n'arrête pas les autres
                self.stdout.write(self.style.ERROR(f'  [ERREUR] {block.__name__}: {exc}'))
        self.stdout.write(self.style.SUCCESS(f'[OK] Seed Lot 10 : {ok}/{len(blocks)} blocs'))

    # ── Structure organisationnelle ──────────────────────────────────────────
    def structure(self):
        Org = M('gouvernance.Organisation').objects.first()
        if not Org:
            return 0
        n = 0
        directions = {}
        for code, nom, sigle in [
            ('DG', 'Direction Générale', 'DG'),
            ('DAF', 'Direction Administrative et Financière', 'DAF'),
            ('DPSE', 'Direction des Programmes et du Suivi-Évaluation', 'DPSE'),
            ('DLOG', 'Direction de la Logistique et des Achats', 'DLOG'),
        ]:
            directions[code] = make(M('gouvernance.Direction'), {'organisation': Org, 'code': code},
                                    nom=nom, sigle=sigle, responsable=self.admin, actif=True)
            n += 1
        sous = {}
        for dcode, code, nom in [
            ('DAF', 'DAF-CMP', 'Comptabilité et Trésorerie'),
            ('DAF', 'DAF-RH', 'Ressources Humaines'),
            ('DPSE', 'DPSE-SE', 'Suivi-Évaluation'),
            ('DLOG', 'DLOG-ACH', 'Achats et Marchés'),
        ]:
            sous[code] = make(M('gouvernance.SousDirection'), {'direction': directions[dcode], 'code': code},
                              nom=nom, actif=True)
            n += 1
        for dcode, sd, code, nom in [
            ('DAF', 'DAF-CMP', 'SRV-COMPTA', 'Service Comptabilité'),
            ('DAF', 'DAF-RH', 'SRV-PAIE', 'Service Paie et Carrières'),
            ('DPSE', 'DPSE-SE', 'SRV-QUALITE', 'Service Qualité des Données'),
            ('DLOG', 'DLOG-ACH', 'SRV-PARC', 'Service Parc Automobile'),
        ]:
            make(M('gouvernance.Service'), {'code': code}, intitule=nom, direction=directions[dcode],
                 sous_direction=sous[sd], responsable=self.admin, actif=True)
            n += 1
        for code, nom, typ, ville in [
            ('SIEGE', 'Siège Abidjan', 'siege', 'Abidjan'),
            ('AG-BKE', 'Agence de Bouaké', 'agence', 'Bouaké'),
            ('AG-MAN', 'Antenne de Man', 'antenne', 'Man'),
            ('BP-KRG', 'Bureau projet Korhogo', 'bureau_projet', 'Korhogo'),
        ]:
            make(M('gouvernance.Site'), {'organisation': Org, 'code': code}, nom=nom, type_site=typ,
                 ville=ville, pays="Côte d'Ivoire", responsable=self.admin, actif=True)
            n += 1
        partenaires = []
        for nom, typ in [
            ('Ministère du Plan et du Développement', 'ministere'),
            ('Agence Française de Développement', 'bailleur'),
            ('ONG Solidarité Rurale', 'ong'),
            ('Cabinet Conseil Afrique SARL', 'prestataire'),
        ]:
            partenaires.append(make(M('gouvernance.Partenaire'), {'organisation': Org, 'nom': nom},
                                    type_partenaire=typ))
            n += 1
        make(M('gouvernance.ComiteDirecteur'), {'organisation': Org, 'intitule': 'Comité Directeur Trimestriel T3'},
             date_tenue=self.now - timedelta(days=20), lieu='Siège Abidjan', president=self.admin,
             ordre_du_jour='1. Revue de l\'exécution budgétaire\n2. État d\'avancement des projets\n3. Risques majeurs',
             compte_rendu='Le comité a validé la revue budgétaire et le plan d\'action du trimestre.')
        n += 1
        Programme = M('programmes_projets.Programme').objects.first()
        if Programme:
            for p, typ in zip(partenaires[:3], ['technique', 'financier', 'mise_en_oeuvre']):
                make(M('programmes_projets.PartenaireProgramme'), {'programme': Programme, 'partenaire': p},
                     type_participation=typ, actif=True)
                n += 1
        return n

    # ── Ressources humaines ──────────────────────────────────────────────────
    def rh(self):
        employes = list(M('rh_projet.EmployeProjet').objects.all()[:5])
        n = 0
        for i, e in enumerate(employes):
            d = self.today + timedelta(days=15 + i * 7)
            make(M('rh_projet.DemandeConge'), {'employe': e, 'date_debut': d},
                 date_fin=d + timedelta(days=4), nombre_jours=5, motif='Congé annuel')
            make(M('rh_projet.DemandeAbsence'), {'employe': e, 'date_absence': self.today - timedelta(days=3 + i)},
                 motif='Rendez-vous médical')
            feuille = make(M('rh_projet.FeuilleTemps'), {'employe': e, 'mois': self.today.month, 'annee': self.today.year},
                           total_heures=Decimal('0'), commentaire='Feuille de temps du mois')
            total = Decimal('0')
            for j in range(1, 6):
                jour = self.today - timedelta(days=j)
                if jour.weekday() < 5:
                    make(M('rh_projet.LigneFeuilleTemps'), {'feuille': feuille, 'date': jour}, heures=Decimal('8'))
                    total += Decimal('8')
            feuille.total_heures = total
            feuille.save(update_fields=['total_heures'])
            make(M('rh_projet.EvaluationPerformance'), {'employe': e, 'annee': self.today.year},
                 evaluateur=self.admin, periode='annuelle', note_globale=Decimal('4.0'),
                 points_forts='Rigueur, esprit d\'équipe', axes_amelioration='Délégation et reporting',
                 date_evaluation=self.today - timedelta(days=10))
            n += 4
        if employes:
            make(M('rh_projet.OccurrenceSpeciale'), {'employe': employes[0], 'type_occurrence': 'naissance'},
                 date_evenement=self.today - timedelta(days=30))
            n += 1
        return n

    # ── Finance ──────────────────────────────────────────────────────────────
    def finance(self):
        n = 0
        Compte, Mvt = M('gestion_financiere.CompteBancaire'), M('gestion_financiere.MouvementBancaire')
        comptes = []
        for code, intitule, banque, solde in [
            ('CPT-001', 'Compte principal projet', 'Société Générale CI', 85000000),
            ('CPT-002', 'Compte bailleur UE', 'Ecobank CI', 42000000),
        ]:
            comptes.append(make(Compte, {'code': code}, intitule=intitule, banque=banque, devise='XOF',
                                solde_initial=Decimal(solde), solde_actuel=Decimal(solde),
                                date_ouverture=self.today - timedelta(days=400), actif=True,
                                responsable=self.admin))
            n += 1
        for c in comptes:
            solde = c.solde_initial
            for k, (typ, lib, mt) in enumerate([
                ('credit', 'Tranche bailleur', 15000000),
                ('debit', 'Paiement fournisseur', 3200000),
                ('debit', 'Salaires du mois', 6500000),
                ('debit', 'Frais de mission', 850000),
            ]):
                solde = solde + Decimal(mt) if typ == 'credit' else solde - Decimal(mt)
                make(Mvt, {'compte': c, 'libelle': f'{lib} #{k + 1}'}, date_operation=self.today - timedelta(days=40 - k * 8),
                     type_mouvement=typ, montant=Decimal(mt), solde_apres=solde, saisi_par=self.admin)
                n += 1
            make(M('gestion_financiere.RapprochementBancaire'), {'compte': c, 'periode_debut': self.today.replace(day=1) - timedelta(days=30)},
                 periode_fin=self.today.replace(day=1) - timedelta(days=1), solde_releve=solde)
            n += 1
        # Budgets par projet (écran « Budgets projet ») + lignes + dépenses simplifiées
        Budget, Ligne, Dep = (M('gestion_financiere.BudgetProjet'), M('gestion_financiere.LigneBudgetaireLegacy'),
                              M('gestion_financiere.DepenseLegacy'))
        for pi, projet in enumerate(M('programmes_projets.Projet').objects.all()[:4]):
            bp = make(Budget, {'projet': projet, 'exercice': self.today.year},
                      montant_initial=Decimal(120000000 + pi * 15000000), statut='approuve',
                      date_approbation=self.now - timedelta(days=60), approuve_par=self.admin,
                      notes='Budget annuel simplifié du projet')
            n += 1
            lignes = []
            for code, lib, cat, prevu in [
                ('L01', 'Ressources humaines', 'personnel', 45000000),
                ('L02', 'Équipements et fournitures', 'equipements', 30000000),
                ('L03', 'Missions et déplacements', 'missions', 15000000),
                ('L04', 'Formation et sensibilisation', 'formations', 20000000),
            ]:
                lignes.append(make(Ligne, {'budget': bp, 'code': code}, libelle=lib, categorie=cat,
                                   montant_prevu=Decimal(prevu), montant_engage=Decimal(prevu) * Decimal('0.6'),
                                   montant_depense=Decimal(prevu) * Decimal('0.4')))
                n += 1
            for k, l in enumerate(lignes):
                make(Dep, {'reference': f'DS-{self.today.year}-{pi + 1}{k + 1:02d}'}, ligne=l,
                     libelle=f'Dépense {l.libelle.lower()}', montant=l.montant_prevu * Decimal('0.1'),
                     date_depense=self.today - timedelta(days=10 + k * 9), fournisseur='Fournisseur Démo SARL',
                     numero_facture=f'FAC-{pi + 1}{k + 1:03d}', saisi_par=self.admin,
                     statut='approuve' if k % 2 == 0 else 'soumis')
                n += 1
        # Flux de trésorerie du mois courant (alimente « Trésorerie — mois courant »)
        plan = M('gestion_financiere.PlanTresorerie').objects.filter(exercice=self.today.year).first()
        if plan:
            Flux = M('gestion_financiere.LigneTresorerie')
            for typ, cat, lib, prevu, realise in [
                ('entrant', 'financement', 'Décaissement tranche bailleur', 60000000, 45000000),
                ('sortant', 'salaire', 'Salaires et charges du mois', 22000000, 21500000),
                ('sortant', 'mission', 'Missions de supervision', 6500000, 3000000),
            ]:
                make(Flux, {'plan': plan, 'libelle': lib, 'mois': self.today.month, 'annee': self.today.year},
                     type_flux=typ, categorie=cat, montant_prevu=Decimal(prevu), montant_realise=Decimal(realise))
                n += 1
        # Une ligne budgétaire en dépassement (alimente « Dépassements budgétaires »)
        budget = M('gestion_financiere.Budget').objects.filter(statut='en_execution').first()
        if budget:
            make(M('gestion_financiere.LigneBudgetaire'), {'budget': budget, 'code': 'DEP-DEMO'},
                 libelle='Carburant et entretien véhicules', categorie='vehicules',
                 montant_prevu=Decimal('5000000'), montant_engage=Decimal('6200000'),
                 montant_depense=Decimal('4000000'), ordre=99)
            n += 1
        Convention, Bailleur = M('gestion_financiere.Convention').objects.first(), M('gouvernance.Bailleur').objects.all()[:2]
        if Convention:
            for b in Bailleur:
                make(M('gestion_financiere.Cofinancement'), {'convention': Convention, 'bailleur': b},
                     montant=Decimal('25000000'), devise='XOF', pourcentage=Decimal('20'), montant_recu=Decimal('10000000'))
                n += 1
        return n

    # ── Logistique ───────────────────────────────────────────────────────────
    def logistique(self):
        n = 0
        Vehicule = M('logistique.Vehicule').objects.all()[:3]
        projet = M('programmes_projets.Projet').objects.first()
        for i, v in enumerate(Vehicule):
            make(M('logistique.MissionVehicule'), {'vehicule': v, 'objet': f'Mission de supervision terrain #{i + 1}'},
                 lieu_depart='Abidjan', lieu_arrivee=['Bouaké', 'Man', 'Korhogo'][i % 3],
                 date_depart=self.now - timedelta(days=12 - i * 3), conducteur=self.admin, projet=projet,
                 km_depart=45000 + i * 1000, autorise_par=self.admin)
            make(M('logistique.EntretienVehicule'), {'vehicule': v, 'date_entretien': self.today - timedelta(days=45 + i * 5)},
                 description='Vidange, filtres et contrôle freins', prestataire='Garage Central', cout=Decimal('185000'),
                 effectue_par=self.admin)
            n += 2
        for a in M('logistique.ArticleStock').objects.all()[:4]:
            make(M('logistique.MouvementStock'), {'article': a, 'type_mouvement': 'entree', 'reference_document': 'BL-2026-001'},
                 quantite=Decimal('50'), motif='Réapprovisionnement', effectue_par=self.admin)
            make(M('logistique.MouvementStock'), {'article': a, 'type_mouvement': 'sortie', 'reference_document': 'BS-2026-001'},
                 quantite=Decimal('12'), motif='Distribution aux équipes terrain', effectue_par=self.admin)
            n += 2
        return n

    # ── Marchés publics ──────────────────────────────────────────────────────
    def marches(self):
        n = 0
        for i, c in enumerate(M('marches_publics.ContratMarche').objects.all()[:2], start=1):
            make(M('marches_publics.AvenantContrat'), {'contrat': c, 'numero_avenant': 1},
                 description='Prolongation du délai d\'exécution de 30 jours', motif='Retard d\'approvisionnement',
                 extension_jours=30, statut='signe' if i == 1 else 'brouillon',
                 date_signature=self.today - timedelta(days=5))
            n += 1
        return n

    # ── Diligences ───────────────────────────────────────────────────────────
    def diligences(self):
        n = 0
        for d in M('diligences.Diligence').objects.all()[:5]:
            make(M('diligences.RelanceDiligence'), {'diligence': d, 'message': 'Rappel : merci de traiter cette diligence dans les meilleurs délais.'})
            make(M('diligences.CommentaireDiligence'), {'diligence': d, 'texte': 'Dossier pris en charge, retour prévu cette semaine.'},
                 auteur=self.admin)
            n += 2
        return n

    # ── Exécution ────────────────────────────────────────────────────────────
    def execution(self):
        n = 0
        for t in M('execution.Tache').objects.all()[:8]:
            make(M('execution.CommentaireTache'), {'tache': t, 'contenu': 'Point d\'avancement : les travaux se déroulent conformément au planning.'},
                 auteur=self.admin)
            n += 1
        for i, m in enumerate(M('execution.Mission').objects.all()[:4], start=1):
            make(M('execution.OrdreMission'), {'mission': m}, numero=f'OM-{self.today.year}-{i:03d}',
                 date_emission=self.today - timedelta(days=i), signataire=self.admin,
                 contenu='Autorisation de déplacement pour mission de terrain.')
            n += 1
        for a in M('execution.ActiviteExecution').objects.all()[:5]:
            make(M('execution.RapportActivite'), {'activite': a, 'periode': 'mensuel', 'date_rapport': self.today.replace(day=1)},
                 taux_realisation=Decimal('60'), observations='Activité en cours conformément au plan.',
                 recommandations='Renforcer le suivi hebdomadaire.', redacteur=self.admin)
            n += 1
        return n

    # ── Partenaires & bailleurs ──────────────────────────────────────────────
    def partenaires(self):
        n = 0
        for i, p in enumerate(M('partenaires_bailleurs.Partenaire').objects.all()[:4], start=1):
            make(M('partenaires_bailleurs.ContactPartenaire'), {'partenaire': p, 'nom': f'Contact{i}'},
                 prenom='Responsable', role='Point focal', email=f'contact{i}@partenaire-demo.org',
                 telephone=f'+22507000000{i}', est_principal=True)
            n += 1
        for c in M('partenaires_bailleurs.Convention').objects.all()[:2]:
            make(M('partenaires_bailleurs.RenouvellementConvention'), {'convention': c},
                 nouvelle_date_fin=self.today + timedelta(days=365), motif='Prolongation pour une année supplémentaire',
                 effectue_par=self.admin)
            n += 1
        return n

    # ── Collaboration ────────────────────────────────────────────────────────
    def collaboration(self):
        n = 0
        Activite = M('collaboration.ActiviteRecente')
        for i, u in enumerate(self.users[:6]):
            typ = ['document', 'courrier', 'livrable', 'tache', 'reunion', 'budget'][i % 6]
            make(Activite, {'utilisateur': u, 'type_activite': typ, 'titre': f'Activité récente : {typ}'})
            n += 1
        evt = M('collaboration.Evenement').objects.first()
        if evt:
            for lib, mt in [('Location de salle', 450000), ('Restauration', 280000), ('Supports de communication', 120000)]:
                make(M('collaboration.DepenseEvenement'), {'evenement': evt, 'libelle': lib}, montant=Decimal(mt))
                n += 1
        return n

    # ── Risques ──────────────────────────────────────────────────────────────
    def risques(self):
        n = 0
        for p in M('programmes_projets.Projet').objects.all()[:3]:
            make(M('programmes_projets.RisqueProjet'), {'projet': p, 'titre': 'Retard dans la mobilisation des fonds'},
                 description='Les décaissements du bailleur pourraient être retardés.', probabilite='moyen', impact='majeur')
            n += 1
        tend = ['stable', 'croissant', 'decroissant']
        for i, r in enumerate(M('suivi_evaluation.RegistreRisque').objects.all()[:6]):
            make(M('suivi_evaluation.SuiviRisque'), {'risque': r, 'date_suivi': self.today - timedelta(days=7 * (i % 3))},
                 probabilite=2 + i % 3, impact=3 + i % 2, statut='surveille', tendance=tend[i % 3],
                 observations='Risque suivi en revue mensuelle.', suivi_par=self.admin)
            n += 1
        return n

    # ── Courrier administratif ───────────────────────────────────────────────
    def courrier(self):
        n = 0
        for p in M('courrier_administratif.Parapheur').objects.all()[:3]:
            etape = M('courrier_administratif.EtapeCircuit').objects.first()
            make(M('courrier_administratif.VisaParapheur'), {'parapheur': p, 'ordre': 1},
                 etape=etape, validateur=self.admin, commentaire='Visa accordé.', date_visa=self.now)
            n += 1
        return n
