from django.urls import path

from .views import landrecords

urlpatterns = [
    path("land-records/", landrecords, name="landrecords"),
]
