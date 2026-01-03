import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para el chat en tiempo real.
    
    Conexión: ws://host/ws/chat/inbox/
    
    Este consumer maneja:
    - Conexiones/desconexiones de clientes
    - Broadcasting de nuevos mensajes a todos los clientes conectados
    """
    
    INBOX_GROUP = 'inbox_updates'
    
    async def connect(self):
        """
        Llamado cuando un cliente se conecta al WebSocket.
        """
        # Unirse al grupo de actualizaciones del inbox
        await self.channel_layer.group_add(
            self.INBOX_GROUP,
            self.channel_name
        )
        
        # Aceptar la conexión
        await self.accept()
        
        logger.info(f"WebSocket connected: {self.channel_name}")
        
        # Enviar mensaje de bienvenida
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to inbox updates'
        }))
    
    async def disconnect(self, close_code):
        """
        Llamado cuando un cliente se desconecta.
        """
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.INBOX_GROUP,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected: {self.channel_name} (code={close_code})")
    
    async def receive(self, text_data):
        """
        Llamado cuando el cliente envía un mensaje.
        Por ahora solo logueamos, el envío real se hace via REST API.
        """
        try:
            data = json.loads(text_data)
            logger.debug(f"WebSocket received: {data}")
            
            # Podemos manejar comandos del cliente aquí si es necesario
            # Por ejemplo: marcar mensajes como leídos, typing indicators, etc.
            
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received on WebSocket")
    
    async def send_new_message(self, event):
        """
        Handler para mensajes nuevos enviados desde signals.
        Este método es llamado cuando se hace group_send con type='send_new_message'.
        """
        message_data = event.get('message', {})
        
        # Enviar al cliente WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': message_data
        }))
    
    async def send_conversation_update(self, event):
        """
        Handler para actualizaciones de conversación (ej: nuevo chat, cambio de estado).
        """
        conversation_data = event.get('conversation', {})
        
        await self.send(text_data=json.dumps({
            'type': 'conversation_update',
            'conversation': conversation_data
        }))

    async def send_status_update(self, event):
        """
        Handler para actualizaciones de estado de mensajes (sent, delivered, read).
        Este método es llamado cuando Meta notifica un cambio de estado.
        """
        status_update = event.get('status_update', {})
        
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status_update': status_update
        }))
