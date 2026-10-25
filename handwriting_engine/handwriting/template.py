"""One-time calibration sheet. The student fills each labeled cell with the Pencil (or pen), then we extract.

Rows that contain punctuation start with the anchor letters "xn": they sit on the baseline, which is how
the extractor measures where the baseline is for rows that have no other baseline letters."""
from __future__ import annotations

import json

from PIL import Image, ImageDraw, ImageFont

LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = LOWER.upper()
DIGITS = "0123456789"
PUNCT_1 = "xn" + ".,;:!?'\"-()"
PUNCT_2 = "xn" + "[]/+=<>*%&#@_•→←~"


def draw_label(d: ImageDraw.ImageDraw, x: int, y: int, ch: str, font, color) -> None:
    """Corner label for a cell. PIL's default font has no glyphs for the bullet and arrows (they showed up as
    empty boxes) and renders "~" as a speck, so those are drawn as small shapes instead of text."""
    cy = y + 9
    if ch == "\u2022":                                   # bullet
        d.ellipse([x + 2, cy - 4, x + 10, cy + 4], fill=color)
    elif ch in "\u2192\u2190":                           # right / left arrow
        a, b, tip = (x, x + 18, 1) if ch == "\u2192" else (x + 18, x, -1)
        d.line([a, cy, b, cy], fill=color, width=2)
        d.line([b, cy, b - 6 * tip, cy - 5], fill=color, width=2)
        d.line([b, cy, b - 6 * tip, cy + 5], fill=color, width=2)
    elif ch == "~":                                       # tilde
        d.line([x, cy + 2, x + 5, cy - 3, x + 10, cy + 2, x + 15, cy - 3], fill=color, width=2)
    else:
        d.text((x, y), ch, fill=color, font=font)


def template_rows(letter_reps: int = 2) -> list[str]:
    return [LOWER] * letter_reps + [UPPER] * letter_reps + [DIGITS] * letter_reps + [PUNCT_1, PUNCT_2]


def make_template(png_path: str, rows_json_path: str, letter_reps: int = 2, cell_w: int = 84, row_h: int = 120,
                  rows: list[str] | None = None):
    """Draw the sheet. Each cell is one box: write the character on the dashed baseline; the pale shaded strip
    underneath is for the tails of g, j, p, q, y, so it reads as part of the cell rather than a separate row.
    (All guide colours stay light enough that the extractor treats them as "not ink".)"""
    rows = rows if rows is not None else template_rows(letter_reps)
    cols = max(len(r) for r in rows)
    img = Image.new("RGB", (cols * cell_w, len(rows) * row_h), "white")
    d = ImageDraw.Draw(img)
    try:
        label_font = ImageFont.load_default(size=15)
    except TypeError:
        label_font = ImageFont.load_default()
    box, guide, label, tint = (190, 205, 235), (172, 188, 232), (195, 205, 235), (242, 245, 252)
    base_y = 86
    for ri, row in enumerate(rows):
        y0 = ri * row_h
        for ci, ch in enumerate(row):
            x0 = ci * cell_w
            d.rectangle([x0, y0 + base_y, x0 + cell_w, y0 + row_h], fill=tint)          # tails zone
        for ci, ch in enumerate(row):
            x0 = ci * cell_w
            d.rectangle([x0, y0, x0 + cell_w, y0 + row_h], outline=box, width=2)
            for x in range(x0 + 4, x0 + cell_w - 4, 12):                                  # dashed baseline
                d.line([x, y0 + base_y, min(x + 7, x0 + cell_w - 4), y0 + base_y], fill=guide, width=2)
            draw_label(d, x0 + 6, y0 + 4, ch, label_font, label)
    img.save(png_path)
    with open(rows_json_path, "w") as f:
        json.dump({"rows": rows}, f, ensure_ascii=False)
    return rows
