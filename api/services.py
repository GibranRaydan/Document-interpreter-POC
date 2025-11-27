# core_project/api/services.py
import ollama
from .schemas import LandRecord
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

def extract_deed_data(deed_text: str, model_name: str = 'llama3.1') -> dict:
    """
    Calls the local Ollama service to extract structured data from the deed text.
    """
    if not deed_text.strip():
        return {"error": "Input text is empty."}
        
    try:
        # 1. Generate the JSON schema from the Pydantic model
        schema = LandRecord.model_json_schema()
        
        # 2. Call the Ollama client with the structured format
        response = ollama.chat(
            model=model_name,
            messages=[
                {'role': 'system', 'content': 'You are a real estate expert. Extract data precisely and return a JSON object strictly following the provided schema.'},
                {'role': 'user', 'content': deed_text},
            ],
            format=schema,
            options={'temperature': 0.1} # Factual output
        )
        
        # 3. Validate and parse the JSON string
        json_content = response['message']['content']
        record = LandRecord.model_validate_json(json_content)
        
        # 4. Return the structured data
        return record.model_dump()
        
    except ValidationError as e:
        logger.error(f"Pydantic Validation Error: {e.errors()}")
        return {"error": "Structured data validation failed", "details": e.errors()}
        
    except ollama.OllamaAPIError as e:
        logger.error(f"Ollama API Error: {e}")
        return {"error": "Ollama API error. Is Ollama running and model pulled?", "details": str(e)}
        
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        return {"error": "An unexpected server error occurred", "details": str(e)}