#!/usr/bin/env python3
"""Entrypoint: chạy `python main.py` từ thư mục gốc repo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from score_lookup import ui  # noqa: E402
from score_lookup.cli import main  # noqa: E402

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        ui.warn("Đã dừng bởi người dùng.")
