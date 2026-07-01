import pytest
from docx import Document

from muleta.parse import read_text


def test_read_txt(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello leverage", encoding="utf-8")
    assert read_text(p) == "hello leverage"


def test_read_docx(tmp_path):
    p = tmp_path / "a.docx"
    doc = Document()
    doc.add_paragraph("We must leverage synergy.")
    doc.save(p)
    assert "leverage synergy" in read_text(p)


def test_unsupported_raises(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(b"%PDF")
    with pytest.raises(ValueError):
        read_text(p)
