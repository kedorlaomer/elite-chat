import re
from datetime import timedelta

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .models import Profile, Room, Message, Image, DeletedMessage
from .forms import MessageForm

# Rows committed just before a poll's cursor can become visible after it; re-read
# this window on every poll and let the client de-duplicate by id.
POLL_OVERLAP = timedelta(seconds=5)

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

def visible_messages(room, user):
    if user.is_staff:
        return room.message_set.all()
    return room.message_set.filter(Q(approved=True) | Q(author=user))


def create_message(room, user, content):
    profile = Profile.objects.get_or_create(user=user)[0]
    message = Message.objects.create(room=room, author=user, content=content, approved=profile.auto_approve)
    # Associate images
    for image_id in re.findall(r'/image/(\d+)/', content):
        try:
            image = Image.objects.get(id=image_id, message__isnull=True)
            image.message = message
            image.save()
        except Image.DoesNotExist:
            pass
    return message


def message_payload(message):
    return {
        'id': message.id,
        'content': message.content,
        'author': message.author.username,
        'author_id': message.author_id,
        'created_at': message.created_at.isoformat(),
        'approved': message.approved,
    }


def member_room_or_none(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if not room.members.filter(id=request.user.id).exists():
        return None
    return room


@login_required
def room(request, room_id):
    room = member_room_or_none(request, room_id)
    if room is None:
        return redirect('dashboard')  # or error message
    messages = visible_messages(room, request.user).order_by('created_at')
    form = MessageForm()
    if request.method == 'POST':
        # Fallback for browsers without JavaScript; the page normally posts to room_messages
        form = MessageForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            if content:
                create_message(room, request.user, content)
        return redirect('room', room_id=room.id)
    return render(request, 'room.html', {
        'room': room,
        'messages': messages,
        'form': form,
        'poll_cursor': timezone.now().isoformat(),
        'poll_interval_ms': settings.CHAT_POLL_INTERVAL_MS,
        'poll_hidden_interval_ms': settings.CHAT_POLL_HIDDEN_INTERVAL_MS,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def room_messages(request, room_id):
    """
    GET ?since=<cursor>: messages created or changed since the cursor, plus ids
    deleted since then (or no longer visible to this user), and the next cursor.
    POST content=<html>: create a message and return it.
    """
    room = member_room_or_none(request, room_id)
    if room is None:
        return HttpResponseForbidden()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)
        message = create_message(room, request.user, content)
        return JsonResponse({'message': message_payload(message)}, status=201)

    now = timezone.now()
    since = parse_datetime(request.GET.get('since', ''))
    if since is None or timezone.is_naive(since):
        return JsonResponse({'error': 'Invalid since parameter'}, status=400)
    window_start = since - POLL_OVERLAP

    changed = (room.message_set.filter(updated_at__gt=window_start)
               .select_related('author').order_by('created_at'))
    updated, hidden = [], []
    for message in changed:
        if message.is_visible_to(request.user):
            updated.append(message_payload(message))
        else:
            hidden.append(message.id)
    deleted = list(DeletedMessage.objects
                   .filter(room_id=room.id, deleted_at__gt=window_start)
                   .values_list('message_id', flat=True))
    return JsonResponse({
        'messages': updated,
        'deleted': deleted + hidden,
        'cursor': now.isoformat(),
    })

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
@require_POST
def upload_image(request):
    if request.FILES.get('upload'):
        file = request.FILES['upload']
        if file.size > settings.MAX_UPLOAD_BYTES:
            limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
            return JsonResponse({'error': {'message': f'Image is larger than {limit_mb} MB'}}, status=413)
        if not (file.content_type or '').startswith('image/'):
            return JsonResponse({'error': {'message': 'Only images can be uploaded'}}, status=400)
        data = b''
        for chunk in file.chunks():
            data += chunk
        image = Image.objects.create(
            data=data,
            filename=file.name,
            content_type=file.content_type
        )
        url = f'/image/{image.id}/'
        return JsonResponse({'url': url})
    return JsonResponse({'error': {'message': 'Invalid request'}}, status=400)

def serve_image(request, image_id):
    image = get_object_or_404(Image, id=image_id)
    response = HttpResponse(image.data, content_type=image.content_type)
    # Images never change once uploaded; let the CDN and browsers keep them
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response

@require_POST
@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    room_id = message.room_id
    if message.author == request.user or request.user.is_staff:
        message.delete()
    return redirect('room', room_id=room_id)

@require_POST
@login_required
def approve_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user.is_staff:
        message.approved = True
        message.save()
    return redirect('room', room_id=message.room.id)
