"""AI service for RepoBuddy AI. Talks to a local Ollama model."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

SYSTEM_PROMPT = """You are RepoBuddy, a friendly senior engineer who helps \
beginners contribute to open-source projects. You are given the text of a \
GitHub issue. Produce guidance that is encouraging, concrete, and honest.

Return your answer STRICTLY as a single JSON object with exactly these keys:
{
  "explanation": "A beginner-friendly explanation of the issue. 2-4 short paragraphs.",
  "steps": ["Ordered, concrete implementation steps."],
  "files_to_inspect": ["Likely files to look at, with a short reason."],
  "tests": ["Specific tests to write or run."],
  "checklist": ["Things to confirm before opening a pull request."]
}

Rules:
- Output ONLY the JSON object. No markdown, no code fences.
- "explanation" is a string. The other four keys are arrays of strings.
- Never claim to have read the repository."""


class AIConfigError(RuntimeError):
    """Raised when the service is not set up correctly."""


class AIResponseError(RuntimeError):
    """Raised when the model call fails or returns something unusable."""


def _coerce_result(raw: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    explanation = raw.get("explanation", "")
    result["explanation"] = explanation if isinstance(explanation, str) else str(explanation)
    for key in ("steps", "files_to_inspect", "tests", "checklist"):
        value = raw.get(key, [])
        if isinstance(value, list):
            result[key] = [str(item) for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            result[key] = [value.strip()]
        else:
            result[key] = []
    return result


def analyze_issue(issue_text: str) -> dict[str, Any]:
    model_id = os.environ.get("MODEL_ID", "llama3.2:3b").strip() or "llama3.2:3b"
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip().rstrip("/")
    if base_url.endswith("api.groq.com") or "groq" in base_url:
        base_url = "http://localhost:11434/v1"

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is the GitHub issue. Respond with the JSON object.\n\n"
                    "=== GITHUB ISSUE START ===\n"
                    f"{issue_text}\n"
                    "=== GITHUB ISSUE END ==="
                ),
            },
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise AIResponseError(
                f"Ollama could not find model '{model_id}'. "
                f"Run this in PowerShell: ollama pull {model_id}"
            ) from exc
        raise AIResponseError(f"Ollama returned an error (HTTP {exc.code}).") from exc
    except urllib.error.URLError as exc:
        raise AIResponseError(
            "Could not reach Ollama. Make sure the Ollama app is running."
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise AIResponseError("Ollama took too long or sent a bad reply. Try again.") from exc

    try:
        content = (body["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIResponseError("The model returned an empty response.") from exc
    if not content:
        raise AIResponseError("The model returned an empty response.")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIResponseError("The model did not return valid JSON. Try again.") from exc
    if not isinstance(parsed, dict):
        raise AIResponseError("The model returned JSON that was not an object.")

    return _coerce_result(parsed)
