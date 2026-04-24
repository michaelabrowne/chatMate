from __future__ import annotations

import subprocess
import sys
import time
import urllib.request

_SERVERS: list[tuple[str, int, str]] = [
    ("weather",    8771, "chatmate.services.agents.servers.weather_server"),
    ("currency",   8772, "chatmate.services.agents.servers.currency_server"),
    ("things_to_do", 8773, "chatmate.services.agents.servers.things_to_do_server"),
]


class AgentServerManager:
    def __init__(self) -> None:
        self._processes: list[subprocess.Popen] = []

    def start_all(self) -> None:
        for _name, _port, module in _SERVERS:
            proc = subprocess.Popen(
                [sys.executable, "-m", module],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._processes.append(proc)
        self._wait_until_ready()

    def stop_all(self) -> None:
        for proc in self._processes:
            proc.terminate()
        self._processes.clear()

    def _wait_until_ready(self, timeout: float = 15.0) -> None:
        pending = [(name, port) for name, port, _ in _SERVERS]
        deadline = time.monotonic() + timeout
        while pending and time.monotonic() < deadline:
            still_pending = []
            for name, port in pending:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
                except Exception:
                    still_pending.append((name, port))
            pending = still_pending
            if pending:
                time.sleep(0.2)
