from urllib.parse import urlparse

def validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only valid HTTP/HTTPS URLs are supported")
    return url.strip()
