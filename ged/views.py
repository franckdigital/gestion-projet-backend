import hashlib
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    Categorie, Document, VersionDocument, DossierDocument,
    WorkflowValidation, SignatureElectronique, LienPartage, AccesDocument,
    AuditDocument, CommentaireDocument,
    PlanConservation, BoiteArchive, DocumentArchive, DemandeDestruction,
    ModeleDocument, EntreesBibliotheque,
)
from .serializers import (
    CategorieSerializer, DocumentListSerializer, DocumentDetailSerializer,
    DocumentCreateSerializer, VersionDocumentSerializer, DossierDocumentSerializer,
    WorkflowValidationSerializer, SignatureSerializer, LienPartageSerializer,
    AccesDocumentSerializer, AuditDocumentSerializer, CommentaireDocumentSerializer,
    PlanConservationSerializer, BoiteArchiveListSerializer, BoiteArchiveDetailSerializer,
    DocumentArchiveSerializer, DemandeDestructionSerializer,
    ModeleDocumentSerializer, EntreeBibliothequeSerializer,
)
from .filters import (
    DocumentFilter, BoiteArchiveFilter, AuditFilter,
    ModeleFilter, BibliothequeFilter,
)

CanReadGED = HasModulePermission.for_module('ged', 'peut_lire')
CanEditGED = HasModulePermission.for_module('ged', 'peut_modifier')
CanValidateGED = HasModulePermission.for_module('ged', 'peut_valider')


def _log_audit(document, action, user, request=None, details=None):
    AuditDocument.objects.create(
        document=document,
        action=action,
        utilisateur=user,
        details=details or {},
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
    )


# ─── Plan de classement ───────────────────────────────────────────────────────

class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.prefetch_related('sous_categories', 'documents').order_by('ordre', 'nom')
    serializer_class = CategorieSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nom', 'code', 'description']
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('racines_seulement'):
            qs = qs.filter(parent__isnull=True)
        domaine = self.request.query_params.get('domaine')
        if domaine:
            qs = qs.filter(domaine=domaine)
        return qs.filter(actif=True)

    @action(detail=False, methods=['get'])
    def arborescence(self, request):
        racines = Categorie.objects.filter(parent__isnull=True, actif=True).order_by('ordre')
        return Response(CategorieSerializer(racines, many=True).data)


# ─── M24 : Documents ─────────────────────────────────────────────────────────

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related(
        'categorie', 'auteur', 'projet', 'programme', 'valide_par'
    ).prefetch_related('historique_versions', 'workflow_validations', 'signatures').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DocumentFilter
    search_fields = ['reference', 'titre', 'description', 'mots_cles', 'texte_ocr',
                     'resume_auto', 'mots_cles_auto']
    ordering_fields = ['created_at', 'titre', 'statut', 'version']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'recherche_plein_texte']:
            return [CanReadGED()]
        if self.action in ['approuver', 'valider_etape', 'rejeter_etape']:
            return [CanValidateGED()]
        return [CanEditGED()]

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return DocumentCreateSerializer
        return DocumentDetailSerializer

    def perform_create(self, s):
        doc = s.save(auteur=self.request.user)
        _log_audit(doc, 'modification', self.request.user, self.request,
                   {'action': 'creation', 'titre': doc.titre})
        if doc.fichier:
            self._calculer_empreinte(doc)

    def _calculer_empreinte(self, doc):
        try:
            h = hashlib.sha256()
            for chunk in doc.fichier.chunks():
                h.update(chunk)
            doc.empreinte_sha256 = h.hexdigest()
            doc.taille_fichier = doc.fichier.size
            ext = doc.fichier.name.split('.')[-1].lower() if '.' in doc.fichier.name else ''
            doc.type_fichier = ext
            doc.save(update_fields=['empreinte_sha256', 'taille_fichier', 'type_fichier'])
        except Exception:
            pass

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        _log_audit(instance, 'consultation', request.user, request)
        return Response(DocumentDetailSerializer(instance).data)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        doc = self.get_object()
        if doc.statut != 'brouillon':
            return Response({'detail': 'Seul un brouillon peut être soumis.'}, status=400)
        doc.soumettre()
        _log_audit(doc, 'validation', request.user, request, {'statut': 'soumis'})
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        doc = self.get_object()
        if doc.statut not in ('soumis', 'en_revision'):
            return Response({'detail': 'Statut incompatible.'}, status=400)
        doc.approuver(request.user)
        _log_audit(doc, 'validation', request.user, request, {'statut': 'approuve'})
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        doc = self.get_object()
        try:
            doc.publier()
            _log_audit(doc, 'modification', request.user, request, {'statut': 'publie'})
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        doc = self.get_object()
        doc.archiver()
        _log_audit(doc, 'archivage', request.user, request)
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        doc = self.get_object()
        doc.statut = 'en_revision'
        doc.notes = request.data.get('motif', doc.notes)
        doc.save(update_fields=['statut', 'notes'])
        _log_audit(doc, 'validation', request.user, request, {'statut': 'rejete'})
        return Response(DocumentDetailSerializer(doc).data)

    @action(detail=True, methods=['post'])
    def nouvelle_version(self, request, pk=None):
        doc = self.get_object()
        fichier = request.FILES.get('fichier')
        commentaire = request.data.get('commentaire', '')
        VersionDocument.objects.create(
            document=doc, numero_version=doc.version,
            fichier=doc.fichier, commentaire=commentaire,
            modifie_par=request.user, taille_fichier=doc.taille_fichier,
            empreinte_sha256=doc.empreinte_sha256,
        )
        nouveau = doc.creer_nouvelle_version(request.user, fichier)
        _log_audit(nouveau, 'modification', request.user, request,
                   {'action': 'nouvelle_version', 'version': nouveau.version})
        return Response(DocumentDetailSerializer(nouveau).data, status=201)

    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        doc = self.get_object()
        _log_audit(doc, 'telechargement', request.user, request)
        if not doc.fichier:
            return Response({'detail': 'Aucun fichier associé.'}, status=404)
        return Response({
            'url': request.build_absolute_uri(doc.fichier.url),
            'nom': doc.titre,
            'type': doc.type_fichier,
            'taille': doc.taille_fichier,
        })

    @action(detail=True, methods=['post'])
    def ocr(self, request, pk=None):
        doc = self.get_object()
        if not doc.fichier:
            return Response({'detail': 'Aucun fichier pour OCR.'}, status=400)
        from ged.services.ocr import extraire_texte
        resultat = extraire_texte(doc.fichier)
        doc.texte_ocr = resultat['texte']
        doc.ocr_effectue = True
        doc.date_ocr = timezone.now()
        doc.save(update_fields=['texte_ocr', 'ocr_effectue', 'date_ocr'])
        return Response({
            'ocr_effectue': True,
            'nb_caracteres': len(resultat['texte']),
            'nb_pages': resultat['nb_pages'],
            'methode': resultat['methode'],
            'erreur': resultat['erreur'],
        })

    @action(detail=True, methods=['post'])
    def analyse_ia(self, request, pk=None):
        doc = self.get_object()
        mots = list(set((doc.mots_cles or '').replace(',', ' ').split()[:10]))
        doc.mots_cles_auto = ', '.join(mots) if mots else doc.titre.split()[0]
        doc.resume_auto = (
            f"[IA] Document '{doc.titre}' — "
            f"Type : {doc.get_type_document_display()}. "
            f"{doc.description[:200]}"
        )
        doc.categorie_suggeree = doc.categorie.nom if doc.categorie else "À classifier"
        doc.save(update_fields=['mots_cles_auto', 'resume_auto', 'categorie_suggeree'])
        return Response({
            'mots_cles_auto': doc.mots_cles_auto,
            'resume': doc.resume_auto,
            'categorie_suggeree': doc.categorie_suggeree,
        })

    @action(detail=False, methods=['get'])
    def recherche_plein_texte(self, request):
        q = request.query_params.get('q', '')
        if len(q) < 3:
            return Response({'detail': 'Requête trop courte (min. 3 caractères).'}, status=400)
        qs = Document.objects.filter(
            Q(titre__icontains=q) | Q(description__icontains=q) |
            Q(mots_cles__icontains=q) | Q(texte_ocr__icontains=q) |
            Q(resume_auto__icontains=q) | Q(mots_cles_auto__icontains=q)
        ).filter(statut__in=['approuve', 'publie'])[:50]
        return Response({
            'requete': q,
            'nb_resultats': qs.count(),
            'resultats': DocumentListSerializer(qs, many=True).data,
        })

    @action(detail=False, methods=['post'])
    def detecter_doublons(self, request):
        empreinte = request.data.get('empreinte_sha256', '')
        titre = request.data.get('titre', '')
        doublons = []
        if empreinte:
            docs = Document.objects.filter(empreinte_sha256=empreinte).exclude(statut='detruit')
            doublons.extend(DocumentListSerializer(docs, many=True).data)
        elif titre:
            docs = Document.objects.filter(titre__icontains=titre).exclude(statut='detruit')[:10]
            doublons.extend(DocumentListSerializer(docs, many=True).data)
        return Response({'nb_doublons': len(doublons), 'doublons': doublons})

    @action(detail=True, methods=['post'])
    def creer_lien_partage(self, request, pk=None):
        doc = self.get_object()
        lien = LienPartage.objects.create(
            document=doc,
            cree_par=request.user,
            email_destinataire=request.data.get('email', ''),
            date_expiration=request.data.get('date_expiration'),
            nb_telechargements_max=request.data.get('nb_max'),
        )
        _log_audit(doc, 'partage', request.user, request)
        return Response(LienPartageSerializer(lien).data, status=201)


class VersionDocumentViewSet(viewsets.ModelViewSet):
    queryset = VersionDocument.objects.order_by('-date_version')
    serializer_class = VersionDocumentSerializer
    permission_classes = [CanReadGED]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        d = self.request.query_params.get('document')
        return qs.filter(document_id=d) if d else qs

    def perform_create(self, s):
        s.save(modifie_par=self.request.user)


class DossierDocumentViewSet(viewsets.ModelViewSet):
    queryset = DossierDocument.objects.prefetch_related('documents', 'sous_dossiers').order_by('ordre', 'nom')
    serializer_class = DossierDocumentSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'description']
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        parent = self.request.query_params.get('parent')
        projet = self.request.query_params.get('projet')
        racines = self.request.query_params.get('racines')
        if parent:
            qs = qs.filter(parent_id=parent)
        if projet:
            qs = qs.filter(projet_id=projet)
        if racines:
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def ajouter_document(self, request, pk=None):
        dossier = self.get_object()
        doc_id = request.data.get('document_id')
        try:
            doc = Document.objects.get(id=doc_id)
            dossier.documents.add(doc)
            return Response({'detail': 'Document ajouté.'})
        except Document.DoesNotExist:
            return Response({'detail': 'Document introuvable.'}, status=404)

    @action(detail=True, methods=['post'])
    def retirer_document(self, request, pk=None):
        dossier = self.get_object()
        doc_id = request.data.get('document_id')
        try:
            doc = Document.objects.get(id=doc_id)
            dossier.documents.remove(doc)
            return Response({'detail': 'Document retiré.'})
        except Document.DoesNotExist:
            return Response({'detail': 'Document introuvable.'}, status=404)


class WorkflowValidationViewSet(viewsets.ModelViewSet):
    queryset = WorkflowValidation.objects.order_by('document', 'ordre')
    serializer_class = WorkflowValidationSerializer
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        d = self.request.query_params.get('document')
        return qs.filter(document_id=d) if d else qs

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        v = self.get_object()
        v.approuver(request.user, request.data.get('commentaire', ''))
        doc = v.document
        if not doc.workflow_validations.filter(statut='en_attente').exists():
            doc.statut = 'approuve'
            doc.valide_par = request.user
            doc.date_validation = timezone.now()
            doc.save(update_fields=['statut', 'valide_par', 'date_validation'])
        _log_audit(doc, 'validation', request.user, request, {'etape': v.id, 'statut': 'approuve'})
        return Response(WorkflowValidationSerializer(v).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        v = self.get_object()
        v.rejeter(request.user, request.data.get('commentaire', ''))
        _log_audit(v.document, 'validation', request.user, request, {'etape': v.id, 'statut': 'rejete'})
        return Response(WorkflowValidationSerializer(v).data)


class SignatureViewSet(viewsets.ModelViewSet):
    queryset = SignatureElectronique.objects.order_by('document', 'ordre')
    serializer_class = SignatureSerializer
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        d = self.request.query_params.get('document')
        return qs.filter(document_id=d) if d else qs

    @action(detail=True, methods=['post'])
    def signer(self, request, pk=None):
        sig = self.get_object()
        if sig.statut == 'signe':
            return Response({'detail': 'Déjà signé.'}, status=400)
        if sig.date_expiration and sig.date_expiration < timezone.now().date():
            sig.statut = 'expire'
            sig.save(update_fields=['statut'])
            return Response({'detail': 'Signature expirée.'}, status=400)
        sig.signer(request.user, request.META.get('REMOTE_ADDR'))
        _log_audit(sig.document, 'signature', request.user, request,
                   {'signature_id': sig.id, 'type': sig.type_signature})
        doc = sig.document
        if not doc.signatures.filter(statut='en_attente').exists() and doc.statut == 'approuve':
            doc.publier()
        return Response(SignatureSerializer(sig).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        sig = self.get_object()
        sig.statut = 'refuse'
        sig.commentaire = request.data.get('commentaire', '')
        sig.save(update_fields=['statut', 'commentaire'])
        return Response(SignatureSerializer(sig).data)


class LienPartageViewSet(viewsets.ModelViewSet):
    queryset = LienPartage.objects.order_by('-created_at')
    serializer_class = LienPartageSerializer
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        d = self.request.query_params.get('document')
        return qs.filter(document_id=d) if d else qs

    def perform_create(self, s):
        s.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        lien = self.get_object()
        lien.actif = False
        lien.save(update_fields=['actif'])
        return Response(LienPartageSerializer(lien).data)

    @action(detail=False, methods=['get'])
    def acceder(self, request):
        token = request.query_params.get('token')
        try:
            lien = LienPartage.objects.get(token=token)
        except LienPartage.DoesNotExist:
            return Response({'detail': 'Lien invalide.'}, status=404)
        if not lien.est_valide:
            return Response({'detail': 'Lien expiré ou désactivé.'}, status=403)
        lien.nb_telechargements += 1
        lien.save(update_fields=['nb_telechargements'])
        return Response(DocumentDetailSerializer(lien.document).data)


class AccesDocumentViewSet(viewsets.ModelViewSet):
    queryset = AccesDocument.objects.select_related('document', 'utilisateur')
    serializer_class = AccesDocumentSerializer
    permission_classes = [CanEditGED]

    def get_queryset(self):
        qs = super().get_queryset()
        d = self.request.query_params.get('document')
        u = self.request.query_params.get('utilisateur')
        if d:
            qs = qs.filter(document_id=d)
        if u:
            qs = qs.filter(utilisateur_id=u)
        return qs

    def perform_create(self, s):
        s.save(accorde_par=self.request.user)


class AuditDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditDocument.objects.select_related('document', 'utilisateur').order_by('-created_at')
    serializer_class = AuditDocumentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AuditFilter
    ordering_fields = ['created_at', 'action']
    permission_classes = [CanReadGED]


class CommentaireDocumentViewSet(viewsets.ModelViewSet):
    queryset = CommentaireDocument.objects.select_related('auteur').order_by('created_at')
    serializer_class = CommentaireDocumentSerializer
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        d = self.request.query_params.get('document')
        return qs.filter(document_id=d) if d else qs

    def perform_create(self, s):
        s.save(auteur=self.request.user)


# ─── M25 : Archivage ─────────────────────────────────────────────────────────

class PlanConservationViewSet(viewsets.ModelViewSet):
    queryset = PlanConservation.objects.select_related('categorie').all()
    serializer_class = PlanConservationSerializer
    permission_classes = [CanReadGED]


class BoiteArchiveViewSet(viewsets.ModelViewSet):
    queryset = BoiteArchive.objects.select_related(
        'categorie', 'programme', 'projet', 'created_by'
    ).prefetch_related('documents_archive').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BoiteArchiveFilter
    search_fields = ['reference', 'intitule', 'service_producteur']
    ordering_fields = ['created_at', 'annee_debut', 'statut']
    permission_classes = [CanReadGED]

    def get_serializer_class(self):
        return BoiteArchiveListSerializer if self.action == 'list' else BoiteArchiveDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def verser(self, request, pk=None):
        boite = self.get_object()
        boite.statut = 'versee'
        boite.date_versement = timezone.now().date()
        boite.save(update_fields=['statut', 'date_versement'])
        return Response(BoiteArchiveDetailSerializer(boite).data)

    @action(detail=True, methods=['post'])
    def ajouter_document(self, request, pk=None):
        boite = self.get_object()
        doc_id = request.data.get('document_id')
        try:
            doc = Document.objects.get(id=doc_id)
            empreinte = doc.empreinte_sha256 or hashlib.sha256(
                f"{doc.reference}-{doc.version}".encode()
            ).hexdigest()
            da, created = DocumentArchive.objects.get_or_create(
                boite=boite, document=doc,
                defaults={'archive_par': request.user, 'empreinte_integrite': empreinte}
            )
            if created:
                # Chiffrement AES-256-GCM si la boîte est un coffre-fort
                if boite.chiffree and boite.cle_chiffrement and doc.fichier:
                    self._chiffrer_document_archive(da, doc, boite)
                doc.archiver()
                _log_audit(doc, 'archivage', request.user, request, {'boite': boite.reference, 'chiffre': boite.chiffree})
            return Response(DocumentArchiveSerializer(da).data, status=201 if created else 200)
        except Document.DoesNotExist:
            return Response({'detail': 'Document introuvable.'}, status=404)

    def _chiffrer_document_archive(self, da, doc, boite):
        """Chiffre le fichier du document et stocke la copie dans da.fichier_chiffre."""
        from ged.services.chiffrement import chiffrer_fichier
        from django.core.files.base import ContentFile
        try:
            doc.fichier.seek(0)
            contenu_clair = doc.fichier.read()
            doc.fichier.seek(0)
            contenu_chiffre = chiffrer_fichier(boite.cle_chiffrement, contenu_clair)
            nom_fichier = f"coffre_{da.id or 'new'}_{doc.reference}.enc"
            da.fichier_chiffre.save(nom_fichier, ContentFile(contenu_chiffre), save=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Chiffrement document %s: %s', doc.reference, e)

    @action(detail=True, methods=['get'])
    def telecharger_dechiffre(self, request, pk=None):
        """Déchiffre et retourne le fichier d'un document dans une boîte chiffrée."""
        boite = self.get_object()
        doc_id = request.query_params.get('document_id')
        if not doc_id:
            return Response({'detail': 'Paramètre document_id requis.'}, status=400)
        try:
            da = DocumentArchive.objects.get(boite=boite, document_id=doc_id)
        except DocumentArchive.DoesNotExist:
            return Response({'detail': 'Document non trouvé dans cette boîte.'}, status=404)
        if not boite.chiffree or not boite.cle_chiffrement:
            return Response({'detail': 'Cette boîte n\'est pas chiffrée.'}, status=400)
        if not da.fichier_chiffre:
            return Response({'detail': 'Aucune copie chiffrée disponible pour ce document.'}, status=404)
        from ged.services.chiffrement import dechiffrer_fichier
        from django.http import HttpResponse
        import os
        try:
            da.fichier_chiffre.seek(0)
            payload = da.fichier_chiffre.read()
            contenu_clair = dechiffrer_fichier(boite.cle_chiffrement, payload)
        except ValueError as e:
            return Response({'detail': str(e)}, status=500)
        doc = da.document
        nom_fichier = f"{doc.reference}_v{doc.version}.{doc.type_fichier or 'bin'}"
        _log_audit(doc, 'telechargement', request.user, request, {'source': 'coffre_fort', 'boite': boite.reference})
        response = HttpResponse(contenu_clair, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
        response['Content-Length'] = len(contenu_clair)
        return response

    @action(detail=True, methods=['get'])
    def inventaire(self, request, pk=None):
        boite = self.get_object()
        docs = boite.documents_archive.select_related('document', 'archive_par')
        return Response({
            'boite': boite.intitule,
            'reference': boite.reference,
            'nb_documents': docs.count(),
            'statut': boite.statut,
            'documents': DocumentArchiveSerializer(docs, many=True).data,
        })


class DocumentArchiveViewSet(viewsets.ModelViewSet):
    queryset = DocumentArchive.objects.order_by('-date_archivage')
    serializer_class = DocumentArchiveSerializer
    permission_classes = [CanReadGED]

    def get_queryset(self):
        qs = super().get_queryset()
        b = self.request.query_params.get('boite')
        return qs.filter(boite_id=b) if b else qs

    def perform_create(self, s):
        s.save(archive_par=self.request.user)


class DemandeDestructionViewSet(viewsets.ModelViewSet):
    queryset = DemandeDestruction.objects.order_by('-date_proposition')
    serializer_class = DemandeDestructionSerializer
    permission_classes = [CanReadGED]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(propose_par=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        d = self.get_object()
        d.statut = 'valide'
        d.valide_par = request.user
        d.date_validation = timezone.now()
        d.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(DemandeDestructionSerializer(d).data)

    @action(detail=True, methods=['post'])
    def autoriser(self, request, pk=None):
        d = self.get_object()
        d.statut = 'autorise'
        d.autorise_par = request.user
        d.date_autorisation = timezone.now()
        d.save(update_fields=['statut', 'autorise_par', 'date_autorisation'])
        return Response(DemandeDestructionSerializer(d).data)

    @action(detail=True, methods=['post'])
    def executer(self, request, pk=None):
        d = self.get_object()
        if d.statut != 'autorise':
            return Response({'detail': 'La destruction doit être autorisée.'}, status=400)
        for doc in d.documents.all():
            doc.statut = 'detruit'
            doc.save(update_fields=['statut'])
            _log_audit(doc, 'destruction', request.user, request, {'demande_id': d.id})
        if d.boite:
            d.boite.statut = 'detruite'
            d.boite.save(update_fields=['statut'])
        d.statut = 'execute'
        d.date_execution = timezone.now()
        d.save(update_fields=['statut', 'date_execution'])
        return Response(DemandeDestructionSerializer(d).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        d = self.get_object()
        d.statut = 'rejete'
        d.save(update_fields=['statut'])
        return Response(DemandeDestructionSerializer(d).data)


# ─── Bibliothèque et modèles ──────────────────────────────────────────────────

class ModeleDocumentViewSet(viewsets.ModelViewSet):
    queryset = ModeleDocument.objects.order_by('type_modele', 'titre')
    serializer_class = ModeleDocumentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ModeleFilter
    search_fields = ['titre', 'description']
    permission_classes = [CanReadGED]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def utiliser(self, request, pk=None):
        modele = self.get_object()
        modele.nb_utilisations += 1
        modele.save(update_fields=['nb_utilisations'])
        return Response({'modele': modele.titre, 'nb_utilisations': modele.nb_utilisations})


class EntreeBibliothequeViewSet(viewsets.ModelViewSet):
    queryset = EntreesBibliotheque.objects.order_by('-created_at')
    serializer_class = EntreeBibliothequeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BibliothequeFilter
    search_fields = ['titre', 'description', 'mots_cles', 'auteur', 'organisation']
    ordering_fields = ['created_at', 'nb_telechargements']
    permission_classes = [CanReadGED]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(ajoute_par=self.request.user)

    @action(detail=True, methods=['post'])
    def telecharger(self, request, pk=None):
        entree = self.get_object()
        entree.nb_telechargements += 1
        entree.save(update_fields=['nb_telechargements'])
        if entree.fichier:
            return Response({'url': request.build_absolute_uri(entree.fichier.url)})
        return Response({'url': entree.url_externe})


# ─── Dashboard GED ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadGED])
def dashboard_ged(request):
    projet_id = request.query_params.get('projet')
    today = timezone.now().date()

    qs_docs = Document.objects.all()
    if projet_id:
        qs_docs = qs_docs.filter(projet_id=projet_id)

    taille_totale = qs_docs.aggregate(s=Sum('taille_fichier'))['s'] or 0

    return Response({
        'documents': {
            'total': qs_docs.count(),
            'par_statut': {s: qs_docs.filter(statut=s).count() for s, _ in Document.STATUT_CHOICES},
            'avec_ocr': qs_docs.filter(ocr_effectue=True).count(),
            'expires': qs_docs.filter(
                date_expiration__lt=today
            ).exclude(statut__in=['archive', 'detruit']).count(),
            'taille_totale_mo': round(taille_totale / (1024 * 1024), 2),
        },
        'archives': {
            'nb_boites': BoiteArchive.objects.count(),
            'boites_ouvertes': BoiteArchive.objects.filter(statut='ouverte').count(),
            'nb_documents_archives': DocumentArchive.objects.count(),
        },
        'activite_recente': {
            'ajouts_ce_mois': qs_docs.filter(
                created_at__month=today.month, created_at__year=today.year
            ).count(),
            'consultations': AuditDocument.objects.filter(
                action='consultation',
                created_at__month=today.month
            ).count(),
            'telechargements': AuditDocument.objects.filter(
                action='telechargement',
                created_at__month=today.month
            ).count(),
        },
        'par_type': [
            {'type': t, 'nb': qs_docs.filter(type_document=t).count()}
            for t, _ in Document.TYPE_DOC_CHOICES
            if qs_docs.filter(type_document=t).exists()
        ],
        'bibliotheque': {
            'nb_modeles': ModeleDocument.objects.filter(actif=True).count(),
            'nb_ressources': EntreesBibliotheque.objects.count(),
        },
    })


@api_view(['GET'])
@permission_classes([CanReadGED])
def rapport_conformite(request):
    qs = Document.objects.all()
    total = qs.count()
    sans_categorie = qs.filter(categorie__isnull=True).count()
    sans_mots_cles = qs.filter(mots_cles='').count()
    return Response({
        'conformite_globale': round((1 - sans_categorie / total) * 100, 1) if total else 100,
        'regles': {
            'RG_GED_001_sans_categorie': {'nb': sans_categorie, 'conforme': sans_categorie == 0},
            'RG_GED_002_sans_mots_cles': {'nb': sans_mots_cles},
            'avec_ocr': {
                'nb': qs.filter(ocr_effectue=True).count(),
                'taux': round(qs.filter(ocr_effectue=True).count() / total * 100, 1) if total else 0,
            },
            'avec_signature': {
                'nb': Document.objects.filter(signatures__statut='signe').distinct().count()
            },
        },
        'par_confidentialite': {
            c: qs.filter(confidentialite=c).count()
            for c, _ in Document.CONFIDENTIALITE_CHOICES
        },
    })
