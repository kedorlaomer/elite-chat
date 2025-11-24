from django.contrib import admin
from chat.models import Message
from .models import UnapprovedMessage, AllMessage

class UnapprovedMessageAdmin(admin.ModelAdmin):
    list_display = ('room_info', 'author', 'content', 'created_at', 'approved', 'previous_messages')
    list_filter = ('room',)
    actions = ['approve_messages']
    search_fields = ('content', 'author__username')
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(approved=False)

    def approve_messages(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f'{updated} messages approved.')
    approve_messages.short_description = "Approve selected messages"

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

class AllMessageAdmin(admin.ModelAdmin):
    list_display = ('room_info', 'author', 'content', 'created_at', 'approved')
    list_filter = ('approved', 'room')
    actions = ['approve_messages']
    search_fields = ('content', 'author__username')
    ordering = ['-created_at']

    def approve_messages(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f'{updated} messages approved.')
    approve_messages.short_description = "Approve selected messages"

    def room_info(self, obj):
        return f"{obj.room.name}: {obj.room.description}"
    room_info.short_description = 'Room'

admin.site.register(UnapprovedMessage, UnapprovedMessageAdmin)
admin.site.register(AllMessage, AllMessageAdmin)
