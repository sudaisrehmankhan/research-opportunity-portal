from django.urls import path

from .views import PortalLoginView, UserProfileAPIView, portal_logout, profile, register

urlpatterns = [
    path('', PortalLoginView.as_view(), name='frontend-home'),
    path('login/', PortalLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('logout/', portal_logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('api/profile/', UserProfileAPIView.as_view(), name='profile-api'),
]
