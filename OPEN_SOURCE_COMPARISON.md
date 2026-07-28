# Open-Source Component Comparison

Research checked current upstream project pages on 2026-07-28. License conclusions
are engineering guidance, not legal advice.

| Candidate | Purpose / current state | License | Safe use and replacement scope | Risk / effort |
|---|---|---|---|---|
| PDFMathTranslate-next | Maintained PDF translation stack based on BabelDOC | AGPL-3.0 | Benchmark against it or isolate behind `PdfTranslationEngine`; could replace most PDF reconstruction | High migration; strong copyleft; would not supply this app's review UX |
| PyMuPDF | Current parser/export dependency; active | AGPL or commercial | Keep short-term for native PDF extraction/export | Existing distribution must satisfy AGPL or hold a commercial license |
| PDF.js | Mature browser PDF renderer | Apache-2.0 | Keep; it already replaces a custom viewer core | Low |
| PaddleOCR | Actively maintained multilingual OCR | Apache-2.0 | Preferred OCR adapter for multilingual/layout OCR | Medium runtime/model footprint |
| OCRmyPDF | Actively maintained searchable-PDF OCR pipeline | MPL-2.0 plus component notices | Strong preprocessing option for scanned PDFs | Medium; subprocess isolation and its dependency notices required |
| Tesseract | Mature OCR engine | Apache-2.0 | Lower-resource OCR fallback, especially through OCRmyPDF | Medium language/layout accuracy |
| OpenCV | Maintained image preprocessing/inpainting toolkit | Apache-2.0 | Use for preprocessing/inpainting primitives, not text translation | Medium; image reconstruction remains product code |
| LibreTranslate | Maintained self-hosted translation API | AGPL-3.0 | Keep as an external provider adapter | Low integration; model quality varies |
| Argos Translate | Offline translation library | MIT or CC0; model licenses vary | Optional in-process/local adapter | Medium; verify every model artifact license |
| Ollama | Local model runtime | MIT for repository code; models have separate licenses | Keep via OpenAI-compatible adapter | Low integration; model-specific license/performance risk |
| LibreOffice headless | Office conversion | MPL-2.0 with varied bundled components | Future isolated Office conversion service | Medium/high security and fidelity risk |
| python-docx | DOCX editing | MIT | Future format adapter; cannot reproduce arbitrary Word layout | Medium |
| python-pptx | PPTX editing | MIT | Future format adapter; incomplete animation/layout surface | Medium |
| openpyxl | XLSX editing | MIT | Future spreadsheet adapter; not a renderer | Medium |

Sources: [PDFMathTranslate-next](https://github.com/PDFMathTranslate/PDFMathTranslate-next),
[PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/faq/index.html),
[PDF.js](https://github.com/mozilla/pdf.js),
[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR),
[OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF),
[Tesseract](https://github.com/tesseract-ocr/tesseract),
[OpenCV](https://github.com/opencv/opencv),
[LibreTranslate](https://github.com/LibreTranslate/LibreTranslate),
[Argos Translate](https://github.com/argosopentech/argos-translate),
[Ollama](https://github.com/ollama/ollama),
[LibreOffice licenses](https://www.libreoffice.org/licenses/), and
[python-docx](https://github.com/python-openxml/python-docx).

## Recommendation

Keep PDF.js and the existing provider boundary. Keep PyMuPDF only with an explicit
AGPL-3.0 project license or a commercial PyMuPDF license. Add OCR behind an adapter,
starting with OCRmyPDF for PDF preprocessing and PaddleOCR when block geometry and
multilingual confidence are needed. Do not import PDFMathTranslate wholesale;
benchmark it and consider a separately deployed AGPL engine adapter.
