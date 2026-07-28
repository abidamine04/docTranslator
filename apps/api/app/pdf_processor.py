import asyncio
from pathlib import Path

import fitz
from langdetect import DetectorFactory, LangDetectException, detect
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Document, DocumentElement, ElementStatus, Page, ProviderConfiguration, ReviewIssue
from .providers import TranslationProvider

DetectorFactory.seed = 0


def analyze_pdf(session: Session, document: Document, progress) -> None:
    pdf = fitz.open(document.source_path)
    if pdf.needs_pass:
        raise ValueError("Password-protected PDF")
    if len(pdf) > get_settings().max_page_count:
        raise ValueError(f"PDF exceeds the {get_settings().max_page_count} page limit")
    session.execute(delete(Page).where(Page.document_id == document.id))
    document.page_count = len(pdf)
    all_text: list[str] = []
    for index, pdf_page in enumerate(pdf):
        progress("detecting_text", index + 1, len(pdf), 10 + (index + 1) / max(len(pdf), 1) * 45)
        page = Page(
            document_id=document.id,
            page_index=index,
            width=pdf_page.rect.width,
            height=pdf_page.rect.height,
            page_type="digital",
        )
        session.add(page)
        session.flush()
        blocks = pdf_page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)["blocks"]
        text_count = 0
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(span.get("text", "") for span in spans).strip()
                if not text:
                    continue
                text_count += len(text)
                first = spans[0]
                x0, y0, x1, y1 = line["bbox"]
                session.add(DocumentElement(
                    page_id=page.id,
                    bounding_box={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0},
                    original_text=text,
                    confidence=1.0,
                    translation_status=ElementStatus.detected.value,
                    style_json={
                        "font_family": first.get("font"),
                        "font_size": first.get("size", 11),
                        "color": first.get("color", 0),
                    },
                ))
                all_text.append(text)
        if text_count < 20:
            page.page_type = "scanned"
            session.add(ReviewIssue(
                document_id=document.id,
                issue_type="ocr_required",
                message=f"Page {index + 1} contains little native text and requires OCR.",
            ))
        session.commit()
    progress("detecting_source_language", len(pdf), len(pdf), 60)
    sample = " ".join(all_text)[:10000]
    try:
        document.source_language = detect(sample) if sample else "unknown"
    except LangDetectException:
        document.source_language = "unknown"
    document.status = "analyzed_with_warnings" if any(p.page_type == "scanned" for p in document.pages) else "analyzed"
    session.commit()


async def translate_document(
    session: Session,
    document: Document,
    provider_config: ProviderConfiguration,
    target: str,
    source: str,
    tone: str,
    progress,
    cancelled,
) -> None:
    provider = TranslationProvider(provider_config)
    elements = list(
        session.scalars(
            select(DocumentElement)
            .join(Page)
            .where(Page.document_id == document.id)
            .order_by(Page.page_index, DocumentElement.id)
        )
    )
    document.target_language = target
    total = len(elements)
    batch_size = provider_config.batch_size
    for start in range(0, total, batch_size):
        if cancelled():
            raise asyncio.CancelledError()
        batch = elements[start:start + batch_size]
        texts = [element.original_text for element in batch]
        try:
            translated = await provider.translate(texts, source, target, tone)
            for element, value in zip(batch, translated, strict=True):
                element.translated_text = value
                element.source_language = source
                element.target_language = target
                element.translation_status = (
                    ElementStatus.unchanged.value if value.strip() == element.original_text.strip()
                    else ElementStatus.translated.value
                )
        except Exception:
            for element in batch:
                try:
                    result = await provider.translate([element.original_text], source, target, tone)
                    element.translated_text = result[0]
                    element.source_language = source
                    element.target_language = target
                    element.translation_status = ElementStatus.translated.value
                except Exception as exc:
                    element.translation_status = ElementStatus.failed.value
                    element.metadata_json = {**element.metadata_json, "translation_error": str(exc)}
        session.commit()
        done = min(start + len(batch), total)
        progress("translating", done, total, 15 + done / max(total, 1) * 70)
    document.status = "translated"
    session.commit()


def export_pdf(session: Session, document: Document, destination: Path) -> tuple[int, int]:
    pdf = fitz.open(document.source_path)
    elements = list(session.scalars(
        select(DocumentElement).join(Page).where(Page.document_id == document.id)
    ))
    pages_by_id = {page.id: page for page in document.pages}
    overflow = 0
    rendered = 0
    for element in elements:
        if not element.translated_text or element.translation_status == ElementStatus.failed.value:
            continue
        page_model = pages_by_id[element.page_id]
        page = pdf[page_model.page_index]
        box = element.bounding_box
        rect = fitz.Rect(box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"])
        page.add_redact_annot(rect, fill=(1, 1, 1))
    for page in pdf:
        page.apply_redactions()
    for element in elements:
        if not element.translated_text or element.translation_status == ElementStatus.failed.value:
            continue
        page_model = pages_by_id[element.page_id]
        page = pdf[page_model.page_index]
        box = element.bounding_box
        rect = fitz.Rect(box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"])
        original_size = float(element.style_json.get("font_size", 11))
        font_size = original_size
        inserted = -1.0
        while font_size >= max(6, original_size * 0.65):
            inserted = page.insert_textbox(rect, element.translated_text, fontsize=font_size, fontname="helv")
            if inserted >= 0:
                break
            font_size -= 0.5
        if inserted < 0:
            overflow += 1
            session.add(ReviewIssue(
                document_id=document.id,
                element_id=element.id,
                issue_type="layout_overflow",
                message="Translated text does not fit its original bounding box.",
            ))
        else:
            rendered += 1
    session.commit()
    metadata = {
        **pdf.metadata,
        "subject": f"Translated {document.source_language} to {document.target_language}",
    }
    pdf.set_metadata(metadata)
    pdf.save(destination, garbage=4, deflate=True)
    return rendered, overflow
