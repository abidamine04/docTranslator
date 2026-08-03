# Architecture

## Services

- `web`: Next.js/React reader workspace. It uploads files, streams job events, edits
  blocks, displays completion metrics, and manages provider and application settings.
- `api`: FastAPI boundary for documents, elements, exports, settings, and health.
- `worker`: Dramatiq process. Jobs are idempotent and store stage/page progress.
- `postgres`: durable metadata and audit-friendly block state.
- `redis`: job broker.
- local volume: immutable source files and generated versions. An S3 adapter can
  replace this boundary later.

## Document model

Each page contains geometry-preserving elements. A text element keeps its original
and translated strings, bounding box, source/target language, confidence, style,
and one explicit status: `detected`, `translated`, `unchanged`, `low_confidence`,
`failed`, `unsupported`, or `manually_edited`.

The PDF processor extracts native spans with PyMuPDF. Export begins with the source
PDF, redacts only original text rectangles, and inserts translated text into the
same geometry. If fitting fails, it records an overflow issue; it never silently
clips a block.

## Provider boundary

`TranslationProvider` is implemented by OpenAI-compatible and LibreTranslate
adapters. Configuration is database-backed and API keys are encrypted with a key
derived from `PROVIDER_SECRET_ENCRYPTION_KEY` or `APP_SECRET_KEY`. Document text is
wrapped as data and the system prompt explicitly rejects instructions within it.

The singleton `application_settings` row stores user-adjustable defaults, document
limits, retention, storage root, OCR confidence, language-detection context, and
the base translation prompt. Environment values seed this row only on first use.

The provider cache key includes normalized text, language pair, and provider
configuration fingerprint. Failed batches are retried per block.

## Security boundaries

Uploads are validated by extension, MIME signature, size, normalized storage path,
and PDF page count. Converters will run in isolated containers in the Office-file
milestone. Cloud providers are contacted only after an administrator enables one.
No analytics are included.

## Quality reporting

Completion is derived from persisted elements, never inferred from job completion.
The API reports detected, translated, failed, untranslated, low-confidence, overflow,
OCR coverage, and translation coverage. A document is `complete_with_warnings` when
any unresolved region remains.
