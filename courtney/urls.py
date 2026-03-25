from django.urls import path

from .views import (
    DocumentUploadView,
    DocumentListView,
    DocumentDetailView,
    DocumentSelectProcessView,
    DocumentProcessDeleteView,
    DocumentProcessStreamView,
)

urlpatterns = [
    path("documents/", DocumentListView.as_view()),
    path("documents/upload/", DocumentUploadView.as_view()),
    path("documents/<slug:slug>/", DocumentDetailView.as_view()),
    path("documents/<slug:slug>/select/<slug:process_slug>/", DocumentSelectProcessView.as_view()),
    path("documents/<slug:slug>/process/", DocumentProcessStreamView.as_view()),
    path("documents/<slug:slug>/process/<slug:process_slug>/", DocumentProcessStreamView.as_view()),
    path("documents/<slug:slug>/process/<slug:process_slug>/delete/", DocumentProcessDeleteView.as_view()),
]
