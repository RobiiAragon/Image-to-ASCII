import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import image_to_ascii as ita  # noqa: E402


def save(tmp_path, img, name="in.png"):
    p = tmp_path / name
    img.save(p)
    return p


def test_aspect_ratio_halves_height(tmp_path):
    p = save(tmp_path, Image.new("RGB", (200, 100), "white"))
    img = ita.load(p, 40)
    assert img.size == (40, 10)


def test_dark_pixels_are_blank_by_default(tmp_path):
    p = save(tmp_path, Image.new("RGB", (10, 10), "black"))
    chars = ita.to_ascii(ita.load(p, 10), ita.RAMPS["classic"])
    assert {c for row in chars for c in row} == {" "}


def test_invert_flips_ramp(tmp_path):
    p = save(tmp_path, Image.new("RGB", (10, 10), "black"))
    chars = ita.to_ascii(ita.load(p, 10), ita.RAMPS["classic"], invert=True)
    assert {c for row in chars for c in row} == {"@"}


def test_transparent_pixels_use_background(tmp_path):
    # Fully transparent white must not become solid characters.
    p = save(tmp_path, Image.new("RGBA", (10, 10), (255, 255, 255, 0)))
    chars = ita.to_ascii(ita.load(p, 10), ita.RAMPS["classic"])
    assert {c for row in chars for c in row} == {" "}


def test_16bit_grayscale_is_not_clipped(tmp_path):
    img = Image.new("I;16", (20, 10))
    img.paste(30000, (10, 0, 20, 10))
    p = save(tmp_path, img)
    gray = ita.load(p, 20).convert("L")
    assert gray.getpixel((0, 0)) < 20 and gray.getpixel((19, 0)) > 235


def test_html_groups_color_runs_and_escapes(tmp_path):
    p = save(tmp_path, Image.new("RGB", (10, 10), (255, 0, 0)))
    img = ita.load(p, 10)
    chars = [["<"] * img.width for _ in range(img.height)]
    out = ita.to_html(chars, img)
    assert out.count("<span") == img.height  # one span per row, not per character
    assert "&lt;" in out and "#ff0000" in out
    assert "#ffffff" in ita.to_html(chars, img, light=True)


def test_ansi_output_resets_color(tmp_path):
    p = save(tmp_path, Image.new("RGB", (10, 10), (0, 128, 255)))
    img = ita.load(p, 10)
    out = ita.to_ansi(ita.to_ascii(img, ita.RAMPS["blocks"]), img)
    assert "\x1b[38;2;0;128;255m" in out
    assert all(line.endswith("\x1b[0m") for line in out.splitlines())


def test_cli_writes_txt_and_html(tmp_path, capsys):
    p = save(tmp_path, Image.new("RGB", (64, 32), "gray"))
    assert ita.main([str(p), "-w", "20", "-o", str(tmp_path / "a.txt"), "-q"]) == 0
    assert len((tmp_path / "a.txt").read_text(encoding="utf-8").splitlines()) == 5
    assert ita.main([str(p), "-w", "20", "-o", str(tmp_path / "a.html"), "-q"]) == 0
    assert (tmp_path / "a.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert capsys.readouterr().out == ""


def test_cli_missing_file_returns_error(tmp_path, capsys):
    assert ita.main([str(tmp_path / "nope.png")]) == 1
    assert "can't open" in capsys.readouterr().err


@pytest.mark.parametrize("ramp", sorted(ita.RAMPS))
def test_every_ramp_runs(tmp_path, ramp, capsys):
    p = save(tmp_path, Image.linear_gradient("L").convert("RGB"))
    assert ita.main([str(p), "-w", "30", "-r", ramp, "-c"]) == 0
    assert capsys.readouterr().out
