#!/usr/bin/env python3
"""Bisect the "Upload to Imgur" crash. Round 2: split the second half.

Round 1 result: the first half (Imgur A — pick image, convert) OPENED; the
second half (Imgur B — upload + menu) CRASHED. So the culprit is in the second
half. This round cuts that second half in two, same header, each a real
openable shortcut.

  B1 — the upload: the If that picks anonymous-vs-keyed, the two Get-Contents-of-
       URL requests (Form body with the image as a File field), the two
       dictionary lookups (data -> link), and the failure alert. 14 actions.

  B2 — the menu: Choose from Menu, Copy to Clipboard + notification on one
       branch, Generate QR Code + Save to Photo Album + notification on the
       other. 9 actions.

B1 followed by B2 is byte-for-byte the second half (Imgur B). Open both:

  B1 crashes -> the fault is in the upload actions (downloadurl with a Form/File
                body, getvalueforkey, alert/exit). Split B1 next.
  B2 crashes -> the fault is in the menu actions (choosefrommenu, notification,
                generatebarcode, savetocameraroll). Split B2 next.
  both crash -> each half has an issue, or a shared construct does; I cut the
                simpler one first.

Only OPEN them; the crash is on open. Neither uploads. They reference variables
the first half set (Upload, ClientID, Link); undefined here, which only matters
if run, not opened.

Run from anywhere:

    python3 shortcuts/_imgur-ladder/build.py [OUTPUT_DIR]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "imgur-upload"))

from shortcut_builder import shortcut, write_shortcut  # noqa: E402

import build as imgur  # noqa: E402  (the real shortcut's action builders)

NAME_B1 = "Imgur B1.shortcut"
NAME_B2 = "Imgur B2.shortcut"

# Same icon as the working Clipboard to TXT shortcut.
GLYPH = 59511
COLOR = 4251333119


def build_b1():
    """The upload half of B: HTTP request(s), dictionary lookups, failure alert."""
    return shortcut(imgur.upload(), glyph_number=GLYPH, start_color=COLOR)


def build_b2():
    """The menu half of B: Choose from Menu, clipboard/notification, QR/save."""
    return shortcut(imgur.choose_output(), glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, NAME_B1), build_b1())
    write_shortcut(os.path.join(out_dir, NAME_B2), build_b2())
