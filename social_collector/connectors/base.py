from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from ..models import Post


class SocialConnector(ABC):
    """Contrat commun : la source de données peut changer sans toucher au reste.

    Utile ici car l'accès aux posts publics par sujet dépend des permissions Meta :
    on peut brancher Instagram (hashtag), la Meta Content Library, ou un jeu de données local.
    """

    name: str

    @abstractmethod
    def collect(self, topic: str, limit: int) -> Iterator[Post]:
        """Produit au plus `limit` posts liés au sujet, commentaires inclus."""
