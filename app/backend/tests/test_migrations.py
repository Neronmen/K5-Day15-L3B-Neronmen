"""Migration Alembic phải khớp app.models: sửa models mà quên tạo migration thì test này hỏng."""
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": db_url}
    return subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env, capture_output=True, text=True)


def test_migrations_upgrade_and_match_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    up = _alembic(url, "upgrade", "head")
    assert up.returncode == 0, up.stderr
    check = _alembic(url, "check")
    assert check.returncode == 0, check.stdout + check.stderr
    down = _alembic(url, "downgrade", "base")
    assert down.returncode == 0, down.stderr
