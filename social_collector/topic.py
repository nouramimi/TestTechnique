import re
import unicodedata


def to_hashtag(topic: str) -> str:
    """'Jacques Chirac' -> 'jacqueschirac' (sans accents, espaces ni ponctuation)."""
    normalized = unicodedata.normalize("NFKD", topic)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    tag = re.sub(r"[^0-9a-zA-Z]", "", ascii_only).lower()
    if not tag:
        raise ValueError(f"Impossible de construire un hashtag à partir de : {topic!r}")
    return tag
