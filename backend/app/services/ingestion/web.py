import requests
from bs4 import BeautifulSoup
from ...config import get_settings
from .base import ExtractionResult, IngestionError
from ...utils.validators import validate_url

def extract_web(url: str) -> ExtractionResult:
    settings = get_settings()
    try:
        url = validate_url(url)
        response = requests.get(url, timeout=settings.request_timeout, headers={"User-Agent": "DocFusionAI/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        if not text:
            raise IngestionError("No readable text found on the page")
        return ExtractionResult(text[:1_000_000], {"url": url, "retrieved_at": response.headers.get("date"), "status_code": response.status_code, "title": soup.title.get_text(strip=True) if soup.title else ""})
    except requests.RequestException as exc:
        raise IngestionError(f"URL retrieval failed: {exc}") from exc
