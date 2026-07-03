"""Giao diện dòng lệnh cho công cụ tra cứu điểm thi."""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import ui
from .api import ScoreLookupError, build_session, fetch_score, get_base_api_url, process_single_sbd
from .captcha import CaptchaSolver
from .config import load_config
from .parser import parse_score_string
from .report import export_and_visualize

DEFAULT_WORKERS = 5


def _run_single(session, base_api_url, solver, sbd: str, year: str) -> None:
    ui.section(f"Đang tra cứu SBD {sbd}")
    raw_score = fetch_score(session, base_api_url, sbd, solver)
    if not raw_score:
        return
    parsed = parse_score_string(raw_score)
    ui.score_table(parsed, sbd)
    parsed["SBD"] = sbd
    export_and_visualize([parsed], year)


def _run_batch(
    session,
    base_api_url,
    solver,
    input_file: Path,
    delay: float,
    year: str,
    workers: int,
) -> None:
    if not input_file.exists():
        input_file.touch()
        ui.warn(f"File '{input_file}' chưa tồn tại, đã tự tạo file trống.")
        ui.info("Hãy copy danh sách SBD (mỗi số 1 dòng) vào rồi chạy lại.")
        return

    lines = [line.strip() for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        ui.warn("Danh sách SBD trong file đang trống!")
        return

    effective_workers = workers
    if not solver.use_2captcha and workers > 1:
        ui.warn("Bạn đang không dùng 2Captcha — chạy đa luồng khi nhập Captcha bằng tay sẽ làm console bị rối.")
        ui.info("Tự động đặt số luồng về 1.")
        effective_workers = 1

    ui.section(f"Tra cứu hàng loạt: {len(lines)} SBD, {effective_workers} luồng")
    results = []

    if effective_workers <= 1:
        for i, sbd in enumerate(lines):
            raw_score = fetch_score(session, base_api_url, sbd, solver)
            if raw_score:
                parsed = parse_score_string(raw_score)
                parsed["SBD"] = sbd
                results.append(parsed)
            ui.progress_bar(i + 1, len(lines), label=f"SBD {sbd}")
            if i < len(lines) - 1:
                time.sleep(delay)
    else:
        # Đa luồng: mỗi luồng dùng session riêng (tạo trong process_single_sbd)
        # để tránh việc các luồng ghi đè token Captcha của nhau.
        done = 0
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            futures = {
                executor.submit(process_single_sbd, sbd, base_api_url, solver): sbd for sbd in lines
            }
            for future in as_completed(futures):
                sbd_task = futures[future]
                try:
                    parsed = future.result()
                    if parsed:
                        results.append(parsed)
                except Exception as exc:  # noqa: BLE001 - muốn log mọi lỗi worker, không dừng cả batch
                    ui.err(f"Lỗi không mong muốn với SBD {sbd_task}: {exc}")
                done += 1
                ui.progress_bar(done, len(lines), label=f"SBD {sbd_task}")

    ui.ok(f"Tra cứu xong {len(results)}/{len(lines)} SBD có điểm.")
    export_and_visualize(results, year)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tra cứu điểm thi tốt nghiệp THPT tự động")
    parser.add_argument("--sbd", help="Tra cứu một số báo danh duy nhất (bỏ trống để chọn chế độ tương tác).")
    parser.add_argument(
        "--batch-file",
        type=Path,
        default=Path("sbd.txt"),
        help="File danh sách SBD cho chế độ hàng loạt (mặc định: sbd.txt).",
    )
    parser.add_argument("--batch", action="store_true", help="Chạy chế độ tra cứu hàng loạt từ --batch-file.")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Số luồng chạy song song ở chế độ hàng loạt (mặc định {DEFAULT_WORKERS}, cần bật 2Captcha).",
    )
    parser.add_argument(
        "--year",
        default=str(datetime.now().year),
        help="Năm thi, dùng để đặt tên file kết quả/biểu đồ (mặc định: năm hiện tại).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    ui.banner(
        "🎯  TRA CỨU ĐIỂM THI TỐT NGHIỆP THPT",
        f"Đa luồng • Tự động giải Captcha • Xuất Excel • Phổ điểm năm {args.year}",
    )

    ui.section("Kiểm tra cấu hình")
    config = load_config()
    session = build_session()
    solver = CaptchaSolver(config.api_key, config.use_2captcha)

    ui.step("Lấy cấu hình máy chủ BGD...")
    try:
        base_api_url = get_base_api_url(session)
    except ScoreLookupError as exc:
        ui.err(str(exc))
        return
    ui.ok("Kết nối máy chủ thành công.")

    if args.sbd:
        _run_single(session, base_api_url, solver, args.sbd.strip(), args.year)
        ui.footer("🎉  Hoàn tất!  🎉")
        return

    if args.batch:
        workers = args.workers or DEFAULT_WORKERS
        _run_batch(session, base_api_url, solver, args.batch_file, config.request_delay, args.year, workers)
        ui.footer("🎉  Hoàn tất!  🎉")
        return

    # Chế độ tương tác nếu không truyền cờ nào
    ui.section("Chọn chế độ hoạt động")
    print(f"  {ui.C.WHITE}1.{ui.C.RESET} Tra cứu 1 SBD")
    print(f"  {ui.C.WHITE}2.{ui.C.RESET} Tra cứu hàng loạt (đa luồng - đọc từ file sbd.txt)")
    choice = input(f"\n  {ui.C.BOLD}Lựa chọn của bạn (1/2): {ui.C.RESET}").strip()

    if choice == "1":
        sbd = input(f"  {ui.C.BOLD}Nhập Số Báo Danh cần tra: {ui.C.RESET}").strip()
        if sbd:
            _run_single(session, base_api_url, solver, sbd, args.year)
    elif choice == "2":
        workers = DEFAULT_WORKERS
        if solver.use_2captcha:
            raw = input(f"\n  Nhập số luồng chạy song song (mặc định {DEFAULT_WORKERS}): ").strip()
            if raw.isdigit():
                workers = int(raw)
        _run_batch(session, base_api_url, solver, args.batch_file, config.request_delay, args.year, workers)
    else:
        ui.err("Lựa chọn không hợp lệ, thoát chương trình.")
        return

    ui.footer("🎉  Hoàn tất!  🎉")


if __name__ == "__main__":
    main()
