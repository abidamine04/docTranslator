# Final configuration audit

Audit scope: the complete repository, including backend, frontend, migrations,
Docker files, examples, tests, and documentation. Generated dependency/build
artifacts (`node_modules`, `.next`, lock files, and `.git`) were excluded.

| Category | Result and classification |
| --- | --- |
| Provider URLs | **Default configurable from UI:** provider base URL and endpoint paths are persisted in `provider_configurations`. **Safe internal/infrastructure constants:** the browser-to-API URL, database URL, Redis URL, and CORS origin are bootstrap infrastructure. Documentation placeholders and test `.invalid` URLs are non-operational examples/fixtures. **Invalid:** none. |
| Model names | **Default configurable from UI:** model is entered and persisted per provider. No concrete runtime model default remains. Generic placeholders and test values are non-operational. **Invalid:** none. |
| API keys | **Default configurable from UI:** provider keys are entered in Settings and encrypted at rest; plaintext values are not returned. Empty keys remain supported. No literal provider key was found. **Invalid:** none. |
| OCR engines | No runtime OCR engine is currently implemented or selected. Product-comparison documentation names possible future engines only. **Invalid:** none. |
| Executable paths | No OCR/provider executable path was found. Container commands are infrastructure startup constants. **Invalid:** none. |
| SMTP hosts | No SMTP integration or SMTP host was found. |
| Storage endpoints | **Default configurable from UI:** storage root is seeded from infrastructure configuration on first run and then read from the database. Existing document paths remain attached to each document so changing the root does not orphan them. **Invalid:** none. |
| Translation prompts | **Default configurable from UI:** the safety-preserving base system prompt is a first-run database seed; the global prompt and per-provider custom instructions are editable. Protocol response-shape instructions remain part of that editable prompt. **Invalid:** none. |
| Timeouts | **Default configurable from UI:** provider timeout. **Safe internal constants:** Docker health-check timeouts and UI/SSE status refresh cadence. **Invalid:** none. |
| Retry values | **Default configurable from UI:** provider maximum retries; runtime requests now consume it. **Safe internal constants:** Docker health retries and zero Dramatiq retries (prevents duplicate document side effects; provider retries happen inside the adapter). Exponential backoff is an internal algorithm bound. **Invalid:** none. |
| Batch sizes | **Default configurable from UI:** provider translation batch size. **Safe internal constant:** the 1 MiB streaming upload chunk, which limits memory and does not constrain user document size. **Invalid:** none. |
| Context sizes | **Default configurable from UI:** provider context size and language-detection sample characters. **Safe internal constants:** PDF layout/font-fit algorithm bounds. **Invalid:** none. |
| Upload limits | **Default configurable from UI:** maximum upload MB and maximum PDF page count. MIME signature and PDF-only milestone checks are safe validation constants. **Invalid:** none. |
| Language defaults | **Default configurable from UI:** default target language and translation tone. The supported-language catalog and `auto`/`unknown` sentinel values are safe protocol/domain constants. **Invalid:** none. |

## Bootstrap boundary

Environment variables remain for values needed before the Settings API and database
can be reached: application environment, database, Redis, browser API address,
CORS origins, initial storage root, and cryptographic secrets. The operational
values for storage, retention, document limits, OCR threshold, and target language
are only first-run seeds; subsequent changes are database-backed and take effect
without a restart.

Provider URLs, models, credentials, endpoint paths, timeouts, retries, batch/context
sizes, output limits, headers, TLS behavior, rate limit, temperature, and prompts
are never environment-only and are editable in Settings.
