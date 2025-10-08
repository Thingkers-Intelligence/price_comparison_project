# comparison_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.price_comparison_view, name='price_comparison'),
    path('oil/', views.oil_comparison_view, name='oil_comparison'),
    path('fish-meat/', views.fish_meat_comparison_view, name='fish_meat_comparison'),
    path('snacks/', views.snacks_comparison_view, name='snacks_comparison'),
]
