# DocTranslator

DocTranslator is a self-hosted document translation workspace focused on preserving
PDF geometry and making every detected text region auditable. This repository
contains the first usable milestone: native PDF upload, extraction, language
detection, queued translation, side-by-side review, block editing, quality metrics,
and searchable PDF export.

No translation API is hardcoded. Provider URL, API key, model, timeout, retries,
batch size, context size, temperature, rate limit, and system prompt are configured
from **Settings** and stored server-side. Secrets are encrypted at rest.

## Quick start

1. Copy `.env.example` to `.env`.
2. Set `APP_SECRET_KEY` and `ADMIN_API_TOKEN`.
3. Run `docker compose up --build`.
4. Open <http://localhost:3000>, then configure a provider in **Settings**.

For Ollama, choose `OpenAI compatible`, use `http://host.docker.internal:11434/v1`,
leave the API key blank, and enter an installed model such as `qwen2.5:7b`.
For LibreTranslate, choose `LibreTranslate` and use its service URL.

The API documentation is available at <http://localhost:8000/docs>.

## Development

Backend:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL="sqlite:///./dev.db"
$env:STORAGE_ROOT="./storage"
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd apps/web
npm install
npm run dev
```

## Current scope and next milestone

Native PDFs are processed without rasterizing the original page. Translated text is
drawn into the original bounding boxes, with overflow surfaced as a review warning.
The original upload is immutable and exports are separate versions.

OCR, image inpainting, Office processors, authentication UI, distributed cancellation,
and visual-regression fixtures are documented design targets and are not falsely
reported as complete. See [Architecture](docs/architecture.md) and
[Operations](docs/operations.md).
