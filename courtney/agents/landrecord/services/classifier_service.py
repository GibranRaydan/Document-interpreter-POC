from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from courtney.agents.abstract.base_llm import call_llm, LLMResponse
from courtney.models import Agent

logger = logging.getLogger(__name__)

VALID_DOC_TYPES = frozenset({"deeds", "mortgages", "releases", "liens", "assignments", "other"})


@dataclass
class ClassifierResult:
    document_type: str
    tokens_input: int
    tokens_output: int


async def classify_document(raw_text: str, client: httpx.AsyncClient, agent: Agent) -> ClassifierResult:
    """
    Classifies the document text into one of the supported document types.
    Defaults to 'other' if the model returns an unexpected value.
    """
    messages = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": raw_text},
    ]

    response: LLMResponse = await call_llm(client, agent.model, messages)

    label = response.content.strip().lower()
    if label not in VALID_DOC_TYPES:
        logger.warning("Classifier returned unexpected label %r, defaulting to 'other'", label)
        label = "other"

    return ClassifierResult(
        document_type=label,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
    )
