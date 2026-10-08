from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

import requests

from .connectors.base import SocialConnector
from .models import Post
from .storage import MongoRepository

log = logging.getLogger(__name__)
MAX_IMAGE_BYTES = 10 * 1024 * 1024

ImageFetcher = Callable[[str], Optional[tuple[bytes, str]]]


def fetch_image(url: str, timeout: float = 15.0) -> Optional[tuple[bytes, str]]:
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Image non téléchargée : %s", type(exc).__name__)
        return None
    if len(resp.content) > MAX_IMAGE_BYTES:
        log.warning("Image ignorée (trop volumineuse)")
        return None
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


@dataclass
class Stats:
    new: int = 0
    updated: int = 0
    images: int = 0
    comments: int = 0


class Collector:
    def __init__(self, connector: SocialConnector, repository: MongoRepository,
                 image_fetcher: ImageFetcher = fetch_image):
        self._connector = connector
        self._repo = repository
        self._fetch_image = image_fetcher

    def run(self, topic: str, limit: int) -> Stats:
        stats = Stats()
        for post in self._connector.collect(topic, limit):
            image, content_type = self._image_for(post)
            is_new = self._repo.save(post, image, content_type)
            stats.new += is_new
            stats.updated += not is_new
            stats.images += image is not None
            stats.comments += len(post.comments)
        log.info("Terminé : %s", stats)
        return stats

    def _image_for(self, post: Post) -> tuple[Optional[bytes], Optional[str]]:
        if post.media_type != "IMAGE" or not post.media_url or self._repo.has_image(post):
            return None, None
        fetched = self._fetch_image(post.media_url)
        return fetched if fetched else (None, None)
