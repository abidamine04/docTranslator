import asyncio
import json
import time
from dataclasses import dataclass, field

import httpx

from .application_settings import DEFAULT_TRANSLATION_SYSTEM_PROMPT
from .models import ProviderConfiguration
from .security import decrypt_secret

@dataclass
class TranslationProvider:
    config: ProviderConfiguration
    system_prompt: str = DEFAULT_TRANSLATION_SYSTEM_PROMPT
    _last_request_at: float = field(default=0.0, init=False)

    async def translate(self, texts: list[str], source: str, target: str, tone: str) -> list[str]:
        if self.config.provider_type == "openai_compatible":
            return await self._openai(texts, source, target, tone)
        if self.config.provider_type == "libretranslate":
            return await self._libre(texts, source, target)
        raise ValueError(f"Unsupported provider: {self.config.provider_type}")

    async def _openai(self, texts: list[str], source: str, target: str, tone: str) -> list[str]:
        if not self.config.model:
            raise ValueError("A model name is required for an OpenAI-compatible provider")
        approximate_input_characters = sum(len(text) for text in texts)
        if approximate_input_characters > self.config.context_size * 4:
            raise ValueError("Translation input exceeds the configured context size")
        system = self.system_prompt.replace("{source}", source).replace("{target}", target)
        if self.config.custom_system_prompt:
            system = f"{system}\nAdditional administrator guidance:\n{self.config.custom_system_prompt}"
        body = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps({"tone": tone, "segments": texts}, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = dict(self.config.custom_headers or {})
        if key := decrypt_secret(self.config.encrypted_api_key):
            headers["Authorization"] = f"Bearer {key}"
        url = f"{self.config.base_url.rstrip('/')}{self.config.chat_completions_path}"
        response = await self._post(url, body, headers)
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        result = parsed.get("translations") if isinstance(parsed, dict) else parsed
        if not isinstance(result, list) or len(result) != len(texts):
            raise ValueError("Provider returned an invalid translation count")
        return [str(value) for value in result]

    async def _post(self, url: str, payload: dict, headers: dict[str, str]) -> httpx.Response:
        last_error: Exception | None = None
        async with httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            verify=self.config.verify_tls,
        ) as client:
            for attempt in range(self.config.max_retries + 1):
                minimum_interval = 60 / self.config.rate_limit_per_minute
                wait_for = minimum_interval - (time.monotonic() - self._last_request_at)
                if wait_for > 0:
                    await asyncio.sleep(wait_for)
                try:
                    self._last_request_at = time.monotonic()
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                    last_error = exc
                    if attempt == self.config.max_retries:
                        raise
                    await asyncio.sleep(min(2 ** attempt, 10))
        raise RuntimeError("Provider request failed") from last_error

    async def _libre(self, texts: list[str], source: str, target: str) -> list[str]:
        key = decrypt_secret(self.config.encrypted_api_key)
        payload = {"q": texts, "source": source if source != "auto" else "auto", "target": target, "format": "text"}
        if key:
            payload["api_key"] = key
        url = f"{self.config.base_url.rstrip('/')}{self.config.translate_path}"
        response = await self._post(url, payload, dict(self.config.custom_headers or {}))
        data = response.json()
        values = data.get("translatedText")
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list) or len(values) != len(texts):
            raise ValueError("LibreTranslate returned an invalid translation count")
        return [str(value) for value in values]
