from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Room, Message, Membership, Profile

def approve_messages(modeladmin, request, queryset):
    updated = queryset.update(approved=True)
    modeladmin.message_user(request, f'{updated} messages approved.')

approve_messages.short_description = "Approve selected messages"

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0

class MembershipInlineForUser(admin.TabularInline):
    model = Membership
    extra = 0

class RoomAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]

class CustomUserAdmin(UserAdmin):
    inlines = [MembershipInlineForUser]

admin.site.register(Room, RoomAdmin)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room_info', 'author', 'content', 'created_at', 'approved', 'previous_messages')
    list_filter = ('approved', 'room')
    actions = [approve_messages]
    search_fields = ('content', 'author__username')
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(approved=False)

    def room_info(self, obj):
        return f"{obj.room.name}: {obj.room.description}"
    room_info.short_description = 'Room'

    def previous_messages(self, obj):
        prev = Message.objects.filter(
            room=obj.room, 
            created_at__lt=obj.created_at
        ).order_by('-created_at')[:5]
        if not prev:
            return "No previous messages"
        return '\n'.join([
            f"{m.author.username} ({m.created_at.strftime('%Y-%m-%d %H:%M')}): {m.content} [{'approved' if m.approved else 'unapproved'}]"
            for m in reversed(prev)
        ])
    previous_messages.short_description = 'Previous Messages (last 5)'

admin.site.register(Message, MessageAdmin)
admin.site.register(Membership)
admin.site.register(Profile)

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
