import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from chat.models import Room, Message, Profile, Image


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        
        # Check if user is member of the room
        if not await self.is_room_member():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        text_data_json = json.loads(text_data)
        message_text = text_data_json['message']
        
        # Save message to database
        message = await self.save_message(message_text)
        
        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'author': message.author.username,
                        'author_id': message.author.id,
                        'created_at': message.created_at.isoformat(),
                        'approved': message.approved
                    }
                }
            )
    
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))
    
    @database_sync_to_async
    def is_room_member(self):
        user = self.scope['user']
        if isinstance(user, AnonymousUser):
            return False
        try:
            room = Room.objects.get(id=self.room_id)
            return room.members.filter(id=user.id).exists()
        except Room.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, message_text):
        user = self.scope['user']
        if isinstance(user, AnonymousUser):
            return None
            
        try:
            room = Room.objects.get(id=self.room_id)
            profile, created = Profile.objects.get_or_create(user=user)
            approved = profile.auto_approve
            
            message = Message.objects.create(
                room=room,
                author=user,
                content=message_text,
                approved=approved
            )
            
            # Associate images
            image_ids = re.findall(r'/image/(\d+)/', message_text)
            for image_id in image_ids:
                try:
                    image = Image.objects.get(id=image_id, message__isnull=True)
                    image.message = message
                    image.save()
                except Image.DoesNotExist:
                    pass
            
            return message
        except Room.DoesNotExist:
            return None