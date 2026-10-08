from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass(frozen=True)
class Comment:
    external_id: str
    text: str
    created_at: Optional[str] = None


@dataclass
class Post:
    source: str                     
    external_id: str
    topic: str
    text: str
    permalink: Optional[str] = None
    created_at: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    like_count: Optional[int] = None
    comments_count: Optional[int] = None
    comments: list[Comment] = field(default_factory=list)

    def to_document(self) -> dict:
        return asdict(self)
