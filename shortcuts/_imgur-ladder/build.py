#!/usr/bin/env python3
"""Bisect the "Upload to Imgur" crash. Round 3: split the upload half.

Trail so far:
  Round 1 — first half opened, second half crashed.
  Round 2 — B1 (the upload) crashed, B2 (the menu) opened.
So the crash is inside the upload block. This round cuts that block at its one
clean seam: the HTTP request, then the response parsing.

  B1a — the request: the If that chooses anonymous vs client-ID, and inside it
        the two Get-Contents-of-URL actions whose body is a Form with the image
        as a File field (WFItemType 5). This is the construct nothing else in
        this repo uses, and the prime suspect.

  B1b — the parse: Get Dictionary Value for `data`, then for `link`, Set
        Variable, and the "no link -> alert, stop" If.

B1a then B1b is byte-for-byte the upload block. Open both:

  B1a crashes -> it is the Form/File request body. That is almost certainly the
                 bug; next I fix how that field is serialized (test a plain
                 request, then the File field alone).
  B1b crashes -> it is Get Dictionary Value or the alert/exit. Split B1b.

Only OPEN them; the crash is on open. Neither uploads. They reference variables
the earlier halves set (Upload, ClientID, Response); undefined here, which only
matters if run.

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

NAME_B1A = "Imgur B1a.shortcut"
NAME_B1B = "Imgur B1b.shortcut"

GLYPH = 59511
COLOR = 4251333119


def _split_upload():
    """Cut the real upload() action list at the end of its auth If block.

    Slicing the actual list (rather than rebuilding) guarantees each sub-half is
    byte-for-byte what the real shortcut contains.
    """
    acts = imgur.upload()
    seam = None
    for i, a in enumerate(acts):
        p = a["WFWorkflowActionParameters"]
        if (
            p.get("GroupingIdentifier") == imgur.G_AUTH
            and p.get("WFControlFlowMode") == 2
        ):
            seam = i + 1
            break
    assert seam is not None, "auth If end marker not found"
    return acts[:seam], acts[seam:]


REQUEST, PARSE = _split_upload()


def build_b1a():
    return shortcut(REQUEST, glyph_number=GLYPH, start_color=COLOR)


def build_b1b():
    return shortcut(PARSE, glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, NAME_B1A), build_b1a())
    write_shortcut(os.path.join(out_dir, NAME_B1B), build_b1b())
