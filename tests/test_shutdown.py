"""Shutdown regression: main loop exits quickly after QUIT event."""

from __future__ import annotations

import threading
import time

import pygame

from game import main as game_main


def test_main_exits_within_2s_after_quit_event() -> None:
    result: dict[str, int] = {}

    def _run_main() -> None:
        result["code"] = game_main.main()

    thread = threading.Thread(target=_run_main)
    thread.start()
    try:
        # Give `main()` time to initialize pygame/display and enter loop.
        time.sleep(1.0)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        thread.join(timeout=2.0)
        assert not thread.is_alive()
        assert result.get("code") == 0
    finally:
        # Other tests in this session still use pygame/font APIs.
        pygame.init()
