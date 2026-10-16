"""Every test gets its own SQLite DB and media dir under a temp DATA_DIR."""
import os
import shutil
import tempfile
from pathlib import Path

# Always a temp dir, never setdefault: VS Code (python.terminal.useEnvFile) injects .env, so DATA_DIR=data
# may already be set, and fresh_db below would then wipe the real hub database. Must precede app.config import.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="ah_test_")
# Tests never call paid/closed APIs, whatever .env says (load_dotenv keeps values already set, even empty ones).
os.environ["CHAT_API_KEY"] = ""
os.environ["TG_AGENT"] = "template"

import pytest  # noqa: E402

from app import db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    d = db.settings.data_dir
    assert d.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), f"refusing to wipe {d}"
    for f in d.glob("apna.db*"):
        f.unlink()
    shutil.rmtree(d / "media", ignore_errors=True)
    db.init_db()
    yield
