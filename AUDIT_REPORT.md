# DocTranslator Technical Audit

Audit date: 2026-07-28

## Executive finding

DocTranslator is a promising prototype and useful integration layer, not yet a
reliable general-purpose document translator. Its real path is limited to native
text PDFs:

`upload -> PyMuPDF extraction -> langdetect -> Dramatiq job -> configured HTTP
translation provider -> per-line persistence -> PyMuPDF redaction/insertion ->
download`

OCR, image-text replacement, Office formats, translation memory, glossary
support, and durable human-review workflows are not implemented. No fake
translation provider exists, which is good, but the UI contains controls and
labels for behavior that is not functional (search, rotate, and a translated
preview before export).

## Architecture

| Area | Implementation | Audit status |
|---|---|---|
| Frontend | Next.js 16, React 19, TypeScript, react-pdf/PDF.js | Implemented but unverified in a browser |
| API | FastAPI, SQLAlchemy, Alembic | Implemented but only lightly tested |
| Jobs | Dramatiq with Redis | Implemented but unverified end-to-end |
| Database | PostgreSQL in Compose; SQLite development fallback | Implemented but PostgreSQL unverified |
| Storage | Local Docker volume and per-document UUID directories | Partially implemented |
| PDF parsing | PyMuPDF native text-line extraction | Implemented and unit-smoke-tested |
| OCR | Scanned-page heuristic and review issue only | Placeholder only |
| Language detection | `langdetect` over the first 10,000 extracted characters | Implemented but unverified across requested languages |
| Translation | OpenAI-compatible and LibreTranslate HTTP adapters | Implemented but no real provider run completed |
| Layout reconstruction | Redact source rectangles and insert Helvetica text | Partially implemented |
| Image text | None | Missing |
| Export | Searchable PDF insertion for translated native text | Implemented with a P0 data-loss defect |
| Authentication | Shared token only on provider-write routes; fail-open if unset | Broken |
| Logging/monitoring | Framework logs and health routes only | Partially implemented |
| Testing | Two secret tests and one PDF fixture smoke test | Partially implemented |

## Real execution-path findings

1. Upload streams bytes to `original.pdf`, enforces a configured byte limit, and
   checks filename suffix plus `%PDF-`.
2. The API creates a job and sends it to Redis. Analysis opens the untrusted PDF
   in the worker, enforces page count, and extracts text lines.
3. Pages with fewer than 20 native characters are marked `scanned` and receive
   `ocr_required`; no OCR engine is called.
4. Language detection samples extracted native text only.
5. Translation sends batches to the configured provider, retries a failed batch
   one block at a time, and persists per-element failures.
6. The UI displays the original PDF in both panes until an export exists; this is
   not a live translated preview.
7. Export redacts every translated block before testing whether replacement text
   fits. An overflow can therefore erase source text without inserting a
   replacement. This is P0.
8. Download returns the generated file without authorization.

## What works

- Source files are stored separately from exports.
- UUID-derived storage paths prevent user-controlled path traversal.
- Translation output count is validated.
- Failed translation batches fall back to per-block attempts.
- Provider secrets are encrypted at rest.
- PDF text-layer rendering remains selectable when insertion succeeds.
- Type checking, frontend production build, migration, lint, and the small unit
  suite pass in the local environment (see `TEST_RESULTS.md`).

## Incomplete, simulated, or misleading behavior

- OCR is only a warning; OCR coverage cannot be truthfully reported.
- “Translation preview pending” displays the original, not translated blocks.
- Search and rotate controls have no handlers.
- Provider retry count, context size, and rate limit are stored but unused.
- File retention is configured but no cleanup task exists.
- Cancellation is cooperative and checked only between translation batches or
  analysis progress callbacks.
- No translation cache, glossary, translation memory, image inpainting, or
  Office processing exists.
- “Private by design” depends on administrator provider choice and is not an
  enforced no-network guarantee.

## Reliability and maintainability conclusion

Preserve the service boundaries, relational element model, immutable-source
storage approach, and provider adapters. Strengthen them incrementally. Do not
replace the application wholesale. The first fix must prevent export from
redacting a block unless replacement rendering has been proven to fit.

## Post-audit P0 remediation

The P0 implementation completed after the baseline audit now preflights text fit before redaction, centralizes exact completion accounting, fails closed on all API routes, sends authentication headers throughout the browser flow, fixes unchanged individual-retry status, removes the web image build blocker, and hardens application containers. Regression tests open both fitting and overflowing exports and prove that overflowing source text is preserved. See `TEST_RESULTS.md`.

The P0-to-P1 gate is still closed because Docker runtime startup and a real translation-provider call could not be executed in this environment. No P1 work was started.
