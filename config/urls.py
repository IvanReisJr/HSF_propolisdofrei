from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from .views import dashboard, htmx_load_movements

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('htmx/load-movements/', htmx_load_movements, name='htmx_load_movements'),
    
    # Auth URLs - Simplified
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view()), # Compatibility
    
    # path('accounts/', include('django.contrib.auth.urls')), # Disabled to prevent password reset access
    path('products/', include('apps.products.urls')),
    path('stock/', include('apps.stock.urls')),
    path('orders/', include('apps.orders.urls')),
    path('audit/', include('apps.audit.urls')),
    path('distributors/', include('apps.distributors.urls')),
    path('reports/', include('apps.reports.urls')),
    
    # Cadastros
    path('categories/', include('apps.categories.urls')),
    path('packagings/', include('apps.products.urls_packagings')),
    path('core/', include('apps.core.urls')),
    
    # API (mantendo por compatibilidade se necessário futuramente)
    path('api/', include('config.api_urls')),
    
    # Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
