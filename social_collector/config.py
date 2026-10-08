from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str
    graph_api_version: str
    ig_user_id: str | None
    ig_access_token: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db=os.getenv("MONGO_DB", "abusive_language"),
            graph_api_version=os.getenv("GRAPH_API_VERSION", "v25.0"),
            ig_user_id=os.getenv("IG_USER_ID"),
            ig_access_token=os.getenv("IG_ACCESS_TOKEN"),
        )

    def require_instagram(self) -> tuple[str, str]:
        if not self.ig_user_id or not self.ig_access_token:
            raise ValueError("IG_USER_ID et IG_ACCESS_TOKEN sont requis (voir .env.example).")
        return self.ig_user_id, self.ig_access_token
