"""Minimal shapes and geometry helpers for turtle_commander.

Contains only what's needed: circle_points, arc_points, star_points,
px_to_units, and SHAPES for aquarius, rainbow, and cap.
"""

import math
from typing import List, Tuple

Point = Tuple[float, float]


def circle_points(cx: float, cy: float, r: float, n: int = 60) -> List[Point]:
    return [
        (cx + r * math.cos(2 * math.pi * i / n),
         cy + r * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def arc_points(cx: float, cy: float, r: float, start_rad: float, end_rad: float, n: int = 48) -> List[Point]:
    while end_rad < start_rad:
        end_rad += 2 * math.pi
    span = end_rad - start_rad
    steps = max(2, int(n * span / (2 * math.pi)))
    return [
        (cx + r * math.cos(start_rad + span * i / steps),
         cy + r * math.sin(start_rad + span * i / steps))
        for i in range(steps + 1)
    ]


def star_points(cx: float, cy: float, r_outer: float, r_inner: float, rotation: float = math.radians(-90)) -> List[Point]:
    pts: List[Point] = []
    for i in range(10):
        ang = rotation + i * math.pi / 5.0
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def px_to_units(x_px: float, y_px: float, width_px: float = 500.0, height_px: float = 500.0, world: float = 11.0) -> Point:
    sx = world / width_px
    sy = world / height_px
    return x_px * sx, y_px * sy


SHAPES = {
    "aquarius": {
        "left_px": 90.0,
        "right_px": 410.0,
        "y_top_px": 290.0,
        "y_bottom_px": 220.0,
        "amplitude_px": 24.0,
        "wavelength_px": 120.0,
        "stroke_px": 16,
        "color": (212, 175, 55),
    },
    "rainbow": {
        "center_px": (250.0, 130.0),
        "outer_radius_px": 220.0,
        "band_thickness_px": 24.0,
        "colors": [
            (255, 0, 0),
            (255, 127, 0),
            (255, 255, 0),
            (0, 255, 0),
            (0, 0, 255),
            (75, 0, 130),
            (148, 0, 211),
        ],
    },
    "cap": {
        "center": (5.5, 5.5),
        "radii": [3.9, 3.1, 2.3, 1.5],
    },
}
