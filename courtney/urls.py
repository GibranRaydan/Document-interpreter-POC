from django.urls import path

from .views import (
    DocumentUploadView,
    DocumentListView,
    DocumentDetailView,
    DocumentSelectProcessView,
    DocumentProcessStreamView,
)

urlpatterns = [
    path("documents/", DocumentListView.as_view()),
    path("documents/upload/", DocumentUploadView.as_view()),
    path("documents/<slug:slug>/", DocumentDetailView.as_view()),
    path("documents/<slug:slug>/select/<slug:process_slug>/", DocumentSelectProcessView.as_view()),
    path("documents/<slug:slug>/process/", DocumentProcessStreamView.as_view()),
]
