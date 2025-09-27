# comparison_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # path('vegetable', views.price_comparison_view, name='vegetable_price_comparison'),
    # path('compare/oil/', views.oil_comparison_view, name='oil_comparison'),

    path('',views.price_comparison_view, name='price_comparison'),
    
    # When a user goes to your-site.com/compare/oil/, run the oil_comparison_view.
    # The template uses {% url 'oil_comparison' %} to find this path.
    path('compare/oil/', views.oil_comparison_view, name='oil_comparison'),
]