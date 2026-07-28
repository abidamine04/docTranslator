import fitz


def test_fixture_pdf_has_searchable_text(tmp_path) -> None:
    path = tmp_path / "fixture.pdf"
    pdf = fitz.open()
    page = pdf.new_page(width=300, height=200)
    page.insert_text((30, 40), "Bonjour document")
    pdf.save(path)
    opened = fitz.open(path)
    assert "Bonjour document" in opened[0].get_text()

