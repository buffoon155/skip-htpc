#!/usr/bin/env python3
"""Stand-in for branded Chrome's remote-debugging pipe."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    if "--version" in sys.argv:
        sys.stdout.write("Google Chrome 142.0.0.0\n")
        return 0
    buffer = b""
    while b"\0" not in buffer:
        chunk = os.read(3, 4096)
        if not chunk:
            break
        buffer += chunk
    raw = buffer.split(b"\0", 1)[0]
    out = os.environ.get("FAKE_CHROME_REQUEST")
    if out:
        Path(out).write_bytes(raw)
    message = json.loads(raw.decode("utf-8"))
    response = {"id": message["id"], "result": {"id": "fakedevextension"}}
    os.write(4, json.dumps(response).encode("utf-8") + b"\0")
    while True:
        try:
            more = os.read(3, 4096)
        except OSError:
            return 0
        if not more:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
