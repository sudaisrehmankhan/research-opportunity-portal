from django.urls import path

from .views import (
    DepartmentListAPIView,
    OpportunityDetailAPIView,
    OpportunityListCreateAPIView,
    PortalLoginView,
    UserProfileAPIView,
    admin_dashboard,
    dashboard,
    frontend_home,
    opportunity_detail_page,
    portal_logout,
    profile,
    register,
)

urlpatterns = [
    path('', PortalLoginView.as_view(), name='frontend-home'),
    path('login/', PortalLoginView.as_view(), name='login'),
    path('opportunities/', frontend_home, name='opportunity-list-page'),
    path('register/', register, name='register'),
    path('logout/', portal_logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('profile/', profile, name='profile'),
    path('opportunities/<int:pk>/', opportunity_detail_page, name='opportunity-page'),
    path('api/opportunities', OpportunityListCreateAPIView.as_view(), name='opportunity-list-create'),
    path('api/opportunities/', OpportunityListCreateAPIView.as_view(), name='opportunity-list-create-slash'),
    path('api/opportunities/<int:pk>', OpportunityDetailAPIView.as_view(), name='opportunity-detail'),
    path('api/opportunities/<int:pk>/', OpportunityDetailAPIView.as_view(), name='opportunity-detail-slash'),
    path('api/departments/', DepartmentListAPIView.as_view(), name='department-list'),
    path('api/profile/', UserProfileAPIView.as_view(), name='profile-api'),
]
