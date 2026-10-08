import mongomock
import pytest
from mongomock.gridfs import enable_gridfs_integration

enable_gridfs_integration()


@pytest.fixture
def db():
    return mongomock.MongoClient()["test"]
