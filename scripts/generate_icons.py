#!/usr/bin/env python3
"""Generate opaque-to-edge PNG icons with no white matte."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflow"
ICONS = WORKFLOW / "icons"

SCALE = 4


def _canvas(size: int, fill: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (size * SCALE, size * SCALE), fill)


def _down(im: Image.Image, size: int) -> Image.Image:
    return im.resize((size, size), Image.Resampling.LANCZOS)


def _save(im: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="PNG", optimize=True)
    print(f"wrote {path} {im.mode} {im.size}")


def _speaker(
    draw: ImageDraw.ImageDraw, cx: float, cy: float, unit: float, color: tuple[int, int, int, int]
) -> None:
    # Body: rounded rectangle + horn trapezoid, then three wave arcs.
    body_w, body_h = unit * 0.42, unit * 0.55
    body = [
        cx - unit * 0.72,
        cy - body_h / 2,
        cx - unit * 0.72 + body_w,
        cy + body_h / 2,
    ]
    draw.rounded_rectangle(body, radius=unit * 0.08, fill=color)

    horn = [
        (cx - unit * 0.34, cy - body_h * 0.28),
        (cx + unit * 0.02, cy - unit * 0.62),
        (cx + unit * 0.02, cy + unit * 0.62),
        (cx - unit * 0.34, cy + body_h * 0.28),
    ]
    draw.polygon(horn, fill=color)

    origin = (cx + unit * 0.08, cy)
    for radius in (unit * 0.28, unit * 0.48, unit * 0.68):
        bbox = [
            origin[0] - radius,
            origin[1] - radius,
            origin[0] + radius,
            origin[1] + radius,
        ]
        width = max(int(unit * 0.09), 6)
        draw.arc(bbox, start=-48, end=48, fill=color, width=width)


def _sparkle(
    draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color: tuple[int, int, int, int]
) -> None:
    pts: list[tuple[float, float]] = []
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        rad = r if i % 2 == 0 else r * 0.38
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    draw.polygon(pts, fill=color)


def _wave(
    draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float, color: tuple[int, int, int, int]
) -> None:
    width = max(int(h * 0.22), 6)
    path = [
        (x, y),
        (x + w * 0.22, y - h),
        (x + w * 0.44, y + h * 0.15),
        (x + w * 0.66, y - h * 0.55),
        (x + w, y),
    ]
    draw.line(path, fill=color, width=width, joint="curve")


def make_main(size: int = 256) -> Image.Image:
    fill = (38, 42, 47, 255)
    accent = (45, 212, 196, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    _speaker(draw, s * 0.46, s * 0.50, s * 0.38, accent)
    return _down(im, size)


def make_edge(size: int = 128) -> Image.Image:
    fill = (106, 138, 196, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    _speaker(draw, s * 0.46, s * 0.50, s * 0.40, (255, 255, 255, 255))
    return _down(im, size)


def make_gemini(size: int = 128) -> Image.Image:
    fill = (74, 48, 128, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    _sparkle(draw, s * 0.50, s * 0.42, s * 0.28, white)
    _wave(draw, s * 0.22, s * 0.78, s * 0.56, s * 0.08, white)
    return _down(im, size)


def make_openai(size: int = 128) -> Image.Image:
    fill = (16, 140, 110, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    _sparkle(draw, s * 0.50, s * 0.46, s * 0.30, white)
    return _down(im, size)


def make_elevenlabs(size: int = 128) -> Image.Image:
    fill = (176, 48, 92, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    bar_w = s * 0.14
    gap = s * 0.10
    x0 = s * 0.31
    for i, h in enumerate((0.46, 0.62)):
        x = x0 + i * (bar_w + gap)
        top = s * 0.50 - s * h / 2
        draw.rounded_rectangle([x, top, x + bar_w, top + s * h], radius=bar_w / 2, fill=white)
    return _down(im, size)


def make_deepgram(size: int = 128) -> Image.Image:
    fill = (28, 102, 108, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    cx, cy = s * 0.50, s * 0.50
    for i, r in enumerate((s * 0.34, s * 0.22, s * 0.10)):
        width = max(int(s * 0.055), 6) if i < 2 else 0
        bbox = [cx - r, cy - r, cx + r, cy + r]
        if i < 2:
            draw.ellipse(bbox, outline=white, width=width)
        else:
            draw.ellipse(bbox, fill=white)
    return _down(im, size)


def make_xai(size: int = 128) -> Image.Image:
    fill = (48, 50, 58, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    width = max(int(s * 0.12), 10)
    pad = s * 0.28
    draw.line([(pad, pad), (s - pad, s - pad)], fill=white, width=width)
    draw.line([(s - pad, pad), (pad, s - pad)], fill=white, width=width)
    return _down(im, size)


def make_aliyun(size: int = 128) -> Image.Image:
    fill = (214, 98, 28, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    _wave(draw, s * 0.18, s * 0.42, s * 0.64, s * 0.10, white)
    _wave(draw, s * 0.18, s * 0.62, s * 0.64, s * 0.10, white)
    return _down(im, size)


def make_volcengine(size: int = 128) -> Image.Image:
    fill = (32, 92, 196, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    peak = [
        (s * 0.50, s * 0.18),
        (s * 0.82, s * 0.78),
        (s * 0.18, s * 0.78),
    ]
    draw.polygon(peak, fill=white)
    crater = [
        (s * 0.50, s * 0.38),
        (s * 0.62, s * 0.62),
        (s * 0.38, s * 0.62),
    ]
    draw.polygon(crater, fill=fill)
    return _down(im, size)


def make_kokoro(size: int = 128) -> Image.Image:
    fill = (196, 90, 48, 255)
    white = (255, 255, 255, 255)
    im = _canvas(size, fill)
    draw = ImageDraw.Draw(im)
    s = size * SCALE
    # Equalizer bars + a small node, matching the previous motif without the white plate.
    bars = (0.18, 0.42, 0.70, 0.34)
    gap = s * 0.08
    bar_w = s * 0.10
    x0 = s * 0.18
    base = s * 0.78
    for i, h in enumerate(bars):
        x = x0 + i * (bar_w + gap)
        top = base - s * h
        draw.rounded_rectangle([x, top, x + bar_w, base], radius=bar_w / 2, fill=white)
    node_r = s * 0.055
    draw.ellipse(
        [s * 0.78 - node_r, s * 0.32 - node_r, s * 0.78 + node_r, s * 0.32 + node_r],
        fill=white,
    )
    draw.ellipse(
        [s * 0.88 - node_r, s * 0.48 - node_r, s * 0.88 + node_r, s * 0.48 + node_r],
        fill=white,
    )
    draw.line([(s * 0.78, s * 0.32), (s * 0.88, s * 0.48)], fill=white, width=max(int(s * 0.035), 4))
    return _down(im, size)


def main() -> None:
    _save(make_main(256), WORKFLOW / "icon.png")
    _save(make_edge(128), ICONS / "edge.png")
    _save(make_gemini(128), ICONS / "gemini.png")
    _save(make_openai(128), ICONS / "openai.png")
    _save(make_elevenlabs(128), ICONS / "elevenlabs.png")
    _save(make_deepgram(128), ICONS / "deepgram.png")
    _save(make_xai(128), ICONS / "xai.png")
    _save(make_aliyun(128), ICONS / "aliyun.png")
    _save(make_volcengine(128), ICONS / "volcengine.png")
    _save(make_kokoro(128), ICONS / "kokoro.png")


if __name__ == "__main__":
    main()
