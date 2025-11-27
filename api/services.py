# core_project/api/services.py
import ollama
from ollama import ResponseError
from .schemas import LandRecord
from pydantic import ValidationError
import logging
import json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a real estate legal document analysis expert."
    "Your task is to extract structured information from U.S. real property documents (deeds, mortgages, releases, liens, assignments, etc.)."
    "Return ONLY a JSON object that strictly follows the provided schema. "
)


def extract_document_data(document_text: str, model_name: str) -> dict:

    if not document_text.strip():
        return {"error": "Input text cannot be only whitespace."}

    try:
        schema = LandRecord.model_json_schema()

        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": document_text},
            ],
            format=schema,
            options={"temperature": 0.0},
        )

        if "message" not in response or "content" not in response["message"]:
            logger.error(f"Ollama response missing required fields: {response}")
            return {
                "error": "Invalid response from model.",
                "details": "Missing 'message.content' field."
            }

        json_raw = response["message"]["content"]

        try:
            data_json = json.loads(json_raw) if isinstance(json_raw, str) else json_raw
        except json.JSONDecodeError:
            logger.error(f"Non-JSON output returned: {json_raw}")
            return {
                "error": "Invalid JSON returned by model.",
                "details": json_raw
            }

        record = LandRecord.model_validate(data_json)
        return record.model_dump()

    except ValidationError as e:
        logger.error(f"Pydantic Validation Error: {e.errors()}")
        return {
            "error": "Structured data validation failed.",
            "details": e.errors()
        }

    except ResponseError as e:
        logger.error(f"Ollama API Error: {str(e)}")
        return {
            "error": "Ollama API error. Ensure Ollama is running & model exists.",
            "details": str(e)
        }

    except Exception as e:
        logger.exception("Unexpected error in document extraction service.")
        return {
            "error": "Unexpected server error occurred.",
            "details": str(e)
        }
