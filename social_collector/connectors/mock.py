from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from ..models import Comment, Post
from .base import SocialConnector


class MockConnector(SocialConnector):
    """Source locale (JSON) : permet de développer et tester sans accès Meta."""

    name = "mock"

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def collect(self, topic: str, limit: int) -> Iterator[Post]:
        records = json.loads(self._path.read_text(encoding="utf-8"))
        for record in records[:limit]:
            comments = [Comment(**c) for c in record.pop("comments", [])]
            yield Post(source=self.name, topic=topic, comments=comments, **record)
