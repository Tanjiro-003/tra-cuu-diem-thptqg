"""Giải mã Captcha bằng 2Captcha (API createTask/getTaskResult) hoặc nhập tay."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import requests

from . import ui

CREATE_TASK_URL = "https://api.2captcha.com/createTask"
RESULT_URL = "https://api.2captcha.com/getTaskResult"

POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 24  # ~2 phút chờ tối đa


class CaptchaSolver:
    """Bọc logic giải Captcha, có thể dùng 2Captcha hoặc yêu cầu nhập tay.

    An toàn khi dùng đa luồng: mỗi SBD lưu ảnh Captcha nhập-tay ra một file
    riêng (captcha_<sbd>.png) để tránh nhiều luồng ghi đè lên nhau.
    """

    def __init__(self, api_key: str, use_2captcha: bool):
        self.api_key = api_key
        self.use_2captcha = use_2captcha

    def solve(self, image_bytes: bytes, sbd: str) -> str:
        """Trả về mã Captcha dạng chuỗi. Ưu tiên 2Captcha, dự phòng nhập tay."""
        if self.use_2captcha:
            code = self._solve_with_2captcha(image_bytes)
            if code:
                return code
            ui.warn(f"SBD {sbd}: 2Captcha giải thất bại, chuyển sang nhập tay cho lần này.")

        return self._solve_manually(image_bytes, sbd)

    def cleanup(self, sbd: str) -> None:
        """Xoá file captcha nhập tay còn sót lại sau khi tra cứu xong (nếu có)."""
        path = Path(f"captcha_{sbd}.png")
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    def _solve_with_2captcha(self, image_bytes: bytes) -> str | None:
        ui.step("Đang gửi Captcha lên 2Captcha...")
        base64_img = base64.b64encode(image_bytes).decode("utf-8")

        task_payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": base64_img,
                "phrase": False,
                "case": False,
                "numeric": 0,
                "math": False,
                "minLength": 4,
                "maxLength": 6,
                "comment": "Vui lòng nhập mã bảo mật trong ảnh",
            },
        }

        try:
            create_res = requests.post(CREATE_TASK_URL, json=task_payload, timeout=15).json()
        except (requests.RequestException, ValueError) as exc:
            ui.err(f"Lỗi kết nối 2Captcha: {exc}")
            return None

        if create_res.get("errorId") != 0:
            ui.err(f"Lỗi tạo task 2Captcha: {create_res.get('errorDescription')}")
            return None

        task_id = create_res.get("taskId")
        ui.step(f"Đã gửi Captcha (Task ID: {task_id}). Đang chờ thợ giải...")

        result_payload = {"clientKey": self.api_key, "taskId": task_id}
        for _ in range(MAX_POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL_SECONDS)
            try:
                result_res = requests.post(RESULT_URL, json=result_payload, timeout=15).json()
            except (requests.RequestException, ValueError) as exc:
                ui.err(f"Lỗi lấy kết quả 2Captcha: {exc}")
                return None

            if result_res.get("errorId") != 0:
                ui.err(f"Lỗi lấy kết quả: {result_res.get('errorDescription')}")
                return None

            status = result_res.get("status")
            if status == "ready":
                solution = result_res.get("solution", {}).get("text")
                ui.ok(f"2Captcha đã giải xong: {solution}")
                return solution
            if status != "processing":
                ui.err(f"Trạng thái không mong muốn từ 2Captcha: {status}")
                return None

        ui.err("Hết thời gian chờ 2Captcha giải mã.")
        return None

    @staticmethod
    def _solve_manually(image_bytes: bytes, sbd: str) -> str:
        # Lưu theo tên SBD để chạy đa luồng không bị nhiều thí sinh đè ảnh của nhau.
        captcha_path = Path(f"captcha_{sbd}.png")
        captcha_path.write_bytes(image_bytes)
        print(f"\n  {ui.C.YELLOW}🔎 Đang tra cứu SBD: {ui.C.BOLD}{sbd}{ui.C.RESET}")
        code = input(f"  {ui.C.CYAN}📎 Mở file '{captcha_path}' và nhập mã xác nhận: {ui.C.RESET}")
        return code.strip()
