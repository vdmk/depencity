import json

import pytest

from depencity._profile.summary import summarize_document

from .utils import read_fixture


@pytest.mark.parametrize(
    ("case", "metrics", "filename"),
    (
        ("edge_cases", None, "expected_output.summary.json"),
        (
            "edge_cases",
            ["graph.paths.expressions.count"],
            "expected_output.filtered.summary.json",
        ),
        ("distribution_key_collisions", None, "expected_output.summary.json"),
        ("pooled_p95_fallback", None, "expected_output.summary.json"),
    ),
)
def test_summary_fixture_snapshots(
    case: str, metrics: list[str] | None, filename: str
):
    prefix = f"summary/{case}"
    document = json.loads(read_fixture(f"{prefix}/input.json"))

    assert summarize_document(document, metrics=metrics) == json.loads(
        read_fixture(f"{prefix}/{filename}")
    )
