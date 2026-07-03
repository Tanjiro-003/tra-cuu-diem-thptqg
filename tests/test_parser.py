import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from score_lookup.parser import parse_score_string


def test_parse_score_string_basic():
    raw = "Toán: 8.5, Ngữ văn: 7.25, Tiếng Anh: 9.0"
    result = parse_score_string(raw)
    assert result == {"Toán": 8.5, "Ngữ văn": 7.25, "Tiếng Anh": 9.0}


def test_parse_score_string_empty():
    assert parse_score_string("") == {}


def test_parse_score_string_ignores_non_matching_text():
    raw = "Kết quả: Vật lí: 6.75; Hóa học: 5.5"
    result = parse_score_string(raw)
    assert result["Vật lí"] == 6.75
    assert result["Hóa học"] == 5.5
