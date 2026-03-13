from django.urls import path
from .views import DocumentUploadView, DocumentProcessView, DocumentDetailView

app_name = "agents"

urlpatterns = [
    path("documents/", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/<int:pk>/process/", DocumentProcessView.as_view(), name="document-process"),
    path("documents/<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
]
