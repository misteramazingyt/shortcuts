#!/usr/bin/env python3
"""Cut the real "Upload to Imgur" shortcut in half to bisect its crash.

The shortcut crashes the Shortcuts app on open and I cannot test on a device.
So this takes the ACTUAL action list of Upload to Imgur and splits it in two
contiguous halves at a clean block boundary. Each half is a real, openable
shortcut on the same header the working shortcuts here use.

  A — the FIRST half: everything up to and including deciding what to upload.
      client-ID text + Set Variable, pick the image (If on Shortcut Input),
      convert to JPEG if it is HEIC (If on the extension). Ends with the
      Upload variable chosen.

  B — the SECOND half: the upload itself (the Form request with the image as a
      File field, the two dictionary lookups, the failure alert) and the menu
      (Copy Link / Save QR Code with its notification and QR actions).

Open both. Whichever crashes contains the culprit, and I split THAT half again
next round. If A opens and B crashes, the bug is in the upload/menu actions; if
A crashes, it is in the pick/convert actions. Same header on both, so the only
thing that varies is which actions are present.

The split is at a top-level boundary, so each half's If/menu blocks are whole
and balanced. B references a couple of variables the first half set (ClientID,
Upload); undefined, they make B run wrong if executed, but this test is about
OPENING, not running. Do not run them.

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

NAME_A = "Imgur A.shortcut"
NAME_B = "Imgur B.shortcut"

# Same icon as the working Clipboard to TXT shortcut.
GLYPH = 59511
COLOR = 4251333119


def first_half():
    """Actions 0..N/2 of the real shortcut, ending at a clean block boundary."""
    return imgur.client_id() + imgur.pick_image() + imgur.normalize_format()


def second_half():
    """Actions N/2..end of the real shortcut, starting at a clean block boundary."""
    return imgur.upload() + imgur.choose_output()


def build_a():
    # Legacy header, like every working shortcut here. The first half references
    # Shortcut Input, so set the flag.
    return shortcut(
        first_half(), glyph_number=GLYPH, start_color=COLOR, uses_shortcut_input=True
    )


def build_b():
    # Same header; the second half does not touch Shortcut Input.
    return shortcut(second_half(), glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, NAME_A), build_a())
    write_shortcut(os.path.join(out_dir, NAME_B), build_b())
