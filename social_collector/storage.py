from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import gridfs
from pymongo import ASCENDING
from pymongo.database import Database

from .models import Post

log = logging.getLogger(__name__)


class MongoRepository:

    def __init__(self, db: Database):
        self._posts = db["posts"]
        self._fs = gridfs.GridFS(db)
        self._posts.create_index(
            [("source", ASCENDING), ("external_id", ASCENDING)], unique=True, name="uniq_source_post"
        )
        self._posts.create_index([("topic", ASCENDING)], name="by_topic")

    def has_image(self, post: Post) -> bool:
        doc = self._posts.find_one(
            {"source": post.source, "external_id": post.external_id}, {"image_file_id": 1}
        )
        return bool(doc and doc.get("image_file_id"))

    def save(self, post: Post, image: Optional[bytes] = None, content_type: Optional[str] = None) -> bool:
        """Upsert idempotent. Retourne True si le post est nouveau."""
        update: dict = {"$set": post.to_document(), "$setOnInsert": {"collected_at": datetime.now(timezone.utc)}}
        if image:
            file_id = self._fs.put(
                image, filename=f"{post.source}_{post.external_id}", content_type=content_type
            )
            update["$set"]["image_file_id"] = file_id
        result = self._posts.update_one(
            {"source": post.source, "external_id": post.external_id}, update, upsert=True
        )
        return result.upserted_id is not None
