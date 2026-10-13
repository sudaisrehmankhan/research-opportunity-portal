from django.urls import path

from .views import DepartmentListAPIView, OpportunityDetailAPIView, OpportunityListCreateAPIView

urlpatterns = [
    path('api/opportunities', OpportunityListCreateAPIView.as_view(), name='opportunity-list-create'),
    path('api/opportunities/', OpportunityListCreateAPIView.as_view(), name='opportunity-list-create-slash'),
    path('api/opportunities/<int:pk>', OpportunityDetailAPIView.as_view(), name='opportunity-detail'),
    path('api/opportunities/<int:pk>/', OpportunityDetailAPIView.as_view(), name='opportunity-detail-slash'),
    path('api/departments/', DepartmentListAPIView.as_view(), name='department-list'),
]
