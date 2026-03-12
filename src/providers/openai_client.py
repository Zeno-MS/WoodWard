"""
src/providers/openai_client.py
Thin OpenAI async client wrapper for structured LLM calls.

Accepts a Pydantic response model, calls OpenAI with json_object mode,
and parses the result into the model. Raises on parse failure.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Thin wrapper around the OpenAI async client.
    Accepts a Pydantic response_model and returns a validated instance.

    Does NOT implement multi-provider routing — that is Phase 5+ work.
    Does NOT retry on validation failures — hard-stop and report.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.model = model
        self._api_key = api_key
        # Defer import so that missing openai package only fails at call time
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "openai package is required for OpenAIClient. "
                    "Install with: pip install openai"
                ) from exc
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def complete_structured(
        self,
        prompt: str,
        system_prompt: str,
        response_model: type[BaseModel],
        temperature: float = 0.3,
    ) -> BaseModel:
        """
        Call OpenAI with json_object response_format.
        Parse response as response_model.
        Raises ValueError on parse failure.
        Raises on API errors.
        """
        client = self._get_client()

        logger.debug(
            f"OpenAIClient.complete_structured: model={self.model} "
            f"response_model={response_model.__name__} temperature={temperature}"
        )

        response = await client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ValueError(
                f"OpenAI returned empty content for model={self.model}, "
                f"response_model={response_model.__name__}"
            )

        try:
            parsed = response_model.model_validate_json(raw_content)
        except Exception as exc:
            logger.error(
                f"OpenAIClient: failed to parse response as {response_model.__name__}. "
                f"Raw content (first 500): {raw_content[:500]}"
            )
            raise ValueError(
                f"Failed to parse LLM response as {response_model.__name__}: {exc}"
            ) from exc

        logger.debug(f"OpenAIClient: parsed {response_model.__name__} successfully")
        return parsed
