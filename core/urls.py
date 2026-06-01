from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication
    path('api/auth/', include('accounts.urls')),

    # Lot 1 - Gouvernance et administration
    path('api/gouvernance/', include('gouvernance.urls')),

    # Lot 2 - Gestion multi-programmes et multi-projets
    path('api/programmes-projets/', include('programmes_projets.urls')),

    # Lot 3 - Planification stratégique
    path('api/planification/', include('planification.urls')),

    # Lot 4 - Exécution opérationnelle
    path('api/execution/', include('execution.urls')),

    # Lot 5 - Suivi-évaluation et RBM
    path('api/suivi-evaluation/', include('suivi_evaluation.urls')),

    # Lot 6 - Gestion financière
    path('api/finances/', include('gestion_financiere.urls')),

    # Lot 7 - GED et archivage électronique
    path('api/ged/', include('ged.urls')),

    # Courrier électronique intelligent
    path('api/courrier-intelligent/', include('courrier_intelligent.urls')),

    # Courrier administratif et parapheur
    path('api/courrier-administratif/', include('courrier_administratif.urls')),

    # Collaboration
    path('api/collaboration/', include('collaboration.urls')),

    # Mobile terrain
    path('api/mobile/', include('mobile_terrain.urls')),

    # Intelligence artificielle
    path('api/ia/', include('intelligence_artificielle.urls')),

    # Business Intelligence
    path('api/bi/', include('business_intelligence.urls')),

    # Marchés publics
    path('api/marches-publics/', include('marches_publics.urls')),

    # RH Projet
    path('api/rh/', include('rh_projet.urls')),

    # Logistique
    path('api/logistique/', include('logistique.urls')),

    # Partenaires et bailleurs
    path('api/partenaires/', include('partenaires_bailleurs.urls')),

    # SIG
    path('api/sig/', include('sig.urls')),

    # Capitalisation des connaissances
    path('api/capitalisation/', include('capitalisation.urls')),

    # Lot 9 — Modules avancés
    path('api/diligences/', include('diligences.urls')),
    path('api/evenements/', include('evenements.urls')),
    path('api/qualite/', include('gestion_qualite.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
