from django.db import models
from django.conf import settings
from django.utils import timezone


# ─── M34 : Tableaux de bord décisionnels ─────────────────────────────────────

class TableauBord(models.Model):
    TYPE_CHOICES = [
        ('direction_generale', 'Direction Générale'),
        ('coordonnateur', 'Coordonnateur Programme'),
        ('responsable_programme', 'Responsable Programme'),
        ('chef_projet', 'Chef de Projet'),
        ('finance', 'Finance'),
        ('suivi_evaluation', 'Suivi & Évaluation'),
        ('logistique', 'Logistique'),
        ('rh', 'Ressources Humaines'),
        ('personnalise', 'Personnalisé'),
    ]

    nom = models.CharField(max_length=200)
    type_dashboard = models.CharField(max_length=25, choices=TYPE_CHOICES, default='personnalise')
    description = models.TextField(blank=True)
    est_public = models.BooleanField(default=False)
    est_defaut = models.BooleanField(default=False)
    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tableaux_bord'
    )
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tableaux_bord'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tableaux_bord'
    )
    configuration = models.JSONField(default=dict, blank=True,
                                     help_text="Config layout: {colonnes, theme, filtres_globaux}")
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tableau de bord'
        ordering = ['-est_defaut', 'nom']

    def __str__(self):
        return f"[{self.get_type_dashboard_display()}] {self.nom}"


class WidgetTableauBord(models.Model):
    TYPE_CHOICES = [
        ('kpi_card', 'Carte KPI'),
        ('graphique_barres', 'Graphique en barres'),
        ('graphique_lignes', 'Graphique en lignes'),
        ('graphique_camembert', 'Graphique camembert'),
        ('graphique_jauge', 'Jauge'),
        ('carte_sig', 'Carte géographique'),
        ('tableau', 'Tableau de données'),
        ('gantt', 'Diagramme Gantt'),
        ('heatmap', 'Heatmap'),
        ('liste_alertes', 'Liste des alertes'),
        ('liste_taches', 'Liste des tâches'),
        ('risques', 'Matrice des risques'),
        ('texte', 'Bloc texte'),
    ]
    SOURCE_CHOICES = [
        ('programmes_projets', 'Programmes & Projets'),
        ('suivi_evaluation', 'Suivi & Évaluation'),
        ('gestion_financiere', 'Gestion Financière'),
        ('execution', 'Exécution'),
        ('risques', 'Risques'),
        ('courriers', 'Courriers'),
        ('ged', 'GED'),
        ('rh', 'RH Projet'),
        ('logistique', 'Logistique'),
        ('custom_sql', 'Requête personnalisée'),
    ]

    tableau_bord = models.ForeignKey(TableauBord, on_delete=models.CASCADE, related_name='widgets')
    titre = models.CharField(max_length=200)
    type_widget = models.CharField(max_length=25, choices=TYPE_CHOICES)
    source_donnees = models.CharField(max_length=25, choices=SOURCE_CHOICES, default='programmes_projets')

    # Position sur le tableau de bord (grille)
    colonne = models.IntegerField(default=0)
    ligne = models.IntegerField(default=0)
    largeur = models.IntegerField(default=4, help_text="Nombre de colonnes (1-12)")
    hauteur = models.IntegerField(default=3, help_text="Nombre de rangées")

    configuration = models.JSONField(default=dict, blank=True,
                                     help_text="Config: {metrique, filtre, couleur, icone, format}")
    filtre_projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True
    )
    filtre_programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True
    )
    actualisation_minutes = models.IntegerField(default=60,
                                                help_text="Intervalle d'actualisation en minutes")
    actif = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Widget tableau de bord'
        ordering = ['ligne', 'colonne', 'ordre']

    def __str__(self):
        return f"{self.tableau_bord.nom} — {self.titre}"

    def calculer_valeur(self):
        """Calcule la valeur actuelle du widget selon sa source."""
        config = self.configuration or {}
        metrique = config.get('metrique', '')
        projet_id = self.filtre_projet_id
        programme_id = self.filtre_programme_id

        try:
            if self.source_donnees == 'programmes_projets':
                from programmes_projets.models import Projet, Programme
                if metrique == 'projets_actifs':
                    qs = Projet.objects.filter(statut='en_cours')
                    return {'valeur': qs.count(), 'unite': 'projets'}
                elif metrique == 'budget_total':
                    from django.db.models import Sum
                    total = Programme.objects.filter(statut='en_cours').aggregate(
                        t=Sum('budget_total'))['t'] or 0
                    return {'valeur': float(total), 'unite': 'FCFA'}

            elif self.source_donnees == 'suivi_evaluation':
                from suivi_evaluation.models import Indicateur
                qs = Indicateur.objects.filter(actif=True)
                if projet_id:
                    qs = qs.filter(projet_id=projet_id)
                if metrique == 'taux_realisation_moyen':
                    indicateurs = list(qs)
                    if not indicateurs:
                        return {'valeur': 0, 'unite': '%'}
                    taux = sum(i.taux_realisation for i in indicateurs) / len(indicateurs)
                    return {'valeur': round(taux, 1), 'unite': '%'}
                elif metrique == 'indicateurs_atteints':
                    return {'valeur': qs.filter(statut='atteint').count(), 'unite': 'indicateurs'}

            elif self.source_donnees == 'risques':
                from suivi_evaluation.models import RegistreRisque
                qs = RegistreRisque.objects.all()
                if projet_id:
                    qs = qs.filter(projet_id=projet_id)
                return {'valeur': qs.filter(niveau_risque='critique').count(), 'unite': 'risques'}

            return {'valeur': None, 'unite': ''}
        except Exception:
            return {'valeur': None, 'unite': '', 'erreur': 'Calcul impossible'}


class PartageTableauBord(models.Model):
    NIVEAU_CHOICES = [
        ('lecture', 'Lecture seule'),
        ('modification', 'Modification'),
    ]

    tableau_bord = models.ForeignKey(TableauBord, on_delete=models.CASCADE, related_name='partages')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tableaux_partages'
    )
    niveau = models.CharField(max_length=15, choices=NIVEAU_CHOICES, default='lecture')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Partage tableau de bord'
        unique_together = ['tableau_bord', 'utilisateur']


# ─── M35 : Business Intelligence & Data Warehouse ────────────────────────────

class DataWarehouseSnapshot(models.Model):
    """Snapshot consolidé des données pour le DW."""
    TYPE_CHOICES = [
        ('programmes', 'Programmes'),
        ('projets', 'Projets'),
        ('finances', 'Finances'),
        ('indicateurs', 'Indicateurs S&E'),
        ('ged', 'GED'),
        ('risques', 'Risques'),
        ('rh', 'RH Projet'),
        ('courriers', 'Courriers'),
        ('full', 'Consolidation complète'),
    ]

    type_snapshot = models.CharField(max_length=20, choices=TYPE_CHOICES)
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    donnees = models.JSONField(default=dict)
    taille_ko = models.IntegerField(default=0)
    nb_enregistrements = models.IntegerField(default=0)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='snapshots_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    valide = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Snapshot Data Warehouse'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_snapshot_display()}] {self.periode_debut} → {self.periode_fin}"


class RapportBI(models.Model):
    TYPE_CHOICES = [
        ('performance_projets', 'Performance Projets'),
        ('performance_programmes', 'Performance Programmes'),
        ('analyse_budgetaire', 'Analyse Budgétaire'),
        ('analyse_beneficiaires', 'Analyse Bénéficiaires'),
        ('analyse_geographique', 'Analyse Géographique'),
        ('analyse_risques', 'Analyse Risques'),
        ('rapport_executif', 'Rapport Exécutif'),
        ('rapport_bailleur', 'Rapport Bailleur'),
        ('rapport_consolidé', 'Rapport Consolidé'),
        ('rapport_predictif', 'Rapport Prédictif'),
    ]
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML interactif'),
        ('powerbi', 'Power BI'),
        ('tableau', 'Tableau'),
    ]
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('genere', 'Généré'),
        ('valide', 'Validé'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
    ]
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
        ('ad_hoc', 'Ad hoc'),
    ]

    titre = models.CharField(max_length=300)
    type_rapport = models.CharField(max_length=30, choices=TYPE_CHOICES)
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default='mensuel')
    format_export = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon')

    date_debut_periode = models.DateField(null=True, blank=True)
    date_fin_periode = models.DateField(null=True, blank=True)

    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_bi'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_bi'
    )

    parametres = models.JSONField(default=dict, blank=True)
    donnees_calculees = models.JSONField(default=dict, blank=True)
    fichier = models.FileField(upload_to='bi/rapports/%Y/%m/', null=True, blank=True)

    genere_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='rapports_bi_generes'
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapports_bi_valides'
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    genere_par_ia = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapport BI'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_rapport_display()}] {self.titre}"

    def generer_donnees(self):
        """Calcule et consolide les données du rapport."""
        from django.db.models import Sum, Count, Avg
        from programmes_projets.models import Projet, Programme

        donnees = {}
        if self.type_rapport == 'performance_projets':
            qs = Projet.objects.all()
            if self.projet:
                qs = qs.filter(id=self.projet_id)
            if self.programme:
                qs = qs.filter(programme=self.programme)

            donnees = {
                'total_projets': qs.count(),
                'par_statut': {s: qs.filter(statut=s).count()
                               for s in ['en_cours', 'termine', 'suspendu', 'en_retard']},
                'taux_completion_moyen': round(
                    qs.aggregate(avg=Avg('taux_avancement'))['avg'] or 0, 1
                ),
            }

        elif self.type_rapport == 'analyse_budgetaire':
            from gestion_financiere.models import LigneBudgetaire
            from django.db.models import Sum
            lignes = LigneBudgetaire.objects.all()
            if self.projet:
                lignes = lignes.filter(budget__projet=self.projet)
            if self.programme:
                lignes = lignes.filter(budget__projet__programme=self.programme)

            donnees = {
                'budget_total': float(lignes.aggregate(t=Sum('montant_prevu'))['t'] or 0),
                'budget_realise': float(lignes.aggregate(t=Sum('montant_realise'))['t'] or 0),
                'par_categorie': list(
                    lignes.values('categorie').annotate(
                        prevu=Sum('montant_prevu'),
                        realise=Sum('montant_realise')
                    )[:10]
                ),
            }
            total = donnees['budget_total']
            realise = donnees['budget_realise']
            donnees['taux_execution'] = round((realise / total * 100) if total > 0 else 0, 1)

        elif self.type_rapport == 'analyse_risques':
            from suivi_evaluation.models import RegistreRisque
            qs = RegistreRisque.objects.all()
            if self.projet:
                qs = qs.filter(projet=self.projet)
            if self.programme:
                qs = qs.filter(programme=self.programme)

            donnees = {
                'total': qs.count(),
                'par_niveau': {n: qs.filter(niveau_risque=n).count()
                               for n in ['critique', 'important', 'modere', 'faible']},
                'par_categorie': {c: qs.filter(categorie=c).count()
                                  for c, _ in RegistreRisque.CATEGORIE_CHOICES},
                'non_traites': qs.filter(statut='identifie').count(),
            }

        elif self.type_rapport == 'rapport_executif':
            from suivi_evaluation.models import Indicateur, RegistreRisque
            projets = Projet.objects.filter(statut='en_cours')
            programmes = Programme.objects.filter(statut='en_cours')
            indicateurs = Indicateur.objects.filter(actif=True)

            donnees = {
                'programmes_actifs': programmes.count(),
                'projets_actifs': projets.count(),
                'indicateurs_atteints': indicateurs.filter(statut='atteint').count(),
                'indicateurs_total': indicateurs.count(),
                'risques_critiques': RegistreRisque.objects.filter(niveau_risque='critique').count(),
                'taux_realisation_moyen': round(
                    sum(i.taux_realisation for i in indicateurs) / indicateurs.count()
                    if indicateurs.count() > 0 else 0, 1
                ),
            }

        else:
            donnees = {'message': f"Rapport {self.get_type_rapport_display()} généré."}

        donnees['genere_le'] = timezone.now().isoformat()
        self.donnees_calculees = donnees
        self.statut = 'genere'
        self.save(update_fields=['donnees_calculees', 'statut'])
        return donnees


class DatamartFinance(models.Model):
    """Datamart finances - données agrégées pour BI."""
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='datamart_finances'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='datamart_finances'
    )
    annee = models.IntegerField()
    mois = models.IntegerField()
    trimestre = models.IntegerField()

    budget_prevu = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    budget_engage = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    budget_realise = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    taux_execution = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    nb_transactions = models.IntegerField(default=0)
    categorie_principale = models.CharField(max_length=50, blank=True)
    bailleur = models.CharField(max_length=200, blank=True)
    zone_geographique = models.CharField(max_length=200, blank=True)

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datamart Finance'
        unique_together = ['programme', 'projet', 'annee', 'mois']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"Finance {self.programme} — {self.annee}/{self.mois:02d}"


class DatamartSE(models.Model):
    """Datamart S&E - indicateurs agrégés."""
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE,
        related_name='datamart_se'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='datamart_se'
    )
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True)

    nb_indicateurs = models.IntegerField(default=0)
    nb_atteints = models.IntegerField(default=0)
    nb_non_atteints = models.IntegerField(default=0)
    taux_realisation_moyen = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    nb_beneficiaires_hommes = models.IntegerField(default=0)
    nb_beneficiaires_femmes = models.IntegerField(default=0)
    nb_beneficiaires_total = models.IntegerField(default=0)

    zone_geographique = models.CharField(max_length=200, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datamart S&E'
        unique_together = ['programme', 'projet', 'annee', 'trimestre']
        ordering = ['-annee', '-trimestre']

    def __str__(self):
        q = f"T{self.trimestre}" if self.trimestre else ""
        return f"S&E {self.programme} — {self.annee}{q}"


class DatamartRH(models.Model):
    """Datamart RH Projet - effectifs et missions agrégés."""
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.CASCADE, related_name='datamart_rh', null=True, blank=True
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True, related_name='datamart_rh'
    )
    annee = models.IntegerField()
    mois = models.IntegerField(null=True, blank=True)

    nb_agents = models.IntegerField(default=0)
    nb_consultants = models.IntegerField(default=0)
    nb_missions = models.IntegerField(default=0)
    nb_contrats_actifs = models.IntegerField(default=0)
    cout_total_rh = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    taux_occupation_moyen = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    zone_geographique = models.CharField(max_length=200, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datamart RH'
        unique_together = ['programme', 'projet', 'annee', 'mois']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"RH {self.programme or 'Global'} — {self.annee}"


class DatamartCourrier(models.Model):
    """Datamart Courriers - flux courriers agrégés."""
    annee = models.IntegerField()
    mois = models.IntegerField()
    trimestre = models.IntegerField()

    nb_courriers_entrants = models.IntegerField(default=0)
    nb_courriers_sortants = models.IntegerField(default=0)
    nb_courriers_internes = models.IntegerField(default=0)
    nb_en_attente = models.IntegerField(default=0)
    nb_traites = models.IntegerField(default=0)
    delai_traitement_moyen = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                                  help_text="Délai moyen en jours")

    direction = models.CharField(max_length=200, blank=True)
    type_dominant = models.CharField(max_length=50, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datamart Courrier'
        unique_together = ['annee', 'mois', 'direction']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"Courriers {self.annee}/{self.mois:02d}"


class DatamartGED(models.Model):
    """Datamart GED - documents agrégés."""
    annee = models.IntegerField()
    mois = models.IntegerField()
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True, related_name='datamart_ged'
    )

    nb_documents = models.IntegerField(default=0)
    nb_valides = models.IntegerField(default=0)
    nb_en_attente = models.IntegerField(default=0)
    taille_totale_mo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    type_dominant = models.CharField(max_length=50, blank=True)
    nb_telechargements = models.IntegerField(default=0)

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datamart GED'
        unique_together = ['annee', 'mois', 'programme']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"GED {self.annee}/{self.mois:02d}"


class DatamartRisque(models.Model):
    """Datamart Risques - registre des risques agrégé."""
    annee = models.IntegerField()
    trimestre = models.IntegerField(null=True, blank=True)
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True, related_name='datamart_risques'
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True, related_name='datamart_risques'
    )

    nb_risques_total = models.IntegerField(default=0)
    nb_critiques = models.IntegerField(default=0)
    nb_eleves = models.IntegerField(default=0)
    nb_moderes = models.IntegerField(default=0)
    nb_faibles = models.IntegerField(default=0)
    nb_maitrise = models.IntegerField(default=0)
    nb_nouveaux = models.IntegerField(default=0)
    score_risque_moyen = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Datamart Risque'
        unique_together = ['annee', 'trimestre', 'programme', 'projet']
        ordering = ['-annee', '-trimestre']

    def __str__(self):
        q = f"T{self.trimestre}" if self.trimestre else ""
        return f"Risques {self.annee}{q}"


class ConnecteurBI(models.Model):
    """Connecteurs vers outils BI externes."""
    TYPE_CHOICES = [
        ('powerbi', 'Microsoft Power BI'),
        ('tableau', 'Tableau'),
        ('metabase', 'Metabase'),
        ('superset', 'Apache Superset'),
        ('grafana', 'Grafana'),
        ('custom_api', 'API personnalisée'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('erreur', 'Erreur'),
    ]

    nom = models.CharField(max_length=200)
    type_outil = models.CharField(max_length=20, choices=TYPE_CHOICES)
    url_endpoint = models.URLField(blank=True)
    configuration = models.JSONField(default=dict, blank=True,
                                     help_text="Config: {api_key, workspace, dataset_id}")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    derniere_synchro = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='connecteurs_bi'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Connecteur BI'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_outil_display()})"


class KPIPersonnalise(models.Model):
    """KPI personnalisé avec formule de calcul."""
    UNITE_CHOICES = [
        ('nombre', 'Nombre'),
        ('pourcentage', 'Pourcentage (%)'),
        ('montant', 'Montant (FCFA)'),
        ('jours', 'Jours'),
        ('autre', 'Autre'),
    ]
    STATUT_CALCUL_CHOICES = [
        ('ok', 'OK'),
        ('erreur', 'Erreur'),
        ('non_calcule', 'Non calculé'),
    ]

    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    formule = models.TextField(help_text="Formule de calcul (Python eval)")
    source_donnees = models.CharField(max_length=25,
                                      choices=WidgetTableauBord.SOURCE_CHOICES,
                                      default='programmes_projets')
    unite = models.CharField(max_length=15, choices=UNITE_CHOICES, default='nombre')
    valeur_actuelle = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    statut_calcul = models.CharField(max_length=15, choices=STATUT_CALCUL_CHOICES,
                                     default='non_calcule')
    seuil_alerte_bas = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    seuil_alerte_haut = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    icone = models.CharField(max_length=50, blank=True)
    couleur = models.CharField(max_length=7, default='#3388ff')
    programme = models.ForeignKey(
        'programmes_projets.Programme', on_delete=models.SET_NULL, null=True, blank=True
    )
    projet = models.ForeignKey(
        'programmes_projets.Projet', on_delete=models.SET_NULL, null=True, blank=True
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='kpis_personnalises'
    )
    derniere_maj = models.DateTimeField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'KPI personnalisé'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} = {self.valeur_actuelle} {self.unite}"
