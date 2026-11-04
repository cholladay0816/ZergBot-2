"""Small serialization contract shared by real recorder tests."""

import json

import pytest


@pytest.fixture
def json_roundtrip():
    def check(payload):
        return json.loads(json.dumps(payload, allow_nan=False))

    return check
