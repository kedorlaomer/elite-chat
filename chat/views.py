import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Profile, Room, Message, Image
from .forms import MessageForm

logger = logging.getLogger(__name__)

# Create your views here.

class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        if not profile.password_set:
            return redirect('set_password')
        return redirect('dashboard')

@login_required
def set_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            profile = Profile.objects.get(user=request.user)
            profile.password_set = True
            profile.save()
            messages.success(request, 'Password set successfully.')
            return redirect('dashboard')  # Redirect to dashboard
    else:
        form = SetPasswordForm(request.user)
    return render(request, 'set_password.html', {'form': form})

@login_required
def dashboard(request):
    rooms = request.user.chat_rooms.all()
    return render(request, 'dashboard.html', {'user': request.user, 'rooms': rooms})

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'user': request.user, 'profile': profile})

@login_required
def room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if not room.members.filter(id=request.user.id).exists():
        return redirect('dashboard')  # or error message
    messages = room.message_set.filter(
        models.Q(approved=True) | models.Q(author=request.user)
    ).order_by('created_at')
    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            if content:
                profile = Profile.objects.get_or_create(user=request.user)[0]
                approved = profile.auto_approve
                message = Message.objects.create(room=room, author=request.user, content=content, approved=approved)
                logger.info("Message created with id: %s", message.id)
                # Associate images
                import re
                image_ids = re.findall(r'/image/(\d+)/', content)
                logger.info("Found image IDs in content: %s", image_ids)
                for image_id in image_ids:
                    try:
                        image = Image.objects.get(id=image_id, message__isnull=True)
                        image.message = message
                        image.save()
                        logger.info("Associated image %s with message %s", image_id, message.id)
                    except Image.DoesNotExist:
                        logger.warning("Image %s not found or already associated", image_id)
        return redirect('room', room_id=room.id)
    return render(request, 'room.html', {'room': room, 'messages': messages, 'form': form})

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@csrf_exempt
def upload_image(request):
    print("upload_image called with method:", request.method)
    if request.method == 'POST' and request.FILES.get('upload'):
        file = request.FILES['upload']
        print("Uploading file:", file.name, "size:", file.size)
        data = b''
        for chunk in file.chunks():
            data += chunk
        image = Image.objects.create(
            data=data,
            filename=file.name,
            content_type=file.content_type
        )
        print("Image created with id:", image.id)
        url = request.build_absolute_uri(f'/image/{image.id}/')
        print("Returning URL:", url)
        return JsonResponse({'url': url})
    print("Invalid request to upload_image")
    return JsonResponse({'error': 'Invalid request'}, status=400)

def serve_image(request, image_id):
    logger.info("serve_image called for id: %s", image_id)
    image = get_object_or_404(Image, id=image_id)
    logger.info("Serving image: %s, size: %s", image.filename, len(image.data))
    return HttpResponse(image.data, content_type=image.content_type)

@require_POST
@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.author == request.user or request.user.is_staff:
        message.delete()
    return redirect('room', room_id=message.room.id)
