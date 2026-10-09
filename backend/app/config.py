from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "DocFusion AI"
    environment: str = "development"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: int = 180
    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'docfusion.db'}"
    upload_dir: str = str(ROOT_DIR / "data" / "uploads")
    generated_dir: str = str(ROOT_DIR / "data" / "generated")
    verification_dir: str = str(ROOT_DIR / "data" / "verification")
    key_dir: str = str(ROOT_DIR / "data" / "keys")
    max_upload_size: int = 10 * 1024 * 1024
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    request_timeout: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.allowed_origins.split(",") if x.strip()]

    def ensure_dirs(self) -> None:
        for path in [self.upload_dir, self.generated_dir, self.verification_dir, self.key_dir]:
            Path(path).mkdir(parents=True, exist_ok=True)

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Migrate projects that still have the retired/restricted 2.5 Flash-Lite
    # setting in their existing .env file. The explicit 3.5 Flash-Lite model
    # is the supported default for new Gemini API projects.
    if settings.gemini_model.strip() == "gemini-2.5-flash-lite":
        settings.gemini_model = "gemini-3.5-flash-lite"
    settings.ensure_dirs()
    return settings
