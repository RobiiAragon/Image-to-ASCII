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


def load(path: Path, width: int) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("RGB")
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


def to_html(chars: list[list[str]], img: Image.Image) -> str:
    rgb = img.load()
    rows = []
    for y, row in enumerate(chars):
        rows.append("".join(
            f'<span style="color:rgb{rgb[x, y]}">{html.escape(c)}</span>' for x, c in enumerate(row)))
    body = "\n".join(rows)
    return ("<!doctype html><meta charset=utf-8><title>ASCII art</title>"
            "<body style=\"background:#0d1117;margin:0;padding:16px\">"
            f"<pre style=\"font:8px/8px ui-monospace,Menlo,Consolas,monospace\">{body}</pre>")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert an image to ASCII art.")
    p.add_argument("image", nargs="?", type=Path, help="path to the image (asks if omitted)")
    p.add_argument("-w", "--width", type=int, default=100, help="output width in characters (default: 100)")
    p.add_argument("-r", "--ramp", choices=RAMPS, default="classic", help="character set (default: classic)")
    p.add_argument("-i", "--invert", action="store_true", help="invert brightness (for white backgrounds / printing)")
    p.add_argument("-o", "--output", type=Path, help="save to a .txt or .html file (html keeps the colors)")
    p.add_argument("-q", "--quiet", action="store_true", help="don't print to the terminal")
    args = p.parse_args(argv)

    path = args.image or Path(input("Image path: ").strip().strip('"'))
    try:
        img = load(path, max(10, args.width))
    except (OSError, ValueError) as e:
        print(f"error: can't open {path}: {e}", file=sys.stderr)
        return 1

    chars = to_ascii(img, RAMPS[args.ramp], args.invert)
    text = "\n".join("".join(r) for r in chars)

    if args.output:
        out = to_html(chars, img) if args.output.suffix.lower() in {".html", ".htm"} else text
        args.output.write_text(out, encoding="utf-8")
        print(f"saved → {args.output}", file=sys.stderr)
    if not args.quiet:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
