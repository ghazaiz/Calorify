import os

import pytest

from app.nutrition.service import search_food


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Live nutrition providers require RUN_INTEGRATION_TESTS=1"
)
def test_search_food():
    result = search_food("apple")

    assert result is not None
    assert "source" in result
    assert "food" in result