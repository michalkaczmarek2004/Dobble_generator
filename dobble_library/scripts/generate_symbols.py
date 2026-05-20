from __future__ import annotations

import argparse
import colorsys
import sys
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from deck_generator import select_cards
from deck_generator.dobble_algorithm import load_patterns

SymbolShape = Literal["circle", "square", "mixed"]
ConcreteSymbolShape = Literal["circle", "square"]


def parse_symbol_shape(value: str) -> SymbolShape:
    normalized = value.strip().lower().replace("-", "_")
    aliases: dict[str, SymbolShape] = {
        "circle": "circle",
        "circles": "circle",
        "kolo": "circle",
        "kola": "circle",
        "square": "square",
        "squares": "square",
        "kwadrat": "square",
        "kwadraty": "square",
        "mixed": "mixed",
        "mix": "mixed",
        "mieszane": "mixed",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise argparse.ArgumentTypeError(
            "Shape must be one of: circle/kolo, square/kwadrat, mixed/mieszane."
        ) from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate placeholder symbol images for a Dobble template file."
    )
    parser.add_argument(
        "--templates",
        default="models_55.json",
        help="Path to the generated template JSON file.",
    )
    parser.add_argument(
        "--output-dir", default="symbols", help="Directory for generated symbol images."
    )
    parser.add_argument(
        "--size-px",
        type=int,
        default=512,
        help="Generated symbol image size in pixels.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed used to validate the deck size.",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing symbol files."
    )
    parser.add_argument(
        "--shape",
        type=parse_symbol_shape,
        default="circle",
        metavar="{circle,square,mixed}",
        help=(
            "Shape used for generated symbols. Accepted values: "
            "circle/kolo, square/kwadrat, mixed/mieszane."
        ),
    )
    return parser.parse_args()


def color_for_symbol(index: int, total: int) -> tuple[int, int, int]:
    hue = index / max(total, 1)
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.62, 0.88)
    return int(red * 255), int(green * 255), int(blue * 255)


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def shape_for_symbol(index: int, shape: SymbolShape) -> ConcreteSymbolShape:
    if shape == "mixed":
        return "circle" if index % 2 == 0 else "square"
    return shape


def draw_symbol_shape(
    draw: ImageDraw.ImageDraw,
    shape: ConcreteSymbolShape,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    width: int,
) -> None:
    if shape == "circle":
        draw.ellipse(
            box,
            fill=(*fill, 255),
            outline=(*outline, 255),
            width=width,
        )
        return

    draw.rectangle(
        box,
        fill=(*fill, 255),
        outline=(*outline, 255),
        width=width,
    )


def save_symbol(
    path: Path,
    index: int,
    total: int,
    size_px: int,
    shape: SymbolShape = "circle",
) -> None:
    image = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = max(12, size_px // 14)
    fill = color_for_symbol(index, total)
    outline = tuple(max(channel - 65, 0) for channel in fill)
    shape_box = (margin, margin, size_px - margin, size_px - margin)

    draw_symbol_shape(
        draw=draw,
        shape=shape_for_symbol(index, shape),
        box=shape_box,
        fill=fill,
        outline=outline,
        width=max(4, size_px // 32),
    )

    label = str(index + 1)
    font = load_font(size_px // 3)
    text_box = draw.textbbox((0, 0), label, font=font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    text_x = (size_px - text_width) / 2
    text_y = (size_px - text_height) / 2 - size_px * 0.03

    draw.text((text_x, text_y), label, fill=(255, 255, 255, 255), font=font)
    image.save(path)


def main() -> None:
    args = parse_args()
    patterns = load_patterns(args.templates)
    if not patterns:
        raise ValueError(f"No card templates found in {args.templates!r}.")

    symbols_per_card = len(patterns[0])
    if any(len(pattern) != symbols_per_card for pattern in patterns):
        raise ValueError("All templates must contain the same number of symbol slots.")

    _, total_symbols = select_cards(
        patterns_count=len(patterns),
        symbols_per_card=symbols_per_card,
        seed=args.seed,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for index in range(total_symbols):
        output_path = output_dir / f"symbol_{index + 1:02d}.png"
        if output_path.exists() and not args.overwrite:
            continue
        save_symbol(
            output_path,
            index=index,
            total=total_symbols,
            size_px=args.size_px,
            shape=args.shape,
        )

    print(f"Generated {total_symbols} {args.shape} symbols in: {output_dir}")


if __name__ == "__main__":
    main()
