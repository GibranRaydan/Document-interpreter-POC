# api/serializers.py

from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__' 


class DocumentExtractionRequestSerializer(serializers.Serializer):
    MODEL_CHOICES = ["llama3.1", "mistral", "nuextract"]

    file = serializers.FileField()
    model = serializers.CharField(required=False, default="llama3")