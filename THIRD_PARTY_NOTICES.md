# Third-Party Notices

This project depends on third-party open-source packages listed in
`apps/api/requirements.txt`, `apps/api/requirements-dev.txt`, and
`apps/web/package.json`. Their copyright notices and license texts remain the
property of their respective authors. Distributors must reproduce all notices
required by the exact dependency versions they ship.

## Material licensing note

PyMuPDF/MuPDF is offered under GNU AGPL terms or a commercial Artifex license.
Because DocTranslator imports and distributes PyMuPDF in its API/worker image,
DocTranslator is now distributed under AGPL-3.0 in `LICENSE`, satisfying the
compatible open-source licensing path. A distributor choosing different terms must
obtain an applicable commercial PyMuPDF license and separate permission from
DocTranslator copyright holders.

See [PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/faq/index.html).

## Direct runtime dependencies

Notices should be generated from the resolved lock/install artifacts for every
release. Important direct projects include FastAPI, Uvicorn, SQLAlchemy, Alembic,
Psycopg, Pydantic Settings, PyMuPDF, HTTPX, Cryptography, Dramatiq, libmagic,
langdetect, Next.js, React, Framer Motion, Lucide, PDF.js, and react-pdf.

Provider services and model weights are not redistributed by this repository.
LibreTranslate is AGPL-3.0; Ollama repository code is MIT; individual Ollama/Argos
models can have separate terms that operators must review.
