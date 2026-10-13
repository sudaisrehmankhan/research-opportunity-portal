from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import filters, generics, permissions

from accounts.models import UserProfile

from .forms import OpportunityForm
from .models import Department, Opportunity
from .serializers import DepartmentSerializer, OpportunitySerializer


def visible_opportunities(user):
    opportunities = Opportunity.objects.select_related('department_record', 'owner')
    profile = (
        UserProfile.objects.select_related('department').filter(user=user).first()
        if user.is_authenticated else None
    )
    if user.is_staff or (profile and profile.role == UserProfile.TEACHER):
        return opportunities
    return opportunities.filter(
        status='Open',
        application_deadline__gte=timezone.localdate(),
    )


def _render_opportunity_browser(request, opportunity_form=None):
    profile = (
        UserProfile.objects.select_related('department').filter(user=request.user).first()
        if request.user.is_authenticated else None
    )
    can_manage = bool(
        request.user.is_authenticated
        and (request.user.is_staff or (profile and profile.role == UserProfile.TEACHER))
    )
    if opportunity_form is None and can_manage:
        opportunity_form = OpportunityForm(user=request.user)
    return render(request, 'opportunities.html', {
        'profile': profile,
        'departments': Department.objects.all(),
        'can_manage': can_manage,
        'opportunity_form': opportunity_form,
    })


@ensure_csrf_cookie
def opportunity_browser(request):
    return _render_opportunity_browser(request)


@login_required
@never_cache
def create_opportunity(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if not request.user.is_staff and (
        profile is None
        or profile.role != UserProfile.TEACHER
        or profile.department_id is None
    ):
        return HttpResponseForbidden(
            'Only teachers with a department or administrators can create opportunities.',
        )

    if request.method == 'POST':
        form = OpportunityForm(request.POST, user=request.user)
        if form.is_valid():
            opportunity = form.save()
            messages.success(request, f'"{opportunity.title}" was created successfully.')
            return redirect('dashboard')
        messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = OpportunityForm(user=request.user)
    return _render_opportunity_browser(request, form)


def opportunity_detail_page(request, pk):
    opportunity = get_object_or_404(visible_opportunities(request.user), pk=pk)
    return render(request, 'opportunity_detail.html', {'opportunity': opportunity})


class IsOpportunityManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        profile = UserProfile.objects.filter(user=request.user).first()
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
    search_fields = [
        'title', 'description', 'research_area', 'faculty_name', 'department', 'required_skills',
    ]
    ordering_fields = ['title', 'application_deadline', 'available_positions', 'status']

    def get_queryset(self):
        queryset = visible_opportunities(self.request.user)
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
    serializer_class = OpportunitySerializer
    permission_classes = [IsOpportunityManager]

    def get_queryset(self):
        return visible_opportunities(self.request.user)


class DepartmentListAPIView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return super().get_permissions()
