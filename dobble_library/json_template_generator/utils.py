from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

MAX_RECTANGLE_ASPECT = 1.0
MIN_AREA = 0.02


def rectangle_proportion(
    width: float,
    height: float,
    max_proportion: float = MAX_RECTANGLE_ASPECT,
) -> Tuple[float, float]:
    if width >= height:
        if width > max_proportion * height:
            width = max_proportion * height
    else:
        if height > max_proportion * width:
            height = max_proportion * width
    return width, height


@dataclass
class Rectangle:
    x: float
    y: float
    w: float
    h: float
    ang_deg: float
    c: float = 1.0
    s: float = 0.0

    def update_trig(self) -> None:
        angle_rad = math.radians(self.ang_deg)
        self.c = math.cos(angle_rad)
        self.s = math.sin(angle_rad)

    def half_diagonal(self) -> float:
        return 0.5 * math.hypot(self.w, self.h)

    def area(self) -> float:
        return self.w * self.h

    def corners(self) -> List[Tuple[float, float]]:
        self.update_trig()
        dx = self.w / 2
        dy = self.h / 2
        local_points = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
        points: List[Tuple[float, float]] = []
        for local_x, local_y in local_points:
            rotated_x = local_x * self.c - local_y * self.s
            rotated_y = local_x * self.s + local_y * self.c
            points.append((self.x + rotated_x, self.y + rotated_y))
        return points


def check_rectangle_inside_circle(
    rectangle: Rectangle,
    circle_center_x: float,
    circle_center_y: float,
    circle_radius: float,
) -> bool:
    distance = math.hypot(rectangle.x - circle_center_x, rectangle.y - circle_center_y)
    if distance + rectangle.half_diagonal() <= circle_radius:
        return True

    radius_squared = circle_radius * circle_radius
    for point_x, point_y in rectangle.corners():
        dx = point_x - circle_center_x
        dy = point_y - circle_center_y
        if dx * dx + dy * dy > radius_squared:
            return False
    return True


def rectangle_collision(first: Rectangle, second: Rectangle) -> bool:
    eps = 1e-10

    a0x, a0y = first.c, first.s
    a1x, a1y = -first.s, first.c
    b0x, b0y = second.c, second.s
    b1x, b1y = -second.s, second.c

    tx = second.x - first.x
    ty = second.y - first.y

    def abs_dot(axis_x: float, axis_y: float) -> float:
        return abs(tx * axis_x + ty * axis_y)

    first_half_w, first_half_h = first.w / 2, first.h / 2
    second_half_w, second_half_h = second.w / 2, second.h / 2

    a0b0 = a0x * b0x + a0y * b0y
    a0b1 = a0x * b1x + a0y * b1y
    a1b0 = a1x * b0x + a1y * b0y
    a1b1 = a1x * b1x + a1y * b1y

    tests = [
        (abs_dot(a0x, a0y), first_half_w, second_half_w * abs(a0b0) + second_half_h * abs(a0b1)),
        (abs_dot(a1x, a1y), first_half_h, second_half_w * abs(a1b0) + second_half_h * abs(a1b1)),
        (abs_dot(b0x, b0y), first_half_w * abs(a0b0) + first_half_h * abs(a1b0), second_half_w),
        (abs_dot(b1x, b1y), first_half_w * abs(a0b1) + first_half_h * abs(a1b1), second_half_h),
    ]

    for projection, ra, rb in tests:
        if projection > ra + rb - eps:
            return False
    return True


class Generator:
    def __init__(self, cx: float = 0.5, cy: float = 0.5, radius: float = 0.47):
        self.cx = cx
        self.cy = cy
        self.R = radius

    def check_one_rectangle(self, rectangles: List[Rectangle], index: int) -> bool:
        rectangle = rectangles[index]
        if rectangle.area() < MIN_AREA:
            return False
        if not check_rectangle_inside_circle(rectangle, self.cx, self.cy, self.R):
            return False
        for other_index, other in enumerate(rectangles):
            if other_index == index:
                continue
            if rectangle_collision(rectangle, other):
                return False
        return True

    def check_all_rectangles_in_circle(self, rectangles: List[Rectangle]) -> bool:
        for rectangle in rectangles:
            if rectangle.area() < MIN_AREA:
                return False
            if not check_rectangle_inside_circle(rectangle, self.cx, self.cy, self.R):
                return False

        for i in range(len(rectangles)):
            for j in range(i + 1, len(rectangles)):
                if rectangle_collision(rectangles[i], rectangles[j]):
                    return False
        return True

    def pack(
        self,
        n: int = 8,
        iters: int = 1400,
        restarts: int = 60,
        move_sigma: float = 0.018,
        rot_sigma: float = 6.0,
        grow_hi: float = 1.10,
    ) -> List[Rectangle]:
        best_rectangles: List[Rectangle] = []
        best_score = -1e18

        def sample_in_disk(cx: float, cy: float, radius: float) -> Tuple[float, float]:
            angle = random.random() * 2.0 * math.pi
            rr = math.sqrt(random.random()) * radius
            return cx + rr * math.cos(angle), cy + rr * math.sin(angle)

        def max_inflate_one(index: int, local_grow_hi: float = 1.30) -> None:
            rectangle = rectangles[index]
            old_w, old_h = rectangle.w, rectangle.h
            lo, hi = 1.0, local_grow_hi
            for _ in range(16):
                mid = 0.5 * (lo + hi)
                rectangle.w = old_w * mid
                rectangle.h = old_h * mid
                rectangle.w, rectangle.h = rectangle_proportion(rectangle.w, rectangle.h)
                if self.check_one_rectangle(rectangles, index):
                    lo = mid
                else:
                    hi = mid

            rectangle.w = old_w * lo
            rectangle.h = old_h * lo
            rectangle.w, rectangle.h = rectangle_proportion(rectangle.w, rectangle.h)

        def build_valid_initial_layout() -> Optional[List[Rectangle]]:
            initial_rectangles: List[Rectangle] = []
            target_areas = sorted([random.uniform(0.023, 0.030) for _ in range(n)], reverse=True)

            for area in target_areas:
                placed = False
                for _ in range(500):
                    aspect = random.uniform(1.0 / MAX_RECTANGLE_ASPECT, MAX_RECTANGLE_ASPECT)
                    width = math.sqrt(area * aspect)
                    height = math.sqrt(area / aspect)

                    rectangle = Rectangle(
                        x=0.0,
                        y=0.0,
                        w=width,
                        h=height,
                        ang_deg=random.uniform(0.0, 180.0),
                    )
                    rectangle.update_trig()

                    margin = 0.001
                    center_radius = max(self.R - rectangle.half_diagonal() - margin, 0.0)
                    rectangle.x, rectangle.y = sample_in_disk(self.cx, self.cy, center_radius)

                    initial_rectangles.append(rectangle)
                    if self.check_one_rectangle(initial_rectangles, len(initial_rectangles) - 1):
                        placed = True
                        break
                    initial_rectangles.pop()

                if not placed:
                    return None

            return initial_rectangles

        for _ in range(restarts):
            rectangles = build_valid_initial_layout()
            if rectangles is None:
                continue

            for _ in range(iters):
                index = min(range(n), key=lambda i: rectangles[i].area()) if random.random() < 0.7 else random.randrange(n)
                rectangle = rectangles[index]

                if random.random() < 0.45:
                    old_state = (rectangle.x, rectangle.y, rectangle.ang_deg, rectangle.c, rectangle.s)
                    rectangle.x += random.uniform(-move_sigma, move_sigma)
                    rectangle.y += random.uniform(-move_sigma, move_sigma)
                    rectangle.ang_deg = (rectangle.ang_deg + random.uniform(-rot_sigma, rot_sigma)) % 180.0
                    rectangle.update_trig()
                    if not self.check_one_rectangle(rectangles, index):
                        rectangle.x, rectangle.y, rectangle.ang_deg, rectangle.c, rectangle.s = old_state

                old_w, old_h = rectangle.w, rectangle.h
                rectangle.w = old_w * grow_hi
                rectangle.h = old_h * grow_hi
                rectangle.w, rectangle.h = rectangle_proportion(rectangle.w, rectangle.h)

                if self.check_one_rectangle(rectangles, index):
                    continue

                rectangle.w, rectangle.h = old_w, old_h
                lo, hi = 1.0, grow_hi
                for _ in range(12):
                    mid = 0.5 * (lo + hi)
                    rectangle.w = old_w * mid
                    rectangle.h = old_h * mid
                    rectangle.w, rectangle.h = rectangle_proportion(rectangle.w, rectangle.h)
                    if self.check_one_rectangle(rectangles, index):
                        lo = mid
                    else:
                        hi = mid
                rectangle.w = old_w * lo
                rectangle.h = old_h * lo
                rectangle.w, rectangle.h = rectangle_proportion(rectangle.w, rectangle.h)

            for index in sorted(range(n), key=lambda i: rectangles[i].area()):
                max_inflate_one(index, local_grow_hi=1.25)

            if self.check_all_rectangles_in_circle(rectangles):
                areas = [rectangle.area() for rectangle in rectangles]
                mean_area = sum(areas) / len(areas)
                score = 10000.0 * sum(areas) + 200.0 * min(areas) - 20.0 * sum((a - mean_area) ** 2 for a in areas)
                if score > best_score:
                    best_score = score
                    best_rectangles = [
                        Rectangle(r.x, r.y, r.w, r.h, r.ang_deg, r.c, r.s) for r in rectangles
                    ]

        return best_rectangles


def draw_pattern(circle_radius: float, image_dimension_px: int, rectangles: List[Rectangle]) -> Image.Image:
    width = height = image_dimension_px
    center_x_px = width / 2
    center_y_px = height / 2
    radius_px = circle_radius * image_dimension_px

    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (center_x_px - radius_px, center_y_px - radius_px, center_x_px + radius_px, center_y_px + radius_px),
        outline="black",
        width=3,
    )

    for rectangle in rectangles:
        points = [(x * image_dimension_px, y * image_dimension_px) for (x, y) in rectangle.corners()]
        draw.polygon(points, outline="red", width=2)

    return image


def sum_rectangles_area(rectangles: List[Rectangle]) -> float:
    return sum(rectangle.w * rectangle.h for rectangle in rectangles)


def generate_until_area(
    packer: Generator,
    target_area: float = 0.4481,
    max_tries: int = 500,
    pack_kwargs: Optional[dict] = None,
) -> Tuple[List[Rectangle], float, int]:
    if pack_kwargs is None:
        pack_kwargs = {}

    best_rectangles: List[Rectangle] = []
    best_area = -1.0

    for attempt in range(1, max_tries + 1):
        rectangles = packer.pack(**pack_kwargs)
        area = sum_rectangles_area(rectangles)
        if area > best_area:
            best_area = area
            best_rectangles = rectangles
        if area >= target_area:
            return rectangles, area, attempt

    return best_rectangles, best_area, max_tries


def rects_to_dict(rectangles: List[Rectangle], include_corners: bool = True) -> Dict[str, Any]:
    return {
        "count": len(rectangles),
        "rects": [
            {
                "id": index,
                "x": rectangle.x,
                "y": rectangle.y,
                "w": rectangle.w,
                "h": rectangle.h,
                "ang_deg": rectangle.ang_deg,
                "area": rectangle.area(),
                **(
                    {"corners": [{"x": cx, "y": cy} for (cx, cy) in rectangle.corners()]}
                    if include_corners
                    else {}
                ),
            }
            for index, rectangle in enumerate(rectangles)
        ],
        "sum_area": sum_rectangles_area(rectangles),
    }


def save_models_json(
    models: List[List[Rectangle]],
    path: str = "models_55.json",
    include_corners: bool = True,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    payload = {
        "units": "normalized_0_1",
        "meta": meta or {},
        "num_models": len(models),
        "models": [
            {"model_id": model_index, **rects_to_dict(rectangles, include_corners=include_corners)}
            for model_index, rectangles in enumerate(models)
        ],
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
