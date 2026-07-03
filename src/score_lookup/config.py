"""Đọc, tạo và xác thực file cấu hình của công cụ."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import requests

from . import ui

DEFAULT_CONFIG_PATH = Path("config_2captcha.json")
TWO_CAPTCHA_BALANCE_URL = "https://api.2captcha.com/getBalance"


@dataclass
class AppConfig:
    """Cấu hình chạy của ứng dụng."""

    api_key: str = ""
    use_2captcha: bool = False
    request_delay: float = 1.5


def _write_default_config(path: Path) -> None:
    default_config = {
        "2captcha": {
            "api_key": "",
            "enable": False,
        },
        "settings": {
            "delay_between_requests": 1.5,
        },
    }
    path.write_text(
        json.dumps(default_config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    ui.warn(f"Đã tạo file cấu hình mẫu tại '{path}'. Hãy điền api_key nếu muốn dùng 2Captcha.")


def _check_2captcha_balance(api_key: str) -> float | None:
    """Trả về số dư tài khoản 2Captcha, hoặc None nếu không xác thực được."""
    try:
        response = requests.post(
            TWO_CAPTCHA_BALANCE_URL,
            json={"clientKey": api_key},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        ui.err(f"Lỗi kết nối đến máy chủ 2Captcha: {exc}")
        return None

    if data.get("errorId") != 0:
        ui.err(f"Lỗi API Key 2Captcha: {data.get('errorDescription')}")
        return None

    return float(data.get("balance", 0))


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Đọc file cấu hình JSON, tạo file mẫu nếu chưa tồn tại.

    Nếu 2Captcha được bật nhưng api_key không hợp lệ hoặc hết tiền,
    tự động chuyển sang chế độ nhập Captcha thủ công.
    """
    if not path.exists():
        _write_default_config(path)
        return AppConfig()

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    captcha_cfg = raw.get("2captcha", {})
    api_key = captcha_cfg.get("api_key", "")
    use_2captcha = bool(captcha_cfg.get("enable", False))
    delay = float(raw.get("settings", {}).get("delay_between_requests", 1.5))

    placeholder_key = "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
    if not (use_2captcha and api_key and api_key != placeholder_key):
        return AppConfig(api_key=api_key, use_2captcha=False, request_delay=delay)

    balance = _check_2captcha_balance(api_key)
    if balance is None:
        ui.warn("Tự động chuyển sang nhập Captcha thủ công.")
        return AppConfig(api_key=api_key, use_2captcha=False, request_delay=delay)

    if balance <= 0:
        ui.warn("Tài khoản 2Captcha đã hết tiền. Tự động chuyển sang nhập tay.")
        return AppConfig(api_key=api_key, use_2captcha=False, request_delay=delay)

    ui.ok(f"2Captcha hợp lệ. Số dư: ${balance}")
    return AppConfig(api_key=api_key, use_2captcha=True, request_delay=delay)
