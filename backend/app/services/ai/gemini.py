from pydantic import ValidationError
from .base import AIProvider, AIUnavailable
from .prompts import build_prompt
from ...config import get_settings
from ...schemas.analysis import AnalysisOutput

class GeminiProvider(AIProvider):
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.gemini_api_key:
            raise AIUnavailable("GEMINI_API_KEY is not configured")
        try:
            from google import genai
        except ImportError as exc:
            raise AIUnavailable("google-genai package is not installed") from exc
        self.client = genai.Client(api_key=self.settings.gemini_api_key)

    def analyze_sources(self, sources: list[dict]) -> AnalysisOutput:
        try:
            prompt = build_prompt(sources)
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                # Keep Gemini's JSON mode but validate against our Pydantic model locally.
                # Passing the full Pydantic schema can include `additionalProperties`,
                # which some Gemini API/model combinations reject. The prompt already
                # includes the required output structure.
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            if getattr(response, "parsed", None) is not None:
                result = response.parsed
                if isinstance(result, AnalysisOutput):
                    return result
            if not response.text:
                raise AIUnavailable("Gemini returned an empty response")
            return AnalysisOutput.model_validate_json(response.text)
        except ValidationError as exc:
            raise AIUnavailable(f"Gemini returned invalid structured output: {exc}") from exc
        except Exception as exc:
            raise AIUnavailable(f"Gemini request failed: {exc}") from exc
