import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    INBOX_GROUP = 'inbox_updates'

    async def connect(self):
        await self.channel_layer.group_add(self.INBOX_GROUP, self.channel_name)

        await self.accept()

        await self.send(
            text_data=json.dumps({'type': 'connection_established', 'message': 'Connected to inbox updates'})
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.INBOX_GROUP, self.channel_name)

    async def receive(self, text_data):
        pass

    async def send_new_message(self, event):
        message_data = event.get('message', {})

        await self.send(text_data=json.dumps({'type': 'new_message', 'message': message_data}))

    async def send_conversation_update(self, event):
        conversation_data = event.get('conversation', {})

        await self.send(text_data=json.dumps({'type': 'conversation_update', 'conversation': conversation_data}))

    async def send_status_update(self, event):
        status_update = event.get('status_update', {})

        await self.send(text_data=json.dumps({'type': 'status_update', 'status_update': status_update}))
