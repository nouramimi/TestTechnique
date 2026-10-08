from __future__ import annotations

import argparse
import logging

from pymongo import MongoClient

from .config import Settings
from .connectors import InstagramHashtagConnector, MockConnector
from .connectors.graph_client import GraphClient
from .pipeline import Collector
from .storage import MongoRepository


def build_connector(args: argparse.Namespace, settings: Settings):
    if args.source == "mock":
        return MockConnector(args.mock_file)
    user_id, token = settings.require_instagram()
    return InstagramHashtagConnector(GraphClient(token, settings.graph_api_version), user_id, args.hashtag)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collecte de posts par sujet vers MongoDB")
    parser.add_argument("--topic", required=True, help='ex. "décès de Jacques Chirac"')
    parser.add_argument("--source", choices=["instagram", "mock"], default="mock")
    parser.add_argument("--hashtag", help="hashtag explicite (sinon déduit du sujet)")
    parser.add_argument("--mock-file", default="sample_data/chirac_sample.json")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()
    repo = MongoRepository(MongoClient(settings.mongo_uri)[settings.mongo_db])
    Collector(build_connector(args, settings), repo).run(args.topic, args.limit)


if __name__ == "__main__":
    main()
