from django.utils import timezone
from .models import Profile

class LastInteractionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.last_interaction = timezone.now()
            profile.save(update_fields=['last_interaction'])
        response = self.get_response(request)
        return response