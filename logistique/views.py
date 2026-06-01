from django.db import transaction
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    Vehicule, MissionVehicule, EntretienVehicule,
    Equipement, Magasin, ArticleStock, LigneStock, MouvementStock,
)
from .serializers import (
    VehiculeListSerializer, VehiculeDetailSerializer,
    MissionVehiculeListSerializer, MissionVehiculeDetailSerializer,
    EntretienVehiculeSerializer,
    EquipementListSerializer, EquipementDetailSerializer,
    MagasinSerializer,
    ArticleStockSerializer, LigneStockSerializer,
    MouvementStockListSerializer, MouvementStockCreateSerializer,
    MouvementBatchSerializer,
)
from .filters import (
    VehiculeFilter, MissionVehiculeFilter, EntretienVehiculeFilter,
    EquipementFilter, MagasinFilter, ArticleStockFilter,
    LigneStockFilter, MouvementStockFilter,
)

CanReadLog = HasModulePermission.for_module('logistique', 'peut_lire')
CanEditLog = HasModulePermission.for_module('logistique', 'peut_modifier')


# ─── M38 : Parc automobile ────────────────────────────────────────────────────

class VehiculeViewSet(viewsets.ModelViewSet):
    queryset = Vehicule.objects.select_related('projet', 'programme').prefetch_related('missions').order_by('immatriculation')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VehiculeFilter
    search_fields = ['immatriculation', 'marque', 'modele', 'notes']
    ordering_fields = ['immatriculation', 'marque', 'statut', 'kilometrage_actuel', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'alertes']:
            return [CanReadLog()]
        return [CanEditLog()]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehiculeListSerializer
        return VehiculeDetailSerializer

    @action(detail=False, methods=['get'])
    def alertes(self, request):
        """Retourne les véhicules avec assurance ou vignette expirée, ou entretien imminent."""
        today = timezone.now().date()
        horizon = request.query_params.get('horizon_jours', 30)
        try:
            horizon = int(horizon)
        except (ValueError, TypeError):
            horizon = 30
        from datetime import timedelta
        date_limite = today + timedelta(days=horizon)

        qs = Vehicule.objects.exclude(statut='reforme')
        assurance_expiree = qs.filter(date_expiration_assurance__lt=today)
        vignette_expiree = qs.filter(date_expiration_vignette__lt=today)
        assurance_bientot = qs.filter(
            date_expiration_assurance__gte=today,
            date_expiration_assurance__lte=date_limite,
        )
        vignette_bientot = qs.filter(
            date_expiration_vignette__gte=today,
            date_expiration_vignette__lte=date_limite,
        )
        entretien_imminent = qs.filter(
            date_prochain_entretien__lte=date_limite
        )
        return Response({
            'assurance_expiree': VehiculeListSerializer(assurance_expiree, many=True).data,
            'vignette_expiree': VehiculeListSerializer(vignette_expiree, many=True).data,
            'assurance_bientot': VehiculeListSerializer(assurance_bientot, many=True).data,
            'vignette_bientot': VehiculeListSerializer(vignette_bientot, many=True).data,
            'entretien_imminent': VehiculeListSerializer(entretien_imminent, many=True).data,
        })

    @action(detail=True, methods=['post'])
    def demarrer_mission(self, request, pk=None):
        """Passe un véhicule en statut en_mission."""
        vehicule = self.get_object()
        if vehicule.statut != 'disponible':
            return Response(
                {'detail': f'Le véhicule est actuellement "{vehicule.get_statut_display()}" et ne peut pas être mis en mission.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vehicule.statut = 'en_mission'
        vehicule.save(update_fields=['statut', 'updated_at'])
        return Response(VehiculeDetailSerializer(vehicule).data)

    @action(detail=True, methods=['post'])
    def terminer_mission(self, request, pk=None):
        """Remet un véhicule à disponible après mission."""
        vehicule = self.get_object()
        if vehicule.statut != 'en_mission':
            return Response(
                {'detail': 'Le véhicule n\'est pas en mission.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vehicule.statut = 'disponible'
        vehicule.save(update_fields=['statut', 'updated_at'])
        return Response(VehiculeDetailSerializer(vehicule).data)


class MissionVehiculeViewSet(viewsets.ModelViewSet):
    queryset = MissionVehicule.objects.select_related(
        'vehicule', 'conducteur', 'projet', 'activite', 'autorise_par'
    ).order_by('-date_depart')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MissionVehiculeFilter
    search_fields = ['objet', 'lieu_depart', 'lieu_arrivee', 'vehicule__immatriculation']
    ordering_fields = ['date_depart', 'statut', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadLog()]
        return [CanEditLog()]

    def get_serializer_class(self):
        if self.action == 'list':
            return MissionVehiculeListSerializer
        return MissionVehiculeDetailSerializer

    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        """Démarre la mission: statut → en_cours, met à jour km_depart."""
        mission = self.get_object()
        if mission.statut != 'planifiee':
            return Response(
                {'detail': f'Impossible de démarrer une mission en statut "{mission.get_statut_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        km_depart = request.data.get('km_depart', mission.vehicule.kilometrage_actuel)
        mission.statut = 'en_cours'
        mission.km_depart = km_depart
        mission.save(update_fields=['statut', 'km_depart'])

        vehicule = mission.vehicule
        if vehicule.statut == 'disponible':
            vehicule.statut = 'en_mission'
            vehicule.save(update_fields=['statut', 'updated_at'])

        return Response(MissionVehiculeDetailSerializer(mission).data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """Termine la mission: statut → terminee, met à jour km_retour et km véhicule."""
        mission = self.get_object()
        if mission.statut != 'en_cours':
            return Response(
                {'detail': 'Seule une mission en cours peut être terminée.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        km_retour = request.data.get('km_retour')
        if km_retour is None:
            return Response(
                {'detail': 'Le kilométrage retour est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        km_retour = int(km_retour)
        if km_retour < mission.km_depart:
            return Response(
                {'detail': 'Le km retour ne peut pas être inférieur au km départ.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        carburant = request.data.get('carburant_litres', mission.carburant_litres)
        cout_carburant = request.data.get('cout_carburant', mission.cout_carburant)
        observations = request.data.get('observations', mission.observations)

        mission.statut = 'terminee'
        mission.km_retour = km_retour
        mission.date_retour_reelle = timezone.now()
        mission.carburant_litres = carburant
        mission.cout_carburant = cout_carburant
        mission.observations = observations
        mission.save()

        vehicule = mission.vehicule
        vehicule.kilometrage_actuel = km_retour
        vehicule.statut = 'disponible'
        vehicule.save(update_fields=['kilometrage_actuel', 'statut', 'updated_at'])

        return Response(MissionVehiculeDetailSerializer(mission).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annule une mission planifiée."""
        mission = self.get_object()
        if mission.statut not in ('planifiee', 'en_cours'):
            return Response(
                {'detail': 'Seules les missions planifiées ou en cours peuvent être annulées.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mission.statut = 'annulee'
        mission.save(update_fields=['statut'])
        if mission.vehicule.statut == 'en_mission':
            mission.vehicule.statut = 'disponible'
            mission.vehicule.save(update_fields=['statut', 'updated_at'])
        return Response(MissionVehiculeDetailSerializer(mission).data)


class EntretienVehiculeViewSet(viewsets.ModelViewSet):
    queryset = EntretienVehicule.objects.select_related('vehicule', 'effectue_par').order_by('-date_entretien')
    serializer_class = EntretienVehiculeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EntretienVehiculeFilter
    search_fields = ['vehicule__immatriculation', 'description', 'prestataire']
    ordering_fields = ['date_entretien', 'cout', 'type_entretien']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadLog()]
        return [CanEditLog()]

    def perform_create(self, serializer):
        entretien = serializer.save(effectue_par=self.request.user)
        # Mettre à jour les dates d'entretien du véhicule si nécessaire
        vehicule = entretien.vehicule
        update_fields = []
        if entretien.prochaine_echeance_date and (
            not vehicule.date_prochain_entretien
            or entretien.prochaine_echeance_date < vehicule.date_prochain_entretien
        ):
            vehicule.date_prochain_entretien = entretien.prochaine_echeance_date
            update_fields.append('date_prochain_entretien')
        if entretien.prochaine_echeance_km:
            vehicule.km_prochain_entretien = entretien.prochaine_echeance_km
            update_fields.append('km_prochain_entretien')
        if update_fields:
            update_fields.append('updated_at')
            vehicule.save(update_fields=update_fields)


# ─── M38 : Équipements ────────────────────────────────────────────────────────

class EquipementViewSet(viewsets.ModelViewSet):
    queryset = Equipement.objects.select_related(
        'projet', 'programme', 'affecte_a'
    ).order_by('type_equipement', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EquipementFilter
    search_fields = ['code_inventaire', 'nom', 'marque', 'modele', 'numero_serie', 'lieu']
    ordering_fields = ['code_inventaire', 'nom', 'type_equipement', 'statut', 'date_acquisition']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadLog()]
        return [CanEditLog()]

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipementListSerializer
        return EquipementDetailSerializer

    @action(detail=True, methods=['post'])
    def affecter(self, request, pk=None):
        """Affecte l'équipement à un utilisateur."""
        equipement = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        equipement.affecte_a = user
        equipement.statut = 'affecte'
        lieu = request.data.get('lieu', equipement.lieu)
        equipement.lieu = lieu
        equipement.save(update_fields=['affecte_a', 'statut', 'lieu', 'updated_at'])
        return Response(EquipementDetailSerializer(equipement).data)

    @action(detail=True, methods=['post'])
    def desaffecter(self, request, pk=None):
        """Retire l'affectation de l'équipement."""
        equipement = self.get_object()
        equipement.affecte_a = None
        equipement.statut = 'disponible'
        equipement.save(update_fields=['affecte_a', 'statut', 'updated_at'])
        return Response(EquipementDetailSerializer(equipement).data)

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        equipement = self.get_object()
        nouveau_statut = request.data.get('statut')
        choix = [s[0] for s in Equipement.STATUT_CHOICES]
        if nouveau_statut not in choix:
            return Response(
                {'detail': f'Statut invalide. Choix: {choix}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        equipement.statut = nouveau_statut
        equipement.save(update_fields=['statut', 'updated_at'])
        return Response(EquipementDetailSerializer(equipement).data)


# ─── M38 : Magasins ───────────────────────────────────────────────────────────

class MagasinViewSet(viewsets.ModelViewSet):
    queryset = Magasin.objects.select_related('responsable', 'projet', 'programme').order_by('nom')
    serializer_class = MagasinSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MagasinFilter
    search_fields = ['nom', 'code', 'adresse']
    ordering_fields = ['nom', 'code', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'stock']:
            return [CanReadLog()]
        return [CanEditLog()]

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Retourne tout le stock d'un magasin, avec alertes."""
        magasin = self.get_object()
        lignes = magasin.lignes_stock.select_related('article').all()
        return Response({
            'magasin': MagasinSerializer(magasin).data,
            'lignes': LigneStockSerializer(lignes, many=True).data,
            'nb_articles_alerte': sum(1 for l in lignes if l.est_sous_alerte),
        })


# ─── M38 : Articles & Stock ───────────────────────────────────────────────────

class ArticleStockViewSet(viewsets.ModelViewSet):
    queryset = ArticleStock.objects.order_by('categorie', 'nom')
    serializer_class = ArticleStockSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ArticleStockFilter
    search_fields = ['code', 'nom', 'description', 'categorie']
    ordering_fields = ['code', 'nom', 'categorie', 'prix_unitaire', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'mouvements_recents']:
            return [CanReadLog()]
        return [CanEditLog()]

    @action(detail=True, methods=['get'])
    def mouvements_recents(self, request, pk=None):
        """Retourne les 20 derniers mouvements d'un article."""
        article = self.get_object()
        mouvements = article.mouvements.select_related(
            'magasin_source', 'magasin_destination', 'effectue_par', 'projet'
        ).order_by('-date_mouvement', '-created_at')[:20]
        return Response(MouvementStockListSerializer(mouvements, many=True).data)

    @action(detail=True, methods=['get'])
    def stock_par_magasin(self, request, pk=None):
        """Retourne le stock de cet article dans tous les magasins."""
        article = self.get_object()
        lignes = article.lignes_stock.select_related('magasin').all()
        return Response(LigneStockSerializer(lignes, many=True).data)


class LigneStockViewSet(viewsets.ModelViewSet):
    queryset = LigneStock.objects.select_related('magasin', 'article').order_by('magasin__nom', 'article__nom')
    serializer_class = LigneStockSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LigneStockFilter
    search_fields = ['article__nom', 'article__code', 'magasin__nom']
    ordering_fields = ['quantite', 'valeur_totale', 'updated_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'articles_en_alerte']:
            return [CanReadLog()]
        return [CanEditLog()]

    @action(detail=False, methods=['get'])
    def articles_en_alerte(self, request):
        """Retourne toutes les lignes de stock dont la quantité est sous le seuil d'alerte."""
        magasin_id = request.query_params.get('magasin')
        qs = LigneStock.objects.select_related('magasin', 'article').filter(
            quantite__lte=F('article__stock_alerte')
        )
        if magasin_id:
            qs = qs.filter(magasin_id=magasin_id)
        return Response({
            'count': qs.count(),
            'articles': LigneStockSerializer(qs, many=True).data,
        })


class MouvementStockViewSet(viewsets.ModelViewSet):
    queryset = MouvementStock.objects.select_related(
        'article', 'magasin_source', 'magasin_destination', 'effectue_par', 'projet'
    ).order_by('-date_mouvement', '-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MouvementStockFilter
    search_fields = ['article__nom', 'article__code', 'reference_document', 'motif']
    ordering_fields = ['date_mouvement', 'type_mouvement', 'valeur_totale', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadLog()]
        return [CanEditLog()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MouvementStockCreateSerializer
        return MouvementStockListSerializer

    def perform_create(self, serializer):
        mouvement = serializer.save(effectue_par=self.request.user)
        self._appliquer_mouvement(mouvement)

    def _appliquer_mouvement(self, mouvement):
        """Met à jour les LigneStock correspondantes."""
        with transaction.atomic():
            if mouvement.type_mouvement in ('entree',):
                ligne, _ = LigneStock.objects.get_or_create(
                    magasin=mouvement.magasin_destination,
                    article=mouvement.article,
                    defaults={'quantite': 0, 'valeur_totale': 0},
                )
                ligne.quantite = F('quantite') + mouvement.quantite
                ligne.valeur_totale = F('valeur_totale') + mouvement.valeur_totale
                ligne.save(update_fields=['quantite', 'valeur_totale'])

            elif mouvement.type_mouvement in ('sortie', 'perte'):
                try:
                    ligne = LigneStock.objects.get(
                        magasin=mouvement.magasin_source,
                        article=mouvement.article,
                    )
                    ligne.quantite = F('quantite') - mouvement.quantite
                    ligne.valeur_totale = F('valeur_totale') - mouvement.valeur_totale
                    ligne.save(update_fields=['quantite', 'valeur_totale'])
                except LigneStock.DoesNotExist:
                    pass

            elif mouvement.type_mouvement == 'transfert':
                # Sortie du magasin source
                try:
                    src = LigneStock.objects.get(
                        magasin=mouvement.magasin_source,
                        article=mouvement.article,
                    )
                    src.quantite = F('quantite') - mouvement.quantite
                    src.valeur_totale = F('valeur_totale') - mouvement.valeur_totale
                    src.save(update_fields=['quantite', 'valeur_totale'])
                except LigneStock.DoesNotExist:
                    pass
                # Entrée dans le magasin destination
                dest, _ = LigneStock.objects.get_or_create(
                    magasin=mouvement.magasin_destination,
                    article=mouvement.article,
                    defaults={'quantite': 0, 'valeur_totale': 0},
                )
                dest.quantite = F('quantite') + mouvement.quantite
                dest.valeur_totale = F('valeur_totale') + mouvement.valeur_totale
                dest.save(update_fields=['quantite', 'valeur_totale'])

            elif mouvement.type_mouvement == 'inventaire':
                # Ajustement direct: source = destination (même magasin)
                magasin = mouvement.magasin_destination or mouvement.magasin_source
                if magasin:
                    ligne, _ = LigneStock.objects.get_or_create(
                        magasin=magasin,
                        article=mouvement.article,
                        defaults={'quantite': 0, 'valeur_totale': 0},
                    )
                    ligne.quantite = mouvement.quantite
                    ligne.valeur_totale = mouvement.valeur_totale
                    ligne.save(update_fields=['quantite', 'valeur_totale'])

    @action(detail=False, methods=['post'])
    def batch(self, request):
        """Enregistre plusieurs mouvements de stock en une seule opération."""
        serializer = MouvementBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        type_mouvement = data['type_mouvement']
        magasin_source_id = data.get('magasin_source')
        magasin_destination_id = data.get('magasin_destination')
        reference_document = data.get('reference_document', '')
        projet_id = data.get('projet')
        date_mouvement = data.get('date_mouvement', timezone.now().date())
        lignes = data['lignes']

        mouvements_crees = []
        erreurs = []

        with transaction.atomic():
            for item in lignes:
                try:
                    article = ArticleStock.objects.get(id=item['article'])
                except ArticleStock.DoesNotExist:
                    erreurs.append({'article': item['article'], 'erreur': 'Article introuvable.'})
                    continue

                mouvement = MouvementStock(
                    article=article,
                    magasin_source_id=magasin_source_id,
                    magasin_destination_id=magasin_destination_id,
                    type_mouvement=type_mouvement,
                    quantite=item['quantite'],
                    prix_unitaire=item.get('prix_unitaire', 0),
                    reference_document=reference_document,
                    motif=item.get('motif', ''),
                    projet_id=projet_id,
                    effectue_par=request.user,
                    date_mouvement=date_mouvement,
                )
                mouvement.save()
                self._appliquer_mouvement(mouvement)
                mouvements_crees.append(mouvement.id)

        return Response({
            'crees': len(mouvements_crees),
            'mouvements_ids': mouvements_crees,
            'erreurs': erreurs,
        }, status=status.HTTP_201_CREATED)


# ─── Dashboard logistique ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadLog])
def dashboard_logistique(request):
    programme_id = request.query_params.get('programme')
    projet_id = request.query_params.get('projet')
    today = timezone.now().date()

    qs_vehicule = Vehicule.objects.all()
    qs_equipement = Equipement.objects.all()
    qs_mission = MissionVehicule.objects.all()
    qs_mouvement = MouvementStock.objects.all()

    if programme_id:
        qs_vehicule = qs_vehicule.filter(programme_id=programme_id)
        qs_equipement = qs_equipement.filter(programme_id=programme_id)
        qs_mission = qs_mission.filter(vehicule__programme_id=programme_id)
    if projet_id:
        qs_vehicule = qs_vehicule.filter(projet_id=projet_id)
        qs_equipement = qs_equipement.filter(projet_id=projet_id)
        qs_mission = qs_mission.filter(projet_id=projet_id)
        qs_mouvement = qs_mouvement.filter(projet_id=projet_id)

    # Véhicules par statut
    vehicules_par_statut = {}
    for statut, _ in Vehicule.STATUT_CHOICES:
        vehicules_par_statut[statut] = qs_vehicule.filter(statut=statut).count()

    # Équipements par statut
    equipements_par_statut = {}
    for statut, _ in Equipement.STATUT_CHOICES:
        equipements_par_statut[statut] = qs_equipement.filter(statut=statut).count()

    # Articles en alerte
    articles_en_alerte = LigneStock.objects.filter(
        quantite__lte=F('article__stock_alerte')
    ).count()

    # Alertes véhicules
    assurance_expiree = qs_vehicule.filter(
        date_expiration_assurance__lt=today
    ).exclude(statut='reforme').count()
    vignette_expiree = qs_vehicule.filter(
        date_expiration_vignette__lt=today
    ).exclude(statut='reforme').count()

    # Mouvements ce mois
    mouvements_mois = qs_mouvement.filter(
        date_mouvement__month=today.month,
        date_mouvement__year=today.year,
    ).count()

    # Valeur totale des stocks
    valeur_stock = LigneStock.objects.aggregate(total=Sum('valeur_totale'))['total'] or 0

    return Response({
        'vehicules': {
            'total': qs_vehicule.count(),
            'par_statut': vehicules_par_statut,
            'alertes': {
                'assurance_expiree': assurance_expiree,
                'vignette_expiree': vignette_expiree,
            },
            'missions_en_cours': qs_mission.filter(statut='en_cours').count(),
        },
        'equipements': {
            'total': qs_equipement.count(),
            'par_statut': equipements_par_statut,
        },
        'stocks': {
            'articles_en_alerte': articles_en_alerte,
            'valeur_totale_stock': float(valeur_stock),
            'mouvements_ce_mois': mouvements_mois,
        },
    })
