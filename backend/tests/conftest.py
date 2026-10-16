"""Every test gets its own SQLite DB and media dir under a temp DATA_DIR."""
import os
import shutil
import tempfile

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="ah_test_"))  # must precede app.config import

import pytest  # noqa: E402

from app import db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    d = db.settings.data_dir
    for f in d.glob("apna.db*"):
        f.unlink()
    shutil.rmtree(d / "media", ignore_errors=True)
    db.init_db()
    yield
