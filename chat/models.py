from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    password_set = models.BooleanField(default=False)
    last_interaction = models.DateTimeField(null=True, blank=True)
    auto_approve = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} Profile'

class Room(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField('auth.User', through='Membership', related_name='chat_rooms')

    def __str__(self):
        return self.name

class Membership(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f'{self.user.username} in {self.room.name}'

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Bumped on every change so polling clients pick up edits and approvals.
    # Bulk updates bypass auto_now and must set it explicitly.
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'

    def is_visible_to(self, user):
        return self.approved or user.is_staff or self.author_id == user.id


class DeletedMessage(models.Model):
    """Tombstone so polling clients can remove messages deleted elsewhere."""
    message_id = models.BigIntegerField()
    room_id = models.BigIntegerField()
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['room_id', 'deleted_at'], name='chat_deleted_room_time_idx')]

class Image(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    data = models.BinaryField()
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
