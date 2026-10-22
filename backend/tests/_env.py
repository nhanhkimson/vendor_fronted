"""Set the test database before the application settings are loaded."""

import os
import tempfile
from pathlib import Path

MEDIA_ROOT = tempfile.mkdtemp(prefix="bazaar-test-media-")
os.environ["DATABASE_URL"] = "postgresql+psycopg://bazaar_app:bazaar_app@127.0.0.1:5432/bazaar_test"
os.environ["OWNER_DATABASE_URL"] = "postgresql+psycopg://bazaar_owner:bazaar_owner@127.0.0.1:5432/bazaar_test"
os.environ["STRICT_AUDIT"] = "true"
os.environ["RUN_MAINTENANCE"] = "false"
os.environ["MEDIA_DIR"] = str(Path(MEDIA_ROOT) / "media")
os.environ["PRIVATE_DIR"] = str(Path(MEDIA_ROOT) / "private")
