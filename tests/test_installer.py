from __future__ import annotations

import os

from alfred_tts.config import load_state, update_state
from alfred_tts.installer import is_kokoro_installing


def test_is_kokoro_installing_dead_pid() -> None:
    update_state(kokoro={"install_status": "installing", "install_pid": 999999})
    assert is_kokoro_installing() is False
    state = load_state()
    assert state.get("kokoro", {}).get("install_status") == "error"


def test_is_kokoro_installing_active_pid() -> None:
    update_state(kokoro={"install_status": "installing", "install_pid": os.getpid()})
    assert is_kokoro_installing() is True
