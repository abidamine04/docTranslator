from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Document, DocumentElement, Page, ReviewIssue
from app.quality import completion_report


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_completion_report_accounts_for_every_detected_block_and_issue() -> None:
    with _session() as session:
        document = Document(filename="mixed.pdf", mime_type="application/pdf", size_bytes=1, source_path="source.pdf")
        native_page = Page(page_index=0, width=100, height=100, page_type="digital")
        scanned_page = Page(page_index=1, width=100, height=100, page_type="scanned")
        document.pages.extend([native_page, scanned_page])
        for status in ["translated", "unchanged", "failed", "detected"]:
            native_page.elements.append(DocumentElement(
                bounding_box={},
                original_text=status,
                translation_status=status,
                metadata_json={"extraction_method": "native"},
            ))
        scanned_page.elements.append(DocumentElement(
            bounding_box={},
            original_text="ocr",
            translation_status="low_confidence",
            confidence=0.4,
            metadata_json={"extraction_method": "ocr"},
        ))
        session.add(document)
        session.flush()
        session.add_all([
            ReviewIssue(document_id=document.id, issue_type="layout_overflow", message="overflow"),
            ReviewIssue(document_id=document.id, issue_type="unresolved_image_text", message="image"),
        ])
        session.commit()

        report = completion_report(session, document.id)

        assert report["total_pages"] == 2
        assert report["total_text_blocks"] == 5
        assert report["native_text_blocks"] == 4
        assert report["ocr_text_blocks"] == 1
        assert report["successfully_translated_blocks"] == 1
        assert report["failed_blocks"] == 1
        assert report["unchanged_blocks"] == 1
        assert report["low_confidence_ocr_regions"] == 1
        assert report["overflow_warnings"] == 1
        assert report["unresolved_image_regions"] == 1
        assert report["translation_coverage_percentage"] == 20.0
        assert report["ocr_coverage_percentage"] == 100.0
        assert report["completion_status"] == "partially_translated"
        assert report["formulas"]["translation_coverage_percentage"] == (
            "successfully_translated_blocks / total_text_blocks * 100"
        )
        assert report["formulas"]["ocr_coverage_percentage"] == (
            "scanned_pages_with_ocr_blocks / scanned_pages * 100"
        )
        accounted = (
            report["successfully_translated_blocks"]
            + report["failed_blocks"]
            + report["unchanged_blocks"]
            + report["pending_blocks"]
        )
        assert accounted == report["total_text_blocks"]


def test_completion_report_is_complete_only_without_unresolved_work() -> None:
    with _session() as session:
        document = Document(filename="done.pdf", mime_type="application/pdf", size_bytes=1, source_path="source.pdf")
        page = Page(page_index=0, width=100, height=100, page_type="digital")
        document.pages.append(page)
        page.elements.append(DocumentElement(
            bounding_box={}, original_text="hello", translated_text="bonjour", translation_status="translated"
        ))
        session.add(document)
        session.commit()

        report = completion_report(session, document.id)
        assert report["completion_status"] == "complete"
        assert report["fully_translated"] is True
        assert report["translation_coverage_percentage"] == 100.0


def test_scanned_page_without_ocr_requires_review() -> None:
    with _session() as session:
        document = Document(filename="scan.pdf", mime_type="application/pdf", size_bytes=1, source_path="source.pdf")
        document.pages.append(Page(page_index=0, width=100, height=100, page_type="scanned"))
        session.add(document)
        session.commit()

        report = completion_report(session, document.id)
        assert report["completion_status"] == "review_required"
        assert report["ocr_coverage_percentage"] == 0.0
        assert report["fully_translated"] is False
