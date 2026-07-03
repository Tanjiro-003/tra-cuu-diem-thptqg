"""Xuất kết quả ra Excel và vẽ biểu đồ phổ điểm chuyên sâu (kèm bảng thống kê)."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import ui

DEFAULT_CHART_DIR = Path("PhoDiem")


def export_to_excel(results: list[dict], year: str) -> pd.DataFrame:
    """Ghi danh sách kết quả ra file Excel (cột SBD đứng đầu). Trả về DataFrame gốc."""
    df = pd.DataFrame(results)
    ordered_cols = ["SBD"] + [c for c in df.columns if c != "SBD"]
    df = df[ordered_cols]

    excel_filename = f"KetQua_DiemThi_{year}.xlsx"
    df.fillna("x").to_excel(excel_filename, index=False)
    ui.ok(f"Đã lưu {len(df)} kết quả vào file: {excel_filename}")
    return df


def draw_advanced_histogram(df: pd.DataFrame, subject: str, year: str, output_dir: Path = DEFAULT_CHART_DIR) -> bool:
    """Vẽ phổ điểm chi tiết kèm bảng thống kê (ĐTB, trung vị, độ lệch chuẩn,
    tỉ lệ dưới điểm liệt/trên 7, mode, số điểm 10/0...) cho một môn thi.

    Trả về True nếu vẽ được (có dữ liệu), False nếu môn đó không có điểm hợp lệ.
    """
    scores = pd.to_numeric(df[subject], errors="coerce").dropna()
    if scores.empty:
        return False

    total_students = len(scores)
    mean_score = scores.mean()
    median_score = scores.median()
    std_dev = scores.std()
    mad = (scores - median_score).abs().mean()
    under_5 = (scores < 5).sum()
    under_5_pct = (under_5 / total_students) * 100
    above_7 = (scores >= 7).sum()
    above_7_pct = (above_7 / total_students) * 100
    mode_score = scores.mode().iloc[0] if not scores.mode().empty else np.nan
    score_10 = (scores == 10).sum()
    score_0 = (scores == 0).sum()
    under_1 = (scores <= 1).sum()
    under_1_pct = (under_1 / total_students) * 100

    bins = np.arange(0, 10.5, 0.5)
    cats = pd.cut(scores, bins=bins, include_lowest=True, right=True)
    counts = cats.value_counts().sort_index()

    labels = []
    for interval in counts.index:
        left_bracket = "[" if interval.left == 0 else "("
        labels.append(f"{left_bracket}{interval.left}, {interval.right}]")

    fig = plt.figure(figsize=(15, 7))
    gs = fig.add_gridspec(1, 3)

    ax_bar = fig.add_subplot(gs[0, :2])
    bars = ax_bar.bar(labels, counts.values, color="#1f77b4", edgecolor="white", width=0.8)

    ax_bar.set_title(f"Biểu đồ phổ điểm thi THPT môn {subject} - Năm {year}", fontsize=14, pad=20)
    ax_bar.set_xlabel("Điểm", fontsize=12)
    ax_bar.set_ylabel("Số lượng thí sinh", fontsize=12)
    ax_bar.tick_params(axis="x", rotation=90)

    max_count = counts.max()
    ax_bar.set_ylim(0, max_count * 1.2)

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax_bar.annotate(
                f"{int(height)}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                rotation=90,
                fontsize=9,
            )

    ax_table = fig.add_subplot(gs[0, 2])
    ax_table.axis("off")

    table_data = [
        ["Số TS", f"{total_students:,.0f}", ""],
        ["ĐTB", f"{mean_score:.2f}", ""],
        ["Trung vị", f"{median_score:.1f}", ""],
        ["ĐLC", f"{std_dev:.2f}", ""],
        ["MAD", f"{mad:.2f}", ""],
        ["< 5", f"{under_5:,.0f}", f"{under_5_pct:.3f} %"],
        [">= 7", f"{above_7:,.0f}", f"{above_7_pct:.3f} %"],
        ["Mode", f"{mode_score:.1f}", ""],
        ["Điểm 10", f"{score_10:,.0f}", ""],
        ["Điểm 0", f"{score_0:,.0f}", ""],
        ["<= 1", f"{under_1:,.0f}", f"{under_1_pct:.3f} %"],
    ]

    table = ax_table.table(cellText=table_data, loc="center", cellLoc="right", colWidths=[0.35, 0.35, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.2)

    for (i, j), cell in table.get_celld().items():
        if j == 0:
            cell.set_text_props(weight="bold", color="white", ha="left")
            cell.set_facecolor("#4A7bc7")
        else:
            cell.set_facecolor("#e9eff9" if i % 2 == 0 else "#ffffff")

        if i in [1, 3, 8] and j == 1:
            cell.set_text_props(color="red")

    plt.tight_layout()

    safe_subject = subject.replace(" ", "_")
    folder_path = output_dir / safe_subject
    folder_path.mkdir(parents=True, exist_ok=True)

    file_path = folder_path / f"PhoDiem_{year}.png"
    plt.savefig(file_path, bbox_inches="tight", dpi=150, facecolor="white")
    plt.close()
    return True


def export_and_visualize(results: list[dict], year: str, output_dir: Path = DEFAULT_CHART_DIR) -> None:
    """Xuất Excel và vẽ phổ điểm chuyên sâu (theo năm) cho danh sách kết quả."""
    if not results:
        ui.warn("Không có dữ liệu hợp lệ để xuất báo cáo.")
        return

    ui.section("Xuất báo cáo")
    df = export_to_excel(results, year)

    ui.step(f"Đang vẽ biểu đồ phổ điểm chuyên sâu cho năm {year}...")
    subjects = [c for c in df.columns if c != "SBD"]
    drawn = sum(draw_advanced_histogram(df, subject, year, output_dir) for subject in subjects)

    ui.ok(f"Đã vẽ {drawn}/{len(subjects)} biểu đồ, phân loại theo thư mục môn trong '{output_dir}/'.")
