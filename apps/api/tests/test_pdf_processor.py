import fitz
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Document, DocumentElement, Page
from app.pdf_processor import analyze_pdf, export_pdf


def test_fixture_pdf_has_searchable_text(tmp_path) -> None:
    path = tmp_path / "fixture.pdf"
    pdf = fitz.open()
    page = pdf.new_page(width=300, height=200)
    page.insert_text((30, 40), "Bonjour document")
    pdf.save(path)
    opened = fitz.open(path)
    assert "Bonjour document" in opened[0].get_text()


def _export_fixture(tmp_path, translated_text: str, width: float = 220) -> tuple[str, int, int]:
    source = tmp_path / "source.pdf"
    destination = tmp_path / "translated.pdf"
    pdf = fitz.open()
    pdf_page = pdf.new_page(width=300, height=200)
    pdf_page.insert_text((30, 40), "Original source text", fontsize=11)
    pdf.save(source)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        document = Document(
            filename="source.pdf",
            mime_type="application/pdf",
            size_bytes=source.stat().st_size,
            source_path=str(source),
            page_count=1,
            source_language="en",
            target_language="fr",
        )
        page = Page(document_id=document.id, page_index=0, width=300, height=200)
        document.pages.append(page)
        page.elements.append(DocumentElement(
            bounding_box={"x": 29, "y": 28, "width": width, "height": 16},
            original_text="Original source text",
            translated_text=translated_text,
            translation_status="translated",
            style_json={"font_size": 11},
        ))
        session.add(document)
        session.commit()
        rendered, overflow = export_pdf(session, document, destination)

    opened = fitz.open(destination)
    return opened[0].get_text(), rendered, overflow


def test_export_preserves_source_text_when_translation_overflows(tmp_path) -> None:
    text, rendered, overflow = _export_fixture(tmp_path, "translation " * 100, width=40)
    assert overflow == 1
    assert rendered == 0
    assert "Original source text" in text


def test_export_replaces_source_text_when_translation_fits(tmp_path) -> None:
    text, rendered, overflow = _export_fixture(tmp_path, "Texte traduit")
    assert overflow == 0
    assert rendered == 1
    assert "Texte traduit" in text
    assert "Original source text" not in text

def test_analysis_persists_every_native_text_line(tmp_path) -> None:
    source = tmp_path / "native.pdf"
    pdf = fitz.open()
    pdf_page = pdf.new_page(width=300, height=200)
    pdf_page.insert_text((30, 40), "First detected line")
    pdf_page.insert_text((30, 70), "Second detected line")
    pdf.save(source)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        document = Document(
            filename="native.pdf",
            mime_type="application/pdf",
            size_bytes=source.stat().st_size,
            source_path=str(source),
        )
        session.add(document)
        session.commit()

        analyze_pdf(session, document, lambda *args: None)
        elements = list(session.scalars(
            select(DocumentElement).join(Page).where(Page.document_id == document.id)
        ))

        assert document.page_count == 1
        assert [element.original_text for element in elements] == [
            "First detected line",
            "Second detected line",
        ]
        assert all(element.metadata_json["extraction_method"] == "native" for element in elements)
