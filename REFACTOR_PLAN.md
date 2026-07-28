# Minimal Refactor Plan

Preserve the current web/API/worker/database/storage topology and relational
document-element model.

1. Introduce small protocols: `PdfTranslationEngine`, `OcrEngine`,
   `TranslationProvider`, `DocumentProcessor`, `ExportEngine`, and
   `StorageProvider`.
2. Wrap the existing PyMuPDF functions in the first PDF engine adapter without
   changing API contracts.
3. Split analysis, translation, completion calculation, and export orchestration
   into services callable by both workers and tests.
4. Add OCR as a worker-only adapter. Never import an OCR engine in frontend code.
5. Centralize completion calculation from elements plus unresolved review issues.
6. Add an authenticated storage download service that validates ownership/path
   and file state.
7. Add provider policy (allowed schemes/hosts, egress documentation) beside the
   existing adapters.

This sequencing avoids a framework rewrite and makes PDFMathTranslate, OCRmyPDF,
PaddleOCR, S3, or other engines replaceable behind boundaries.
