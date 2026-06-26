import json
from typing import Any

from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)


class OpenAiJsonHelper:
    """Helpers for turning a raw GPT text response into a parsed JSON object.

    Shared by the AI services that prompt the model to return a single JSON
    object (``FormAiFillService`` for form values, ``FormTemplateAiService``
    for template specs). Centralizes the fence-stripping + parse + shape-check
    so the three call sites stay in sync.
    """

    @staticmethod
    def strip_code_fences(response: str) -> str:
        """Remove a surrounding ```...``` / ```json ... ``` fence if present."""
        text = response.strip()
        if not text.startswith("```"):
            return text
        # Drop the opening fence line (``` or ```json) and the closing fence.
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @classmethod
    def parse_json_object(cls, response: str) -> dict[str, Any]:
        """Strip fences then parse the response as a JSON object.

        Raises ``BadRequestException`` when the response is not valid JSON or
        is not a JSON object (e.g. an array or scalar).
        """
        cleaned = cls.strip_code_fences(response)
        try:
            parsed = json.loads(cleaned)
        except Exception as err:
            raise BadRequestException(
                f"The AI returned a response that is not valid JSON: {err}"
            ) from err
        if not isinstance(parsed, dict):
            raise BadRequestException(
                "The AI response must be a JSON object."
            )
        return parsed
