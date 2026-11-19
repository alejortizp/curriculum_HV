"""The only door to the Anthropic API. No other module imports `anthropic`.

Callers receive `complete_json` as a default argument, so tests replace it with a
fake and never spend API credit.
"""

import json
import os
from functools import cache
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent

EXTRACTION_MODEL = "claude-opus-5-5"
EXTRACTION_EFFORT = "low"
TAILORING_MODEL = "claude-opus-5-5"
TAILORING_EFFORT = "high"


class LLMError(Exception):
    pass


@cache
def _client() -> anthropic.Anthropic:
    # Same resolution as the Gemini key: environment first, then .env
    if not os.environ.get("ANTHROPIC_API_KEY"):
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        # without this the SDK fails later with a TypeError and a traceback
        raise LLMError("No hay credenciales de Anthropic: define ANTHROPIC_API_KEY en .env "
                       "o como variable de entorno.")
    return anthropic.Anthropic()


def complete_json(prompt: str, schema: dict, *, model: str, effort: str,
                  max_tokens: int = 16000) -> dict:
    """One request whose answer is JSON conforming to `schema`."""
    try:
        response = _client().beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            # if the model declines, the API reruns the request on a fallback model
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError as e:
        raise LLMError("Credenciales de Anthropic inválidas o ausentes.") from e
    except anthropic.RateLimitError as e:
        raise LLMError("Límite de uso alcanzado; intenta de nuevo en unos minutos.") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"Error de la API ({e.status_code}): {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError("Sin conexión con la API de Anthropic.") from e
    if response.stop_reason == "refusal":
        raise LLMError("El modelo rechazó la solicitud.")
    if response.stop_reason == "max_tokens":
        raise LLMError("La respuesta se cortó por max_tokens.")
    return json.loads(next(b.text for b in response.content if b.type == "text"))
