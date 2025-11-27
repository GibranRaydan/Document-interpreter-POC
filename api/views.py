# core_project/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import extract_deed_data

class DeedExtractionView(APIView):
    """
    Receives raw deed text and uses Ollama to return structured extracted data.
    """
    def post(self, request, *args, **kwargs):
        # 1. Get the text input from the request body
        deed_text = request.data.get('text')
        model = request.data.get('model', 'llama3.1') # Default model

        if not deed_text:
            return Response(
                {"error": "Missing 'text' field in the request body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Call the Ollama service
        result = extract_deed_data(deed_text, model_name=model)
        
        # 3. Return the result
        if "error" in result:
            # Handle server/Ollama errors
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Success: Return the structured data
        return Response(result, status=status.HTTP_200_OK)