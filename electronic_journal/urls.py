from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import RedirectView

schema_view = get_schema_view(
    openapi.Info(
        title="Электронный журнал API",
        default_version='v1',
        description="API для электронного журнала вуза",
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="admin@iljicevs-edu.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Включаем allauth без namespace
    path('accounts/signup/', RedirectView.as_view(pattern_name='account_login'), name='account_signup'),
    path('accounts/', include('allauth.urls')),
    
    # Наше приложение accounts с namespace
    path('accounts/', include('accounts.urls', namespace='accounts')),
    
    # API эндпоинты
    path('api/v1/', include([
        path('accounts/', include('accounts.api.urls')),
        # Здесь будут другие API-эндпоинты
    ])),
    
    # Документация API
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Настройка для медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)