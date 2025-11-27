# core_project/api/urls.py
from django.urls import path
from .views import DeedExtractionView

urlpatterns = [
    # Map POST requests to the DeedExtractionView
    path('extract-deed/', DeedExtractionView.as_view(), name='extract_deed'),
]