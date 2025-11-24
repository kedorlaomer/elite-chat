"""
URL configuration for elite_chat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from chat.views import set_password, CustomLoginView, dashboard, home, profile, room, upload_image, serve_image, delete_message

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', profile, name='profile'),
    path('set_password/', set_password, name='set_password'),
    path('dashboard/', dashboard, name='dashboard'),
    path('room/<int:room_id>/', room, name='room'),
    path('message/<int:message_id>/delete/', delete_message, name='delete_message'),
    path('upload_image/', upload_image, name='upload_image'),
    path('image/<int:image_id>/', serve_image, name='serve_image'),
    path('ckeditor5/image_upload/', upload_image, name='ckeditor_upload'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
