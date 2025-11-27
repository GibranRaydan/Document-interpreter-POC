# core_project/api/urls.py
from django.urls import path
from .views import DocumentDataExtractionView

urlpatterns = [
    path('extract-deed/', DocumentDataExtractionView.as_view(), name='extract_ddocument_data'),
]