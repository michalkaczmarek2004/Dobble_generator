from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageOps


@dataclass
class RectSlot:
    x: float
    y: float
    width: float
    height: float
    angle: float


def is_prime(number: int) -> bool:
    if number < 2:
        return False
    for i in range(2, int(number**0.5) + 1):
        if number % i == 0:
            return False
    return True


def load_patterns(
    path: str = "../Model_data/models/templates.json",
) -> List[List[RectSlot]]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    patterns: List[List[RectSlot]] = []
    for model in data.get("models", []):
        rects: List[RectSlot] = []
        rects_src = sorted(
            model.get("rects", []), key=lambda item: int(item.get("id", 0))
        )
        for rect in rects_src:
            rects.append(
                RectSlot(
                    x=float(rect["x"]),
                    y=float(rect["y"]),
                    width=float(rect["w"]),
                    height=float(rect["h"]),
                    angle=float(rect.get("ang_deg", rect.get("rotation angle", 0))),
                )
            )
        if rects:
            patterns.append(rects)
    return patterns


def generate_full_dobble_deck(symbols_per_card: int = 8) -> Tuple[List[List[int]], int]:
    n = symbols_per_card - 1
    if not is_prime(n):
        raise ValueError(
            f"Ta implementacja wymaga, aby symbols_per_card - 1 było liczbą pierwszą. Dla {symbols_per_card=} mamy n={n}."
        )

    point_id = {}
    next_id = 0

    for x in range(n):
        for y in range(n):
            point_id[("affine", x, y)] = next_id
            next_id += 1

    for slope in range(n):
        point_id[("inf", slope)] = next_id
        next_id += 1

    point_id[("inf", "v")] = next_id
    next_id += 1

    cards: List[List[int]] = []

    for slope in range(n):
        for bias in range(n):
            card = [point_id[("affine", x, (slope * x + bias) % n)] for x in range(n)]
            card.append(point_id[("inf", slope)])
            cards.append(card)

    for x_const in range(n):
        card = [point_id[("affine", x_const, y)] for y in range(n)]
        card.append(point_id[("inf", "v")])
        cards.append(card)

    cards.append(
        [point_id[("inf", slope)] for slope in range(n)] + [point_id[("inf", "v")]]
    )

    expected = n * n + n + 1
    assert len(cards) == expected
    assert next_id == expected
    return cards, next_id


def verify_dobble_deck(cards: Sequence[Sequence[int]]) -> bool:
    for i in range(len(cards)):
        first = set(cards[i])
        for j in range(i + 1, len(cards)):
            second = set(cards[j])
            if len(first & second) != 1:
                return False
    return True


def select_cards(
    patterns_count: int,
    symbols_per_card: int = 8,
    seed: int = 1234,
) -> Tuple[List[List[int]], int]:
    full_cards, total_symbols = generate_full_dobble_deck(
        symbols_per_card=symbols_per_card
    )

    rng = random.Random(seed)
    rng.shuffle(full_cards)
    for card in full_cards:
        rng.shuffle(card)

    if patterns_count > len(full_cards):
        raise ValueError(
            f"Masz {patterns_count} wzorów kart, ale dla {symbols_per_card} symboli na karcie maksymalnie da się zbudować {len(full_cards)} kart w pełnej talii."
        )

    return full_cards[:patterns_count], total_symbols


def crop_transparent(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def load_symbol_images(symbols_dir: str, needed: int) -> List[Image.Image]:
    extensions = {".png", ".webp", ".jpg", ".jpeg"}
    paths = sorted(
        path
        for path in Path(symbols_dir).iterdir()
        if path.suffix.lower() in extensions
    )

    if len(paths) < needed:
        raise ValueError(
            f"W folderze {symbols_dir!r} jest tylko {len(paths)} plików graficznych, a potrzeba co najmniej {needed}."
        )

    images: List[Image.Image] = []
    for path in paths[:needed]:
        image = Image.open(path).convert("RGBA")
        images.append(crop_transparent(image))
    return images


def paste_symbol_into_slot(
    canvas: Image.Image,
    symbol_img: Image.Image,
    slot: RectSlot,
    card_size_px: int,
    fit_scale: float = 0.88,
    rotation_sign: int = -1,
    extra_angle: float = 0,
) -> None:
    slot_width = max(1, int(slot.width * card_size_px * fit_scale))
    slot_height = max(1, int(slot.height * card_size_px * fit_scale))

    fitted = ImageOps.contain(
        symbol_img, (slot_width, slot_height), method=Image.Resampling.LANCZOS
    )
    base = Image.new("RGBA", (slot_width, slot_height), (0, 0, 0, 0))
    paste_x = (slot_width - fitted.width) // 2
    paste_y = (slot_height - fitted.height) // 2
    base.paste(fitted, (paste_x, paste_y), fitted)

    rotated = base.rotate(
        rotation_sign * slot.angle + extra_angle,
        expand=True,
        resample=Image.Resampling.BICUBIC,
    )

    center_x = int(slot.x * card_size_px)
    center_y = int(slot.y * card_size_px)
    symbol_x = center_x - rotated.width // 2
    symbol_y = center_y - rotated.height // 2
    canvas.paste(rotated, (symbol_x, symbol_y), rotated)


def render_card(
    card_symbols: Sequence[int],
    pattern: Sequence[RectSlot],
    symbol_images: Sequence[Image.Image],
    card_size_px: int = 1134,
    fit_scale: float = 1.0,  # previous 0.88
    round_card: bool = True,
    rotation_sign: int = -1,
    circle_margin: float = 0,  # previous 0.02
    rng: random.Random | None = None,
) -> Image.Image:
    if len(card_symbols) != len(pattern):
        raise ValueError(
            f"Karta ma {len(card_symbols)} symboli, a wzór ma {len(pattern)} slotów."
        )

    canvas = Image.new("RGBA", (card_size_px, card_size_px), (255, 255, 255, 0))

    if round_card:
        draw = ImageDraw.Draw(canvas)
        margin = max(1, int(circle_margin * card_size_px))
        draw.ellipse(
            (margin, margin, card_size_px - margin, card_size_px - margin),
            fill=(0, 0, 0, 0),
            outline=(0, 0, 0, 0),
            width=max(2, card_size_px // 256),
        )

    for symbol_id, slot in zip(card_symbols, pattern):
        extra_angle = rng.choice([0, 180]) if rng is not None else 0
        paste_symbol_into_slot(
            canvas=canvas,
            symbol_img=symbol_images[symbol_id],
            slot=slot,
            card_size_px=card_size_px,
            fit_scale=fit_scale,
            rotation_sign=rotation_sign,
            extra_angle=extra_angle,
        )

    return canvas


# PX = round(96 / 25.4 * 300)


def render_deck(
    json_path: str,
    symbols_dir: str,
    output_dir: str = "dobble_library/output_cards",
    card_size_px: int = 1134,  # 1024
    seed: int = 1234,
    fit_scale: float = 1.0,  # previous 0.88
    rotation_sign: int = -1,
    circle_margin: float = 0,  # previous 0.02
) -> None:
    patterns = load_patterns(json_path)
    if not patterns:
        raise ValueError("Nie udało się wczytać żadnych wzorów kart z JSON-a.")

    symbols_per_card = len(patterns[0])
    cards, total_symbols = select_cards(
        patterns_count=len(patterns),
        symbols_per_card=symbols_per_card,
        seed=seed,
    )

    if not verify_dobble_deck(cards):
        raise RuntimeError("Wygenerowana talia nie spełnia warunku Dobble.")

    symbol_images = load_symbol_images(symbols_dir, needed=total_symbols)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    render_rng = random.Random(seed)
    for index, (card_symbols, pattern) in enumerate(zip(cards, patterns), start=1):
        print(f"Generuję kartę {index}/{len(cards)}")
        card_image = render_card(
            card_symbols=card_symbols,
            pattern=pattern,
            symbol_images=symbol_images,
            card_size_px=card_size_px,
            fit_scale=fit_scale,
            round_card=True,
            rotation_sign=rotation_sign,
            circle_margin=circle_margin,
            rng=render_rng,
        )
        card_image.save(output_path / f"card_{index:02d}.png")
