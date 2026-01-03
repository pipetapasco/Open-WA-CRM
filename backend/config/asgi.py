"""
ASGI config for WhatsApp CRM project.

Configura el servidor ASGI para manejar:
- HTTP requests (Django REST API)
- WebSocket connections (Django Channels)

Reference: https://channels.readthedocs.io/en/stable/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP requests -> Django REST API
    "http": django_asgi_app,
    
    # WebSocket connections -> Django Channels
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
