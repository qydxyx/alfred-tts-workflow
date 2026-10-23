from __future__ import annotations

import json
from pathlib import Path

from alfred_tts.cli import main
from alfred_tts.models import Action
from alfred_tts.payload import decode_payload


def test_config_filter_has_defaults_and_cleanup(monkeypatch, capsys) -> None:
    monkeypatch.setattr("alfred_tts.cli.which_uv", lambda: Path("/usr/bin/uv"))
    monkeypatch.setattr("alfred_tts.cli.core_venv_ready", lambda: True)
    monkeypatch.setattr("sys.argv", ["alfred-tts", "config-filter", ""])
    main()
    data = json.loads(capsys.readouterr().out)
    actions = [decode_payload(item["arg"])["action"] for item in data["items"]]
    assert Action.SET_DEFAULT in actions
    assert Action.SET_VOICE in actions
    assert Action.INSTALL_KOKORO in actions
    assert Action.REMOVE_KOKORO in actions
    assert Action.CLEAR_CACHE in actions
