from django.urls import path

from .views import create_opportunity, opportunity_browser, opportunity_detail_page

urlpatterns = [
    path('', opportunity_browser, name='opportunity-list-page'),
    path('create/', create_opportunity, name='opportunity-create'),
    path('<int:pk>/', opportunity_detail_page, name='opportunity-page'),
]
