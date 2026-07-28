# Feature Verification Matrix

Statuses reflect executed evidence, not the existence of UI controls or classes.

| Feature | Status | Evidence |
|---|---|---|
| PDF upload size limit | Implemented but unverified | Streaming check in `storage.py`; no endpoint test |
| Extension/signature validation | Partially implemented | Suffix and first five bytes only |
| Native text extraction | Fully implemented and verified | PyMuPDF path inspected; searchable fixture test passes |
| All-page processing | Implemented but unverified | Iterates all pages; no large/multipage integration fixture |
| Scanned-PDF OCR | Placeholder only | Adds `ocr_required`; invokes no OCR engine |
| Image-text detection/replacement | Missing | Non-text PDF blocks are ignored |
| Language detection | Implemented but unverified | `langdetect` sample; no language matrix |
| OpenAI-compatible translation | Implemented but unverified | Real HTTP adapter; no live provider result |
| LibreTranslate translation | Implemented but unverified | Real HTTP adapter; no live provider result |
| Provider retries | Partially implemented | Batch-to-block fallback; configured `max_retries` unused |
| Layout preservation | Partially implemented | Bounding-box insertion; font, color, rotation, RTL not preserved |
| Overflow reporting | Fully implemented and verified | Fit is preflighted; overflow preserves source text and has regression coverage |
| Side-by-side reader | Partially working differentiator | Two PDF.js panes; no synchronized scroll |
| Block editing | Implemented but unverified | API and UI exist; no endpoint/browser test |
| Completion report | Fully implemented and verified | Exact counts/formulas and terminal status covered by tests |
| Searchable export | Partially implemented | Text insertion path exists; only fixture PDF searchability tested |
| Original immutability | Implemented but unverified | Export opens source and saves a destination |
| Export download | Implemented but insecure | FileResponse has no authorization |
| Authentication/authorization | Fully implemented and verified | All API routes fail closed; header flow type-checks/builds |
| Docker deployment | Implemented but runtime-unverified | Compose config passes and images are hardened; daemon unavailable |
| Frontend type check/build | Fully implemented and verified | Both commands pass |
| Backend lint/unit tests | Fully implemented and verified for current suite | Ruff and 14 tests pass |
| Integration/E2E tests | Missing | No such tests or fixtures |
| Logging/monitoring | Partially implemented | Health checks and default logs only |

## Requested real-file matrix

No supplied fixtures exist for native, scanned, image-text, multi-column, table,
Arabic, mixed-language, or large PDFs. A generated one-line native PDF exercised
only searchable text creation. All remaining requested real-file cases are
**unverified**, not passed.
