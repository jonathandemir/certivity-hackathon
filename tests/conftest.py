import json

import pytest

from certreq import paths

needs_package = pytest.mark.skipif(not paths.INDEX_PATH.exists(), reason="Teilnehmerpaket fehlt (scripts/setup)")
DEV_CASE = paths.CASES_DIR / "dev-rear-lamp"


@pytest.fixture(scope="session")
def dev_expected():
    return json.loads((DEV_CASE / "expected.json").read_text(encoding="utf-8"))["requirements"]
