# api/serializers.py

from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__' 


class DocumentExtractionRequestSerializer(serializers.Serializer):
    MODEL_CHOICES = ["llama3.1", "mistral", "nuextract"]

    text = serializers.CharField(required=True)
    model = serializers.ChoiceField(choices=MODEL_CHOICES, required=False, default="llama3.1")