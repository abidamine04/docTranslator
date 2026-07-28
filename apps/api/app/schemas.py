from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class TranslateRequest(BaseModel):
    target_language: str = Field(min_length=2, max_length=24)
    source_language: str | None = None
    provider_id: str | None = None
    tone: str = "neutral"
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
    is_active: bool = False


class ProviderTest(BaseModel):
    provider_id: str

