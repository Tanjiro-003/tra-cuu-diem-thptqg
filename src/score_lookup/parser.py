"""Phân tích chuỗi điểm trả về từ API thành dữ liệu có cấu trúc."""

from __future__ import annotations

import re

_SCORE_PATTERN = re.compile(
    r"([A-ZÂĐÊÔƠƯa-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộ"
    r"ơờớởỡợùúủũụưừứửữựỳýỷỹỵ\s]+):\s*([\d\.]+)"
)


def parse_score_string(score_str: str) -> dict[str, float]:
    """Trích xuất chuỗi 'Toán: 8.5, Văn: 7.25, ...' thành dict {môn: điểm}."""
    return {
        subject.strip(): float(score)
        for subject, score in _SCORE_PATTERN.findall(score_str)
    }
