from unittest.mock import patch

import pytest


@pytest.fixture(scope="module", autouse=True)
def use_snapshot_version():
    with (
        patch("depencity._graph.export.json.version", return_value="0.0.0"),
        patch("depencity._profile.summary.version", return_value="0.0.0"),
    ):
        yield
