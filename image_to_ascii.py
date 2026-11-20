#!/usr/bin/env python3
"""Image to ASCII — turn any image into ASCII art in your terminal, a .txt or a colored .html.

By Jesús Aragón · https://github.com/RobiiAragon
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

from PIL import Image, ImageOps

# Character ramps, from densest to emptiest.
RAMPS = {
    "classic": "@%#*+=-:. ",
    "detailed": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    "blocks": "█▓▒░ ",
}
CHAR_ASPECT = 0.5  # terminal characters are about twice as tall as they are wide


def load(path: Path, width: int, background: tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    img = ImageOps.exif_transpose(Image.open(path))
    # 16/32-bit grayscale (e.g. 16-bit PNGs) would clip to white when converted
    # straight to RGB, so scale it down to 8 bits first.
    if img.mode in ("I", "I;16", "I;16B", "I;16L", "F"):
        lo, hi = img.getextrema()
        scale = 255 / (hi - lo) if hi > lo else 0
        img = img.point(lambda v: (v - lo) * scale).convert("L")
    # Flatten transparency onto the background, otherwise the hidden RGB values
    # under transparent pixels (often white) show up as solid characters.
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        img = img.convert("RGBA")
        img = Image.alpha_composite(Image.new("RGBA", img.size, (*background, 255)), img)
    img = img.convert("RGB")
    height = max(1, round(img.height / img.width * width * CHAR_ASPECT))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def to_ascii(img: Image.Image, ramp: str, invert: bool = False) -> list[list[str]]:
    # Dark terminals: dark pixels become empty space. --invert flips it for light backgrounds.
    if not invert:
        ramp = ramp[::-1]
    gray = img.convert("L")
    last = len(ramp) - 1
    px = gray.load()
    return [[ramp[px[x, y] * last // 255] for x in range(gray.width)] for y in range(gray.height)]


def _runs(row: list[str], colors: list[tuple[int, int, int]]):
    """Group consecutive characters that share a color, so we emit one tag per run."""
    start = 0
    for x in range(1, len(row) + 1):
        if x == len(row) or colors[x] != colors[start]:
            yield "".join(row[start:x]), colors[start]
            start = x


def _row_colors(img: Image.Image, y: int) -> list[tuple[int, int, int]]:
    rgb = img.load()
    return [rgb[x, y] for x in range(img.width)]


def to_html(chars: list[list[str]], img: Image.Image, light: bool = False) -> str:
    rows = []
    for y, row in enumerate(chars):
        rows.append("".join(
            f'<span style="color:#{r:02x}{g:02x}{b:02x}">{html.escape(text)}</span>'
            for text, (r, g, b) in _runs(row, _row_colors(img, y))))
    body = "\n".join(rows)
    bg = "#ffffff" if light else "#0d1117"
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>ASCII art</title></head>\n"
            f"<body style=\"background:{bg};margin:0;padding:16px\">"
            f"<pre style=\"font:8px/8px ui-monospace,Menlo,Consolas,monospace\">{body}</pre>"
            "</body></html>\n")


def to_ansi(chars: list[list[str]], img: Image.Image) -> str:
    """24-bit color escape codes for terminals that support truecolor."""
    lines = []
    for y, row in enumerate(chars):
        lines.append("".join(f"\x1b[38;2;{r};{g};{b}m{text}"
                             for text, (r, g, b) in _runs(row, _row_colors(img, y))) + "\x1b[0m")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert an image to ASCII art.")
    p.add_argument("image", nargs="?", type=Path, help="path to the image (asks if omitted)")
    p.add_argument("-w", "--width", type=int, default=100, help="output width in characters (default: 100)")
    p.add_argument("-r", "--ramp", choices=RAMPS, default="classic", help="character set (default: classic)")
    p.add_argument("-i", "--invert", action="store_true", help="invert brightness (for white backgrounds / printing)")
    p.add_argument("-o", "--output", type=Path, help="save to a .txt or .html file (html keeps the colors)")
    p.add_argument("-c", "--color", action="store_true", help="print in 24-bit color (truecolor terminals)")
    p.add_argument("-q", "--quiet", action="store_true", help="don't print to the terminal")
    args = p.parse_args(argv)

    if args.image is None:
        try:
            args.image = Path(input("Image path: ").strip().strip('"\''))
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            return 1
    path = args.image
    try:
        img = load(path, max(10, args.width), (255, 255, 255) if args.invert else (0, 0, 0))
    except (OSError, ValueError, Image.DecompressionBombError) as e:
        print(f"error: can't open {path}: {e}", file=sys.stderr)
        return 1

    chars = to_ascii(img, RAMPS[args.ramp], args.invert)
    text = "\n".join("".join(r) for r in chars)

    if args.output:
        out = to_html(chars, img, args.invert) if args.output.suffix.lower() in {".html", ".htm"} else text + "\n"
        try:
            args.output.write_text(out, encoding="utf-8")
        except OSError as e:
            print(f"error: can't write {args.output}: {e}", file=sys.stderr)
            return 1
        print(f"saved -> {args.output}", file=sys.stderr)
    if not args.quiet:
        # Windows consoles may not be UTF-8; never crash on the block characters.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        print(to_ansi(chars, img) if args.color else text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
