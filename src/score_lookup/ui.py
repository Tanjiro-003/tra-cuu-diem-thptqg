"""Tiện ích in ấn đẹp cho dòng lệnh: màu ANSI, banner, thanh tiến độ, bảng điểm.

Không phụ thuộc thư viện ngoài — tự tắt màu nếu output không phải là terminal
(ví dụ khi bị redirect ra file hoặc chạy trong CI).
"""

from __future__ import annotations

import shutil
import sys


class C:
    """Mã màu ANSI."""

    ENABLE = sys.stdout.isatty()

    RESET = "\033[0m" if ENABLE else ""
    BOLD = "\033[1m" if ENABLE else ""
    DIM = "\033[2m" if ENABLE else ""

    RED = "\033[91m" if ENABLE else ""
    GREEN = "\033[92m" if ENABLE else ""
    YELLOW = "\033[93m" if ENABLE else ""
    BLUE = "\033[94m" if ENABLE else ""
    MAGENTA = "\033[95m" if ENABLE else ""
    CYAN = "\033[96m" if ENABLE else ""
    WHITE = "\033[97m" if ENABLE else ""


def width(default: int = 64) -> int:
    try:
        return min(shutil.get_terminal_size().columns, 100)
    except Exception:
        return default


def banner(title: str, subtitle: str = "") -> None:
    w = width()
    print(f"{C.CYAN}{'═' * w}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{title.center(w)}{C.RESET}")
    if subtitle:
        print(f"{C.DIM}{subtitle.center(w)}{C.RESET}")
    print(f"{C.CYAN}{'═' * w}{C.RESET}")


def footer(text: str) -> None:
    w = width()
    print(f"\n{C.CYAN}{'═' * w}{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}{text.center(w)}{C.RESET}")
    print(f"{C.CYAN}{'═' * w}{C.RESET}\n")


def section(text: str) -> None:
    print(f"\n{C.BOLD}{C.BLUE}▶ {text}{C.RESET}")


def ok(text: str) -> None:
    print(f"  {C.GREEN}✔ {text}{C.RESET}")


def warn(text: str) -> None:
    print(f"  {C.YELLOW}⚠ {text}{C.RESET}")


def err(text: str) -> None:
    print(f"  {C.RED}✘ {text}{C.RESET}")


def info(text: str) -> None:
    print(f"  {C.CYAN}ℹ {text}{C.RESET}")


def step(text: str) -> None:
    print(f"  {C.MAGENTA}➤ {text}{C.RESET}")


def progress_bar(current: int, total: int, label: str = "") -> None:
    """Vẽ thanh tiến độ [███░░░] 70% (12/17) — an toàn khi dùng đa luồng
    (mỗi lần gọi in hẳn một dòng mới, tránh nhiều luồng đè dòng của nhau)."""
    bar_width = 28
    ratio = current / total if total else 0
    filled = int(bar_width * ratio)
    bar = "█" * filled + "░" * (bar_width - filled)
    pct = int(ratio * 100)
    print(f"  {C.CYAN}[{bar}]{C.RESET} {pct:3d}%  ({current}/{total}) {label}")


def score_table(parsed: dict, sbd: str) -> None:
    """In bảng điểm gọn đẹp cho một thí sinh."""
    w = 40
    print(f"\n  {C.BOLD}{C.WHITE}┌{'─' * w}┐{C.RESET}")
    header = f"SBD: {sbd}"
    print(f"  {C.BOLD}{C.WHITE}│{C.RESET} {header}".ljust(w + 12) + f"{C.WHITE}│{C.RESET}")
    print(f"  {C.WHITE}├{'─' * w}┤{C.RESET}")
    for subject, score in parsed.items():
        if subject == "SBD":
            continue
        color = C.GREEN if score >= 5 else C.RED
        left = f"  {C.WHITE}│{C.RESET}  {subject:<22} {color}{score:>5.2f}{C.RESET}"
        pad = w + 9 - len(subject)
        print(left + " " * max(pad - 5, 0) + f"{C.WHITE}│{C.RESET}")
    print(f"  {C.WHITE}└{'─' * w}┘{C.RESET}\n")
