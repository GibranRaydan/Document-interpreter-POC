from django.urls import path

from .views import DocumentUploadAndProcessView

urlpatterns = [
    path("documents/upload_and_process/", DocumentUploadAndProcessView.as_view()),
]
