from __future__ import annotations

from pathlib import Path


def read_text(path: Path | str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".txt":
        return p.read_text(encoding="utf-8")
    if ext == ".docx":
        from docx import Document

        return "\n".join(para.text for para in Document(str(p)).paragraphs)
    raise ValueError(f"unsupported file type: {ext} (v1 supports .txt, .docx)")
