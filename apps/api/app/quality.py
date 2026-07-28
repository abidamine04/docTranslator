from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .models import DocumentElement, Page, ReviewIssue

SUCCESS_STATUSES = {"translated", "manually_edited", "reviewed"}
IMAGE_ISSUE_TYPES = {"unresolved_image", "unresolved_image_text", "image_text"}


def completion_report(session: Session, document_id: str) -> dict:
    pages = list(session.scalars(
        select(Page).options(selectinload(Page.elements)).where(Page.document_id == document_id)
    ))
    elements: list[DocumentElement] = [element for page in pages for element in page.elements]
    issues = list(session.scalars(select(ReviewIssue).where(
        ReviewIssue.document_id == document_id,
        ReviewIssue.resolved.is_(False),
    )))

    total = len(elements)
    ocr_elements = [
        element for element in elements if element.metadata_json.get("extraction_method") == "ocr"
    ]
    successful = sum(element.translation_status in SUCCESS_STATUSES for element in elements)
    failed = sum(element.translation_status == "failed" for element in elements)
    unchanged = sum(element.translation_status == "unchanged" for element in elements)
    pending = total - successful - failed - unchanged
    low_ocr = sum(
        element.translation_status == "low_confidence"
        or element.confidence < get_settings().ocr_confidence_threshold
        for element in ocr_elements
    )
    scanned_pages = [page for page in pages if page.page_type == "scanned"]
    scanned_with_ocr = {
        element.page_id for element in ocr_elements if any(page.id == element.page_id for page in scanned_pages)
    }
    overflow = sum(issue.issue_type == "layout_overflow" for issue in issues)
    unresolved_images = sum(issue.issue_type in IMAGE_ISSUE_TYPES for issue in issues)

    translation_coverage = round(successful / total * 100, 1) if total else 0.0
    ocr_coverage = (
        round(len(scanned_with_ocr) / len(scanned_pages) * 100, 1) if scanned_pages else 100.0
    )

    has_warnings = bool(issues or low_ocr or unchanged)
    if total > 0 and failed == total:
        completion_status = "failed"
    elif successful > 0 and (failed or unchanged or pending):
        completion_status = "partially_translated"
    elif failed or unchanged or pending or total == 0:
        completion_status = "review_required"
    elif successful == total and has_warnings:
        completion_status = "complete_with_warnings"
    else:
        completion_status = "complete"

    return {
        "total_pages": len(pages),
        "total_text_blocks": total,
        "native_text_blocks": total - len(ocr_elements),
        "ocr_text_blocks": len(ocr_elements),
        "successfully_translated_blocks": successful,
        "failed_blocks": failed,
        "unchanged_blocks": unchanged,
        "pending_blocks": pending,
        "low_confidence_ocr_regions": low_ocr,
        "overflow_warnings": overflow,
        "unresolved_image_regions": unresolved_images,
        "translation_coverage_percentage": translation_coverage,
        "ocr_coverage_percentage": ocr_coverage,
        "completion_status": completion_status,
        "formulas": {
            "translation_coverage_percentage": (
                "successfully_translated_blocks / total_text_blocks * 100"
            ),
            "ocr_coverage_percentage": "scanned_pages_with_ocr_blocks / scanned_pages * 100",
        },
        # Backward-compatible fields consumed by the current frontend.
        "text_detected": total,
        "successfully_translated": successful,
        "failed": failed,
        "untranslated": pending + unchanged,
        "low_confidence": low_ocr,
        "translation_coverage": translation_coverage,
        "fully_translated": completion_status == "complete",
    }
