# Test Results

Run date: 2026-07-28. Commands are shown exactly apart from shell prompt.

## Baseline

| Command | Outcome |
|---|---|
| `npm test` (`apps/web`) | PASS: TypeScript `tsc --noEmit` |
| `npm run build` (`apps/web`) | PASS: Next.js 16.2.12 production build; four routes generated |
| `docker compose config --quiet` | PASS |
| `docker compose build` | BLOCKED: Docker Desktop Linux daemon pipe was not running |
| `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///D:/amine/projects/docTranslator/audit-verification.db` | PASS: revision `0001_initial` |
| `python -m ruff check app tests migrations` | PASS |
| `python -m pytest -q` | ENVIRONMENTAL ERROR: 2 passed; pytest could not access `C:\Users\abida\AppData\Local\Temp\pytest-of-abida` |
| `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-verification` | PASS: 3 passed, 5 PyMuPDF/SWIG deprecation warnings |

## Unexecuted or blocked baseline checks

- API, worker, PostgreSQL, Redis, and browser E2E startup: blocked by stopped Docker daemon.
- Real translation: no configured/reachable translation provider established.
- Requested native/scanned/image/multicolumn/table/Arabic/mixed/large fixture matrix:
  fixtures absent; not claimed as passed.
- Visual comparison: not executed.

## P0 fix results

### P0-1 — web container build blocker

- Change: removed the runtime-stage copy of absent `/app/public`.
- `npm test` — PASS (`tsc --noEmit`).
- `npm run build` — PASS; Next.js production build completed and generated all four routes.
- `docker compose build` remains blocked because the Docker Desktop Linux daemon is unavailable.

### P0-2 — export data loss on overflow

- Red test: `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-2-red tests/test_pdf_processor.py` — EXPECTED FAIL: overflow export removed part of `Original source text`.
- Change: preflight textbox fit without committing; redact/render only fitting blocks; preserve source and create one unresolved overflow issue otherwise.
- Intermediate full suite — 5 tests passed, but Ruff correctly failed on appended import placement; no next fix was started.
- Final `python -m ruff check app tests migrations` — PASS.
- Final `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-2-final3` — PASS: 5 passed, 5 PyMuPDF/SWIG deprecation warnings.

### P0-3 — completeness accounting and terminal status

- Red test: `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-3-red tests/test_quality.py` — EXPECTED COLLECTION ERROR: `app.quality` did not exist.
- Change: centralized all requested block/page/issue counts, published both formulas, accounted for every block, and derived document/job/export status from unresolved work.
- Intermediate full suite — 8 tests passed; Ruff found two unused imports and one line-length issue, which were corrected before continuing.
- Final `python -m ruff check app tests migrations` — PASS.
- Final `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-3-export` — PASS: 8 passed, 5 PyMuPDF/SWIG deprecation warnings.

### P0-4 — fail-closed API authorization

- Red test: `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-4-red tests/test_api_auth.py` — EXPECTED FAIL: 2 failed, proving unauthenticated access and empty-token fail-open behavior.
- Backend change: all `/api/*` routes require `X-Admin-Token`; unset configuration returns 503; health remains public.
- `python -m ruff check app tests migrations` — PASS.
- `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-4-backend` — PASS: 12 passed, 57 dependency/deprecation warnings.
- Frontend change: session-scoped token headers for fetch, XHR, PDF.js, authenticated job polling, and authenticated blob downloads.
- First `npm test; npm run build` — FAIL: installed react-pdf types rejected `httpHeaders` in `file`; no next P0 fix was started.
- Correction: moved headers to react-pdf's supported memoized `options` prop.
- Final `npm test` — PASS (`tsc --noEmit`).
- Final `npm run build` — PASS; all four routes generated.

### P0-5 — application-container isolation

- Red assertion: Compose output contained no `no-new-privileges` entry — EXPECTED FAIL.
- Change: API/worker/web runtime users are non-root; application services use read-only root filesystems, `no-new-privileges`, all capabilities dropped, and explicit tmpfs/data writes.
- `docker compose config --quiet` plus assertions for three hardened services — PASS.
- `python -m ruff check app tests migrations` — PASS.
- `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-5-final` — PASS: 12 passed, 57 dependency/deprecation warnings.
- `npm test` — PASS (`tsc --noEmit`).
- `npm run build` — PASS; all four routes generated.
- Runtime container verification remains blocked by the stopped Docker Desktop Linux daemon.

### P0-3 follow-up — unchanged individual retries

- Red test: `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-3-retry-red tests/test_translation.py` — EXPECTED FAIL: both unchanged responses were marked `translated`.
- Change: individual retry results now use the same translated-versus-unchanged comparison as batch results.
- `python -m ruff check app tests migrations` — PASS.
- `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-p0-3-retry-green` — PASS: 13 passed, 57 dependency/deprecation warnings.

## Direct startup and remaining gate checks

- API direct startup: PASS. `uvicorn app.main:app --host 127.0.0.1 --port 8000` returned HTTP 200 for `/health/live` and authenticated `/api/languages` (14 languages).
- Web standalone startup: PASS. `PORT=3001 node .next/standalone/server.js` returned HTTP 200 via direct curl.
- `npm start` is not the correct production command with `output: standalone`; Next.js emitted that warning. The Docker image already uses `node server.js`, which is correct.
- Docker Compose runtime: BLOCKED because the Docker Desktop Linux daemon is stopped.
- Local Ollama (`localhost:11434`) and LibreTranslate (`localhost:5000`): unavailable/time out.
- Public LibreTranslate demo attempt: BLOCKED by DNS resolution in the execution environment.
- Therefore a real external translation-provider run is **not verified**, and the P0-to-P1 gate remains closed. No P1 work was started.

## Final regression run

- `python -m ruff check app tests migrations` — PASS.
- `python -m pytest -q --basetemp D:\amine\projects\docTranslator\.pytest-final` — PASS: 14 passed, 57 dependency/deprecation warnings. This includes real PyMuPDF analysis of a generated native PDF, persistence of every detected line, searchable fitting export, and overflow source preservation.
- `npm test` — PASS (`tsc --noEmit`).
- `npm run build` — PASS; all four routes generated.
- `docker compose config --quiet` — PASS.
- `git diff --check` — PASS; only Git line-ending conversion notices were emitted.

## Dependency vulnerability checks

- `npm audit --omit=dev` — PASS: found 0 vulnerabilities.
- `python -m pip_audit -r requirements.txt` — BLOCKED: `pip_audit` is not installed in the available Python 3.14 environment. No clean Python vulnerability result is claimed.
