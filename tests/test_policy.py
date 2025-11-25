from pocket_ai.core.policy_engine import policy_engine


def test_offline_blocks_cloud():
    policy_engine.refresh()
    assert policy_engine.can_use_cloud("chat_completion") is False


def test_secret_capability_requires_secret(monkeypatch):
    monkeypatch.setenv("TODOIST_TOKEN", "demo")
    assert policy_engine.can_use_capability("secrets:todoist_token", "todoist_tasks") is True
    monkeypatch.delenv("TODOIST_TOKEN")
    assert policy_engine.can_use_capability("secrets:todoist_token", "todoist_tasks") is False

