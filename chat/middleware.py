from django.urls import resolve, Resolver404
from django.utils import timezone
from .models import Profile

# Background requests the page makes on its own; they say nothing about user activity
PASSIVE_URL_NAMES = {'room_messages'}

class LastInteractionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not self.is_passive(request):
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.last_interaction = timezone.now()
            profile.save(update_fields=['last_interaction'])
        response = self.get_response(request)
        return response

    @staticmethod
    def is_passive(request):
        if request.method != 'GET':
            return False
        try:
            return resolve(request.path_info).url_name in PASSIVE_URL_NAMES
        except Resolver404:
            return False
