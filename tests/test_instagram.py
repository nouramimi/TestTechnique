import pytest
import responses
from social_collector.connectors import InstagramHashtagConnector
from social_collector.connectors import graph_client
from social_collector.connectors.graph_client import GraphClient
from social_collector.errors import AuthError, ConnectorError

BASE = "https://graph.facebook.com/v25.0"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(graph_client.time, "sleep", lambda s: None)


def make():
    return InstagramHashtagConnector(GraphClient("TOKEN", "v25.0"), "IGUSER")


@responses.activate
def test_collect_with_pagination_and_comments():
    responses.get(f"{BASE}/ig_hashtag_search", json={"data": [{"id": "H1"}]})
    responses.get(f"{BASE}/H1/recent_media", json={
        "data": [{"id": "m1", "caption": "a", "media_type": "IMAGE", "media_url": "http://x/1.jpg"}],
        "paging": {"next": f"{BASE}/H1/recent_media?page=2"}})
    responses.get(f"{BASE}/H1/recent_media", json={"data": [{"id": "m2", "caption": "b"}]})
    responses.get(f"{BASE}/m1/comments", json={"data": [{"id": "c1", "text": "salut"}]})
    responses.get(f"{BASE}/m2/comments", json={"error": {"code": 100, "message": "unsupported"}}, status=400)
    posts = list(make().collect("Jacques Chirac", limit=10))
    assert [p.external_id for p in posts] == ["m1", "m2"]
    assert posts[0].comments[0].text == "salut"
    assert posts[1].comments == []          # dégradation propre


@responses.activate
def test_limit_is_respected():
    responses.get(f"{BASE}/ig_hashtag_search", json={"data": [{"id": "H1"}]})
    responses.get(f"{BASE}/H1/recent_media", json={"data": [{"id": f"m{i}"} for i in range(5)]})
    responses.get(f"{BASE}/m0/comments", json={"data": []})
    assert len(list(make().collect("x", limit=1))) == 1


@responses.activate
def test_unknown_hashtag_raises():
    responses.get(f"{BASE}/ig_hashtag_search", json={"data": []})
    with pytest.raises(ConnectorError):
        list(make().collect("x", limit=1))


@responses.activate
def test_expired_token_is_auth_error():
    responses.get(f"{BASE}/ig_hashtag_search", json={"error": {"code": 190, "message": "expired"}}, status=400)
    with pytest.raises(AuthError):
        list(make().collect("x", limit=1))


@responses.activate
def test_retry_on_server_error():
    responses.get(f"{BASE}/ig_hashtag_search", status=500)
    responses.get(f"{BASE}/ig_hashtag_search", json={"data": [{"id": "H1"}]})
    responses.get(f"{BASE}/H1/recent_media", json={"data": []})
    assert list(make().collect("x", limit=1)) == []


@responses.activate
def test_missing_comment_permission_does_not_stop_collection():
    responses.get(f"{BASE}/ig_hashtag_search", json={"data": [{"id": "H1"}]})
    responses.get(f"{BASE}/H1/recent_media", json={"data": [{"id": "m1"}, {"id": "m2"}]})
    responses.get(f"{BASE}/m1/comments", json={"error": {"code": 10, "message": "no permission"}}, status=403)
    responses.get(f"{BASE}/m2/comments", json={"data": [{"id": "c1", "text": "ok"}]})
    posts = list(make().collect("x", limit=10))
    assert [len(p.comments) for p in posts] == [0, 1]


@responses.activate
def test_expired_token_during_comments_stops_collection():
    responses.get(f"{BASE}/ig_hashtag_search", json={"data": [{"id": "H1"}]})
    responses.get(f"{BASE}/H1/recent_media", json={"data": [{"id": "m1"}]})
    responses.get(f"{BASE}/m1/comments", json={"error": {"code": 190, "message": "expired"}}, status=400)
    with pytest.raises(AuthError):
        list(make().collect("x", limit=10))
