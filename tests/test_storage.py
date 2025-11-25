from pocket_ai.core import config as config_module
from pocket_ai.core.storage import DataLifecycleManager


def test_storage_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("POCKET_STORAGE_PATH", str(tmp_path))
    config_module._config_instance = None
    config_module.load_config()

    mgr = DataLifecycleManager()
    mgr.store("preferences", "theme", {"theme": "dark"})
    stored = mgr.retrieve("preferences", "theme")
    assert stored["theme"] == "dark"

    export_key = mgr.export_user_data()
    assert export_key in mgr.list_keys("user_exports")

    # Restore default config for other tests
    config_module._config_instance = None

