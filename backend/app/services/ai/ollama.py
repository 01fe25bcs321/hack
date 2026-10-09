import json
import requests
from pydantic import ValidationError
from .base import AIProvider, AIUnavailable
from .prompts import build_prompt
from ...config import get_settings
from ...schemas.analysis import AnalysisOutput

class OllamaProvider(AIProvider):
    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.settings = get_settings()
        self.base_url = (base_url or self.settings.ollama_base_url).rstrip('/')
        self.model = model or self.settings.ollama_model
        self.timeout = self.settings.ollama_timeout

    def list_models(self) -> list[str]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return [m.get("name") for m in response.json().get("models", []) if m.get("name")]
        except Exception as exc:
            raise AIUnavailable(f"Ollama is unavailable at {self.base_url}: {exc}") from exc

    def analyze_sources(self, sources: list[dict]) -> AnalysisOutput:
        prompt = build_prompt(sources) + "\n\nReturn JSON matching this exact structure: " + json.dumps(AnalysisOutput.model_json_schema(), ensure_ascii=False)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            if response.status_code == 404:
                raise AIUnavailable(f"Ollama model '{self.model}' was not found. Pull it first with: ollama pull {self.model}")
            response.raise_for_status()
            data = response.json()
            raw = data.get("response", "")
            if not raw:
                raise AIUnavailable("Ollama returned an empty response")
            return AnalysisOutput.model_validate_json(raw)
        except ValidationError as exc:
            raise AIUnavailable(f"Ollama returned invalid structured output: {exc}") from exc
        except AIUnavailable:
            raise
        except requests.RequestException as exc:
            raise AIUnavailable(f"Ollama request failed: {exc}") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise AIUnavailable(f"Ollama returned invalid JSON: {exc}") from exc
