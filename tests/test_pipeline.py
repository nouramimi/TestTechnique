from social_collector.connectors import MockConnector
from social_collector.models import Post
from social_collector.pipeline import Collector
from social_collector.storage import MongoRepository

SAMPLE = "sample_data/chirac_sample.json"


def test_run_is_idempotent(db):
    repo = MongoRepository(db)
    collector = Collector(MockConnector(SAMPLE), repo)
    first = collector.run("Jacques Chirac", 10)
    second = collector.run("Jacques Chirac", 10)
    assert (first.new, first.comments) == (2, 2)
    assert (second.new, second.updated) == (0, 2)
    assert db["posts"].count_documents({}) == 2


def test_comments_stored_with_post(db):
    repo = MongoRepository(db)
    Collector(MockConnector(SAMPLE), repo).run("Jacques Chirac", 10)
    doc = db["posts"].find_one({"external_id": "mock_1"})
    assert len(doc["comments"]) == 2 and "collected_at" in doc


def test_image_downloaded_once(db):
    calls = []
    def fetcher(url):
        calls.append(url)
        return b"\x89PNG", "image/png"
    class One:
        name = "t"
        def collect(self, topic, limit):
            yield Post("t", "p1", topic, "txt", media_type="IMAGE", media_url="http://x/i.png")
    collector = Collector(One(), MongoRepository(db), image_fetcher=fetcher)
    first = collector.run("t", 1)
    collector.run("t", 1)
    assert first.images == 1 and len(calls) == 1
    assert db["fs.files"].count_documents({}) == 1
