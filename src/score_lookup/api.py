"""Giao tiếp với API tra cứu điểm thi tốt nghiệp THPT."""

from __future__ import annotations

import time
import urllib.parse

import requests

from . import ui
from .captcha import CaptchaSolver

CONFIG_URL = "https://tracuudiem.thitotnghiepthpt.edu.vn/config.json"
PORTAL_ORIGIN = "https://tracuudiem.thitotnghiepthpt.edu.vn"

MAX_CAPTCHA_RETRIES = 10
HTTP_TIMEOUT = 20


class ScoreLookupError(Exception):
    """Lỗi phát sinh trong quá trình tra cứu điểm."""


def build_session() -> requests.Session:
    """Tạo một session HTTP mới với header chuẩn.

    Mỗi luồng khi tra cứu song song nên có session riêng (không share Session
    giữa các thread) để tránh việc token Captcha của luồng này bị luồng khác
    ghi đè.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"
            ),
            "Connection": "keep-alive",
        }
    )
    return session


def get_base_api_url(session: requests.Session) -> str:
    """Lấy BASE_URL động của hệ thống tra cứu điểm."""
    try:
        response = session.get(CONFIG_URL, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        base_url = response.json().get("BASE_URL")
    except (requests.RequestException, ValueError) as exc:
        raise ScoreLookupError(f"Lỗi lấy cấu hình hệ thống: {exc}") from exc

    if not base_url:
        raise ScoreLookupError("Không tìm thấy BASE_URL trong cấu hình hệ thống.")
    return base_url


def fetch_score(
    session: requests.Session,
    base_api_url: str,
    sbd: str,
    solver: CaptchaSolver,
) -> str | None:
    """Tra cứu điểm cho một số báo danh, tự thử lại nếu nhập sai Captcha.

    Trả về chuỗi điểm thô nếu thành công, None nếu SBD không có điểm.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": PORTAL_ORIGIN,
        "Referer": f"{PORTAL_ORIGIN}/",
    }
    captcha_url = f"https://{base_api_url}/Captcha/GetCaptchaImage"

    for attempt in range(1, MAX_CAPTCHA_RETRIES + 1):
        captcha_res = session.get(captcha_url, timeout=HTTP_TIMEOUT)
        if captcha_res.status_code != 200:
            ui.warn(f"SBD {sbd}: không tải được ảnh Captcha, thử lại sau 2s...")
            time.sleep(2)
            continue

        captcha_code = solver.solve(captcha_res.content, sbd)
        if not captcha_code:
            continue

        search_url = (
            f"https://{base_api_url}/Search_Score_/GetStudentMark"
            f"?SBD={urllib.parse.quote(sbd)}&CaptchaValue={captcha_code}"
        )
        score_res = session.get(search_url, headers=headers, timeout=HTTP_TIMEOUT)

        if score_res.status_code == 200:
            ui.ok(f"SBD {sbd}: Tra cứu thành công!")
            solver.cleanup(sbd)
            return score_res.text

        if score_res.status_code == 204:
            ui.warn(f"SBD {sbd}: Chưa có điểm hoặc SBD không tồn tại.")
            solver.cleanup(sbd)
            return None

        error_msg = ""
        try:
            error_msg = score_res.json().get("ErrorMesage", "")
        except ValueError:
            pass

        if "xác nhận" in error_msg.lower() or "captcha" in error_msg.lower():
            ui.warn(f"SBD {sbd}: mã xác nhận sai (lần {attempt}), tải lại mã mới...")
            continue

        if error_msg:
            ui.err(f"SBD {sbd}: lỗi hệ thống: {error_msg}")
            return None

        ui.warn(f"SBD {sbd}: lỗi HTTP {score_res.status_code}, thử lại...")
        time.sleep(2)

    ui.err(f"SBD {sbd}: vượt quá số lần thử Captcha cho phép, bỏ qua.")
    return None


def process_single_sbd(
    sbd: str,
    base_api_url: str,
    solver: CaptchaSolver,
) -> dict | None:
    """Hàm worker dùng cho tra cứu đa luồng.

    Mỗi lần gọi tạo một session HTTP độc lập để tránh việc các luồng chạy
    song song ghi đè token Captcha của nhau. Trả về dict điểm (có key 'SBD')
    hoặc None nếu SBD không có điểm.
    """
    from .parser import parse_score_string  # tránh import vòng ở module-level

    local_session = build_session()
    raw_score = fetch_score(local_session, base_api_url, sbd, solver)
    if not raw_score:
        return None

    parsed = parse_score_string(raw_score)
    parsed["SBD"] = sbd
    return parsed
