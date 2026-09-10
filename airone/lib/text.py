import unicodedata


def normalize_search_text(value: str) -> str:
    """Normalize text for case- and width-insensitive search."""
    return unicodedata.normalize("NFKC", value).casefold()
