from __future__ import annotations

import logging
from typing import Iterator

from ..errors import AuthError, ConnectorError
from ..models import Comment, Post
from ..topic import to_hashtag
from .base import SocialConnector
from .graph_client import GraphClient

log = logging.getLogger(__name__)

MEDIA_FIELDS = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"
COMMENT_FIELDS = "id,text,timestamp"


class InstagramHashtagConnector(SocialConnector):
    """Posts publics récents d'un hashtag (API Graph, Instagram Public Content Access).

    Prérequis côté Meta : compte Instagram professionnel lié à une Page Facebook,
    app approuvée en App Review (instagram_basic + feature Instagram Public Content Access).
    Limite documentée : 30 hashtags distincts par fenêtre de 7 jours.
    """

    name = "instagram"

    def __init__(self, client: GraphClient, ig_user_id: str, hashtag: str | None = None):
        self._client = client
        self._ig_user_id = ig_user_id
        self._hashtag_override = hashtag

    def collect(self, topic: str, limit: int) -> Iterator[Post]:
        hashtag = self._hashtag_override or to_hashtag(topic)
        hashtag_id = self._hashtag_id(hashtag)
        params = {"user_id": self._ig_user_id, "fields": MEDIA_FIELDS, "limit": min(limit, 50)}
        count = 0
        for item in self._client.paginate(f"{hashtag_id}/recent_media", params):
            if count >= limit:
                return
            yield self._to_post(item, topic)
            count += 1

    def _hashtag_id(self, hashtag: str) -> str:
        data = self._client.get("ig_hashtag_search", {"user_id": self._ig_user_id, "q": hashtag})
        results = data.get("data", [])
        if not results:
            raise ConnectorError(f"Hashtag introuvable ou refusé par Meta : #{hashtag}")
        return results[0]["id"]

    def _to_post(self, item: dict, topic: str) -> Post:
        return Post(
            source=self.name,
            external_id=item["id"],
            topic=topic,
            text=item.get("caption") or "",
            permalink=item.get("permalink"),
            created_at=item.get("timestamp"),
            media_type=item.get("media_type"),
            media_url=item.get("media_url"),
            like_count=item.get("like_count"),
            comments_count=item.get("comments_count"),
            comments=self._comments(item["id"]),
        )

    def _comments(self, media_id: str) -> list[Comment]:
        """Dégradation propre : un échec sur les commentaires n'invalide pas le média.

        Seul un token invalide (AuthError) arrête la collecte ; une permission manquante
        ou une erreur sur ce média est journalisée et la liste de commentaires reste vide.
        """
        try:
            raw = self._client.paginate(f"{media_id}/comments", {"fields": COMMENT_FIELDS})
            return [Comment(c["id"], c.get("text", ""), c.get("timestamp")) for c in raw]
        except AuthError:
            raise
        except ConnectorError as exc:
            log.warning("Commentaires indisponibles pour %s : %s", media_id, exc)
            return []
