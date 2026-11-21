import json
from importlib.metadata import version

from depencity import build, summarize, to_json


def test_outputs_report_installed_version():
    scopes = build("x = 1")
    expected = version("depencity")
    assert json.loads(to_json(scopes))["version"] == expected
    assert summarize(scopes)["version"] == expected
