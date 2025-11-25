import os
import subprocess
import sys
from pathlib import Path

from pocket_ai.core import config as config_module
from pocket_ai.core.storage import DataLifecycleManager


def test_export_cli_decrypt(tmp_path, monkeypatch):
    monkeypatch.setenv("POCKET_STORAGE_PATH", str(tmp_path))
    config_module._config_instance = None
    config_module.load_config()

    manager = DataLifecycleManager()
    manager.store("preferences", "theme", {"theme": "dark"})
    export_key = manager.export_user_data()

    output_path = tmp_path / "export.zip"
    env = os.environ.copy()
    env["POCKET_STORAGE_PATH"] = str(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pocket_ai.cli.export",
            "decrypt",
            export_key,
            "--out",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()

