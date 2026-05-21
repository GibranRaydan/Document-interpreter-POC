from django.urls import path

from .views import book_status, books_create, landrecords

urlpatterns = [
    path("land-records/", landrecords, name="landrecords"),
    path("books/", books_create, name="books_create"),
    path("books/<uuid:uuid>/", book_status, name="book_status"),
]
