"""
URL configuration for config project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = (
    [
        path('admin/', admin.site.urls),
        path('api/auth/', include('apps.accounts.urls')),
        path('api/config/', include('apps.config_api.urls')),
        path('api/contacts/', include('apps.contacts.urls')),
        path('api/chat/', include('apps.chat.urls')),
        path('api/ai-bot/', include('apps.ai_bot.urls')),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
