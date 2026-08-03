from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class TranslateRequest(BaseModel):
    target_language: str | None = Field(default=None, min_length=2, max_length=24)
    source_language: str | None = None
    provider_id: str | None = None
    tone: str | None = None
    preserve_names: bool = True
    preserve_terminology: bool = True


class ElementPatch(BaseModel):
    translated_text: str = Field(min_length=1)


class ProviderWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider_type: Literal["openai_compatible", "libretranslate"]
    base_url: HttpUrl
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: int = Field(default=60, ge=5, le=600)
    max_retries: int = Field(default=2, ge=0, le=10)
    batch_size: int = Field(default=12, ge=1, le=100)
    context_size: int = Field(default=8192, ge=256, le=1000000)
    temperature: float = Field(default=0.1, ge=0, le=2)
    custom_system_prompt: str | None = None
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    max_output_tokens: int = Field(default=4096, ge=1, le=1000000)
    chat_completions_path: str = Field(default="/chat/completions", min_length=1, max_length=200)
    models_path: str = Field(default="/models", min_length=1, max_length=200)
    translate_path: str = Field(default="/translate", min_length=1, max_length=200)
    custom_headers: dict[str, str] = Field(default_factory=dict)
    verify_tls: bool = True
    is_active: bool = False

    @field_validator("chat_completions_path", "models_path", "translate_path")
    @classmethod
    def normalize_endpoint_path(cls, value: str) -> str:
        value = value.strip()
        return value if value.startswith("/") else f"/{value}"


class ProviderTest(BaseModel):
    provider_id: str


class ApplicationSettingsWrite(BaseModel):
    default_target_language: str = Field(min_length=2, max_length=24)
    ocr_confidence_threshold: float = Field(ge=0, le=1)
    max_upload_mb: int = Field(ge=1, le=100000)
    max_page_count: int = Field(ge=1, le=100000)
    file_retention_days: int = Field(ge=0, le=36500)
    default_translation_tone: str = Field(min_length=1, max_length=50)
    translation_system_prompt: str = Field(min_length=1, max_length=50000)
    storage_root: str = Field(min_length=1, max_length=2000)
    language_detection_sample_chars: int = Field(ge=100, le=1000000)
