from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/chat/inbox/', consumers.ChatConsumer.as_asgi()),
]
