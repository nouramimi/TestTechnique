import pytest
from social_collector.topic import to_hashtag


def test_accents_spaces_and_case():
    assert to_hashtag("Décès de Jacques Chirac") == "decesdejacqueschirac"


def test_empty_topic_raises():
    with pytest.raises(ValueError):
        to_hashtag("!!!")
