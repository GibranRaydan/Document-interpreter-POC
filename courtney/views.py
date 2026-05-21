from http import HTTPMethod
from pathlib import Path

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.generics import get_object_or_404

from .models import Book, Record
from .serializers import (
    BookCreateSerializer,
    BookStatusSerializer,
    RecordSerializer,
)
from .temporal_dispatch import start_book_workflow, start_landrecord_workflow


@api_view([HTTPMethod.POST])
def landrecords(request):
    serializer = RecordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    record: Record = serializer.save()

    start_landrecord_workflow(record.pk, str(record.uuid))

    return Response(serializer.data, status=http_status.HTTP_201_CREATED)


@api_view([HTTPMethod.POST])
def books_create(request):
    serializer = BookCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    folder_path = serializer.validated_data["folder_path"]

    book, _ = Book.objects.get_or_create(
        folder_path=folder_path,
        defaults={"name": Path(folder_path).name},
    )
    start_book_workflow(book.pk, str(book.uuid), folder_path)

    return Response(BookStatusSerializer(book).data, status=http_status.HTTP_202_ACCEPTED)


@api_view([HTTPMethod.GET])
def book_status(request, uuid):
    book = get_object_or_404(Book, uuid=uuid)
    return Response(BookStatusSerializer(book).data)
