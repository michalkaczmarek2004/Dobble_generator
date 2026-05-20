from __future__ import annotations

from typing import List, Tuple

from .utils import Generator, Rectangle, generate_until_area, save_models_json


def generate_card_rectangles(
    num_cards: int = 55,
    num_rectangles_per_card: int = 8,
    margin: float = 0.03,
) -> Tuple[List[List[Rectangle]], float]:
    circle_radius = 0.5 - margin
    packer = Generator(cx=0.5, cy=0.5, radius=circle_radius)

    pack_kwargs = {
        "n": num_rectangles_per_card,
        "iters": 1600,
        "restarts": 80,
        "move_sigma": 0.016,
        "rot_sigma": 5.0,
        "grow_hi": 1.10,
    }

    models: List[List[Rectangle]] = []
    for _ in range(num_cards):
        rectangles, area, attempts = generate_until_area(
            packer,
            target_area=0.44,
            max_tries=100,
            pack_kwargs=pack_kwargs,
        )
        models.append(rectangles)
        print(f"Model: area={area:.6f}, attempts={attempts}")

    return models, circle_radius


def save_template_json(
    card_rectangles: List[List[Rectangle]],
    circle_radius: float,
    output_file_path: str = "templates.json",
) -> None:
    save_models_json(
        card_rectangles,
        path=output_file_path,
        include_corners=True,
        meta={
            "circle_center": [0.5, 0.5],
            "circle_R": circle_radius,
        },
    )
    print(f"Saved: {output_file_path}")
