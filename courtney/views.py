from http import HTTPMethod

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Record
from .serializers import RecordSerializer
from .temporal_dispatch import start_landrecord_workflow


@api_view([HTTPMethod.POST])
def landrecords(request):
    serializer = RecordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    record: Record = serializer.save()

    start_landrecord_workflow(record.pk, str(record.uuid))

    return Response(serializer.data, status=status.HTTP_201_CREATED)
