import re
from hashlib import sha256
from typing import Optional

from sotapapers.utils.string_util import remove_unicode_chars

def make_generated_id(title: str, year: Optional[int]) -> str:
    cleaned_title = remove_unicode_chars(title.lower())
    raw = f"{cleaned_title.strip()}|{year or ''}"
    return f"gen:{sha256(raw.encode()).hexdigest()[:12]}"

def make_short_id(title: str) -> str:
    return f"gen:{sha256(title.encode()).hexdigest()[:6]}"

def detect_arxiv_id_from_citation(citation: str) -> Optional[str]:
    if 'arxiv' not in citation.lower():
        return None
    
    # extract the arxiv id from the citation
    arxiv_id = re.search(r'arxiv:\d{4}\.\d{4,5}', citation.lower())
    if arxiv_id is None:
        return None
    
    return arxiv_id.group(0)