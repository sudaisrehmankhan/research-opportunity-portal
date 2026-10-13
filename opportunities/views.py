from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from rest_framework import filters, generics, permissions

from .forms import RegistrationForm
from .models import Department, Opportunity, UserProfile
from .serializers import (
    DepartmentSerializer,
    OpportunitySerializer,
    UserProfileSerializer,
)


def _profile_for(user):
    return UserProfile.objects.select_related('department').filter(user=user).first()


@ensure_csrf_cookie
def frontend_home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    profile = _profile_for(request.user) if request.user.is_authenticated else None
    return render(request, 'index.html', {
        'profile': profile,
        'departments': Department.objects.all(),
        'can_manage': bool(request.user.is_authenticated and (
            request.user.is_staff or (profile and profile.role == UserProfile.TEACHER)
        )),
    })


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
def dashboard(request):
    profile = _profile_for(request.user)
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin-dashboard')
    if profile is None:
        messages.error(request, 'Your account needs a profile. Please contact an administrator.')
        return redirect('frontend-home')
    return render(request, 'dashboard.html', {
        'profile': profile,
        'opportunities': Opportunity.objects.filter(owner=request.user).order_by('-id')
        if profile.role == UserProfile.TEACHER else Opportunity.objects.filter(status='Open'),
    })


@login_required
@never_cache
def profile(request):
    user_profile = _profile_for(request.user)
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


@login_required
@never_cache
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    return render(request, 'admin_dashboard.html', {
        'student_count': UserProfile.objects.filter(role=UserProfile.STUDENT).count(),
        'teacher_count': UserProfile.objects.filter(role=UserProfile.TEACHER).count(),
        'department_count': Department.objects.count(),
        'opportunity_count': Opportunity.objects.count(),
    })


def opportunity_detail_page(request, pk):
    opportunity = get_object_or_404(
        Opportunity.objects.select_related('department_record', 'owner'),
        pk=pk,
    )
    return render(request, 'opportunity_detail.html', {'opportunity': opportunity})


class IsOpportunityManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        profile = _profile_for(request.user)
        return bool(profile and profile.role == UserProfile.TEACHER)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.is_superuser or obj.owner_id == request.user.id


class OpportunityListCreateAPIView(generics.ListCreateAPIView):
    queryset = Opportunity.objects.select_related('department_record', 'owner').order_by(
        '-application_deadline', '-id',
    )
    serializer_class = OpportunitySerializer
    permission_classes = [IsOpportunityManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'research_area', 'faculty_name', 'department', 'required_skills']
    ordering_fields = ['title', 'application_deadline', 'available_positions', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('mine') == '1' and self.request.user.is_authenticated:
            if not self.request.user.is_staff:
                queryset = queryset.filter(owner=self.request.user)
        status = self.request.query_params.get('status')
        department = self.request.query_params.get('department')
        if status in {'Open', 'Closed'}:
            queryset = queryset.filter(status=status)
        if department:
            queryset = queryset.filter(department__icontains=department)
        return queryset


class OpportunityDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Opportunity.objects.select_related('department_record', 'owner')
    serializer_class = OpportunitySerializer
    permission_classes = [IsOpportunityManager]


class DepartmentListAPIView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)
