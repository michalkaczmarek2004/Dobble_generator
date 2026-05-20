from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

DPI = 300
CARD_DIAMETER_MM = 96.0
INPUT_DIR = "../Model_data/output_cards"
OUTPUT_DIR = "../Results"
OUTPUT_PDF_NAME = "cards.pdf"


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# A4 page
# MM_PER_INCH = 25.4
# A4_WIDTH_MM = 210.0
# A4_HEIGHT_MM = 297.0

MM_PER_INCH = 25.4
NF_WIDTH_MM = 96.0
NF_HEIGHT_MM = 96.0


def mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / MM_PER_INCH * dpi)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create A4 PDF with one Dobble card per page."
    )
    parser.add_argument(
        "--input-dir",
        default=str(PROJECT_ROOT / INPUT_DIR),
        help="Directory with rendered card PNG files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / OUTPUT_DIR),
        help="Output directory for the PDF.",
    )
    parser.add_argument(
        "--output-name",
        default=OUTPUT_PDF_NAME,
        help="Output PDF filename.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DPI,
        help="Print resolution in DPI.",
    )
    parser.add_argument(
        "--card-diameter-mm",
        type=float,
        default=CARD_DIAMETER_MM,
        help="Card diameter in mm on the printed page.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    card_paths = sorted(p for p in input_path.iterdir() if p.suffix.lower() == ".png")
    if not card_paths:
        print(f"No PNG files found in {input_path}")
        sys.exit(1)

    page_w_px = mm_to_px(NF_WIDTH_MM, args.dpi)
    page_h_px = mm_to_px(NF_HEIGHT_MM, args.dpi)
    card_px = mm_to_px(args.card_diameter_mm, args.dpi)

    pages: list[Image.Image] = []
    for card_path in card_paths:
        print(f"Processing {card_path.name}")
        card_img = Image.open(card_path).convert("RGBA")
        card_img = card_img.resize((card_px, card_px), Image.Resampling.LANCZOS)

        page = Image.new("RGB", (page_w_px, page_h_px), (255, 255, 255))
        paste_x = (page_w_px - card_px) // 2
        paste_y = (page_h_px - card_px) // 2
        page.paste(card_img, (paste_x, paste_y), card_img)
        pages.append(page)

    output_file = output_path / args.output_name
    pages[0].save(
        output_file,
        "PDF",
        resolution=args.dpi,
        save_all=True,
        append_images=pages[1:],
    )
    print(f"Saved: {output_file} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
