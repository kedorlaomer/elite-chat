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
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'
