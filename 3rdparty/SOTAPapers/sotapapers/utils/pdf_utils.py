import fitz
from typing import Optional
from pathlib import Path

def get_full_text_from_pdf(file_path: Path) -> Optional[str]:
    with fitz.open(file_path) as doc:
        full_text = ''
        for page in doc:
            text = page.get_text()
            full_text += text
        return full_text
    return None