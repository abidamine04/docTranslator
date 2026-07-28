import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Document, DocumentElement, Page, ProviderConfiguration
from app.pdf_processor import translate_document


class BatchFailingUnchangedProvider:
    def __init__(self, config) -> None:
        self.config = config

    async def translate(self, texts, source, target, tone):
        if len(texts) > 1:
            raise RuntimeError("batch failure")
        return texts


def test_individual_retry_records_unchanged_output(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        document = Document(filename="test.pdf", mime_type="application/pdf", size_bytes=1, source_path="test.pdf")
        page = Page(page_index=0, width=100, height=100)
        document.pages.append(page)
        for text in ["Name", "https://example.com"]:
            page.elements.append(DocumentElement(
                bounding_box={}, original_text=text, translation_status="detected"
            ))
        provider = ProviderConfiguration(
            name="test",
            provider_type="openai_compatible",
            base_url="http://provider.invalid",
            model="test",
            batch_size=2,
        )
        session.add_all([document, provider])
        session.commit()
        monkeypatch.setattr("app.pdf_processor.TranslationProvider", BatchFailingUnchangedProvider)

        asyncio.run(translate_document(
            session,
            document,
            provider,
            "fr",
            "en",
            "neutral",
            lambda *args: None,
            lambda: False,
        ))

        assert [element.translation_status for element in page.elements] == ["unchanged", "unchanged"]
