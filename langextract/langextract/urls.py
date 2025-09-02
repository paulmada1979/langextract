"""
URL configuration for langextract project.
"""
from django.urls import path, include

urlpatterns = [
    # Admin disabled for stateless API service
    # path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/document/', include('document_api.urls')),
    path('health/', include('core.urls')),
]
