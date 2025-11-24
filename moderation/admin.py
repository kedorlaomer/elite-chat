from django.contrib import admin
from .models import UnapprovedMessage, AllMessage

class UnapprovedMessageAdmin(admin.ModelAdmin):
    list_display = ('room_info', 'author', 'content', 'created_at', 'approved')
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
