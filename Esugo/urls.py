"""
URL configuration for Esugo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth import logout
from myapp import views as myapp_views

def custom_logout(request):
    """Custom logout view that handles GET requests"""
    logout(request)
    return redirect('home')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),
    # Custom login view with role-based redirect
    path('accounts/login/', myapp_views.login_view, name='login'),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(template_name='myapp/password_change.html'), name='password_change'),
    path('accounts/password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='myapp/password_change_done.html'), name='password_change_done'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])