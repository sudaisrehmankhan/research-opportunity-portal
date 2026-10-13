from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions

from .forms import RegistrationForm
from .models import UserProfile
from .serializers import UserProfileSerializer


@method_decorator(never_cache, name='dispatch')
class PortalLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    next_page = '/dashboard/'

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        if self.request.user.is_staff or self.request.user.is_superuser:
            return reverse('admin-dashboard')
        return reverse('dashboard')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created. Sign in to continue.')
        return redirect('login')
    return render(request, 'register.html', {'form': form})


@require_POST
@never_cache
def portal_logout(request):
    logout(request)
    return redirect('frontend-home')


@login_required
@never_cache
def profile(request):
    user_profile = UserProfile.objects.select_related('department').filter(user=request.user).first()
    if user_profile is None:
        messages.error(request, 'No profile is available for this account.')
        return redirect('dashboard')
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()
        user_profile.phone = request.POST.get('phone', '').strip()
        user_profile.program = request.POST.get('program', '').strip()
        user_profile.position_title = request.POST.get('position_title', '').strip()
        user_profile.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'profile.html', {'profile': user_profile})


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)
