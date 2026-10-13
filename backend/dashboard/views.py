from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from accounts.models import UserProfile
from opportunities.models import Department, Opportunity
from opportunities.views import visible_opportunities


@login_required
@never_cache
def dashboard(request):
    profile = UserProfile.objects.select_related('department').filter(user=request.user).first()
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin-dashboard')
    if profile is None or profile.role not in {UserProfile.TEACHER, UserProfile.STUDENT}:
        return HttpResponseForbidden(
            'Your account has no valid student or teacher profile. Please contact an administrator.',
        )
    if profile.role == UserProfile.TEACHER and profile.department_id is None:
        return HttpResponseForbidden(
            'Your teacher profile has no department. Please contact an administrator.',
        )
    if profile.role == UserProfile.TEACHER:
        template_name = 'teacher_dashboard.html'
        opportunities = Opportunity.objects.filter(owner=request.user).order_by('-id')
    else:
        template_name = 'student_dashboard.html'
        opportunities = visible_opportunities(request.user)
    return render(request, template_name, {
        'profile': profile,
        'opportunities': opportunities,
    })


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
