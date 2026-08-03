# DocTranslator

DocTranslator is a self-hosted document translation workspace focused on preserving
PDF geometry and making every detected text region auditable. This repository
contains the first usable milestone: native PDF upload, extraction, language
detection, queued translation, side-by-side review, block editing, quality metrics,
and searchable PDF export.

No translation API is hardcoded. Provider URL, endpoint paths, API key, model,
timeout, retries, batch/context/output sizes, temperature, rate limit, custom
headers, TLS behavior, and prompts are configured from **Settings** and stored
server-side. General translation defaults, document limits, OCR threshold,
retention, and storage root are database-backed there as well. Environment values
for those fields are first-run seeds only. Secrets are encrypted at rest.

## Quick start

1. Copy `.env.example` to `.env`.
2. Set `APP_SECRET_KEY` and `ADMIN_API_TOKEN`.
3. Run `docker compose up --build`.
4. Open <http://localhost:3000>, then configure a provider in **Settings**.

Enter the provider URL and model manually. Local OpenAI-compatible services may
leave the API key blank. No provider, URL, or model is created automatically.

Docker runs database migrations before starting the API. The complete hardcoded
setting classification is in [Configuration audit](CONFIGURATION_AUDIT.md).

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

## Open-source license

Copyright (c) 2026 DocTranslator contributors.

DocTranslator is open-source software licensed under the
[GNU Affero General Public License v3.0](LICENSE). If you modify the software and
make it available to users over a network, the AGPL requires that those users can
obtain the corresponding source code for the version they are using.

This license choice is also compatible with the open-source PyMuPDF/MuPDF build
used by the API and worker. A distributor that does not want to operate under the
AGPL must obtain an appropriate commercial PyMuPDF license and separately arrange
a different license for DocTranslator from its copyright holders. Third-party
components remain under their own licenses; see
[Third-Party Notices](THIRD_PARTY_NOTICES.md).
