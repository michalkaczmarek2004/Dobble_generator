from __future__ import annotations

import argparse

from dobble_library.json_template_generator.shortcuts import (
    generate_card_rectangles,
    save_template_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Dobble card layout templates."
    )
    parser.add_argument(
        "--num-cards",
        type=int,
        default=55,
        help="Number of card templates to generate.",
    )
    parser.add_argument(
        "--symbols-per-card",
        type=int,
        default=8,
        help="Number of symbol slots per card.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.03,
        help="Circle margin as fraction of card size (0-1). Affects usable area for symbols.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path. Defaults to models_{num_cards}.json.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = args.output or f"models_{args.num_cards}.json"
    models, circle_radius = generate_card_rectangles(
        num_cards=args.num_cards,
        num_rectangles_per_card=args.symbols_per_card,
        margin=args.margin,
    )
    save_template_json(models, circle_radius, output_file_path=output)
