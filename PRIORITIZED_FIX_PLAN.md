# Prioritized Fix Plan

Only P0 items are authorized for implementation in the current work.

| Priority | Problem | Evidence | User impact | Proposed fix | Files affected | Complexity | Regression risk | Test required |
|---|---|---|---|---|---|---|---|---|
| P0-1 | Web container build/start blocker | Dockerfile copies `/app/public`, but repository has no `public` directory | Compose web image cannot complete | Remove optional copy and verify standalone output | `apps/web/Dockerfile` | Low | Low | frontend build; Compose build when daemon available |
| P0-2 | Export redacts text before fit is known | `export_pdf` applies every redaction, then attempts insertion | Blank/data-lost translated regions | Preflight fit; redact/render only fitting blocks; preserve source and report overflow | `pdf_processor.py`, tests | Medium | Medium | overflow and successful export tests |
| P0-3 | Detected text and unresolved work can be reported complete | unchanged counted successful; OCR/review issues ignored; requested metrics absent | Silent incompleteness and false “complete” | Centralize exact report formulas and terminal status from elements/issues | API/worker/models/tests | Medium | Medium | status/count/formula tests |
| P0-4 | API authorization fails open | Most `/api/*` routes unprotected; empty configured token bypasses provider guard | Document disclosure/deletion and admin takeover | Fail closed; protect API; send token from UI without query strings | API security/main; web API/pages/PDF pane; tests | Medium | Medium | auth middleware and frontend type/build |
| P0-5 | Worker/container lacks basic isolation | Images run as root; no capability/read-only restrictions | Parser compromise has broader impact | Non-root images and Compose hardening compatible with writable data/temp | Dockerfiles, Compose | Medium | Medium | config validation/build/start |

## P1 (not authorized until all P0 gates pass)

Real OCR, synchronized scrolling, rendering fidelity/RTL fonts, durable retries,
provider rate limiting, browser E2E coverage, and full requested fixture corpus.

## Gate

Do not start P1 until the stack starts, a real provider translates a real PDF, the
export opens, every detected block is accounted for, terminal status is accurate,
and all Critical/High findings are resolved.

## Implementation status (2026-07-28)

- P0-1 through P0-5: implemented with available lint/unit/build/config checks.
- Direct API and standalone web startup: verified.
- Full Compose startup: blocked by unavailable Docker daemon.
- Real provider translation: blocked because local providers were unavailable and external DNS failed.
- P1: not started.
