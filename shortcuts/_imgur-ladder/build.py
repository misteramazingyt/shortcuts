#!/usr/bin/env python3
"""Verify the crash fix. Round 5: the File form field, corrected.

The bisect ended at B1a-3: the image sent as a Form File field (WFItemType 5)
crashed the app on open, while the same request as a text field (B1a-2) opened.
Ground truth (the julian-englert/apple-shortcuts decompiler notes' Whisper-API
upload) shows a File field's WFValue is doubly wrapped — a
WFTokenAttachmentParameterState around the WFTextTokenAttachment — and the old
file_item emitted only the inner layer. tools/shortcut_builder.py is now fixed.

This builds ONE shortcut: the exact B1a-3 request (single POST, Form body, image
as a File field, no headers) with the corrected serialization. If it OPENS, the
File field is fixed — and because the real Upload to Imgur uses the same
file_item, the real shortcut is fixed too.

Only OPEN it; the crash is on open. It does not upload (the image variable is
undefined here).

Run from anywhere:

    python3 shortcuts/_imgur-ladder/build.py [OUTPUT_DIR]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "imgur-upload"))

from shortcut_builder import (  # noqa: E402
    action,
    dictionary_value,
    file_item,
    shortcut,
    text_item,
    variable_ref,
    write_shortcut,
)

import build as imgur  # noqa: E402

NAME = "Imgur File Fixed.shortcut"
GLYPH = 59511
COLOR = 4251333119
U_HTTP = "5D0F1C8A-0F7E-4D3E-9E4B-0111A2C3D4E5"


def build():
    a = action(
        "is.workflow.actions.downloadurl",
        {
            "WFURL": imgur.ENDPOINT,
            "WFHTTPMethod": "POST",
            "WFHTTPBodyType": "Form",
            "WFFormValues": dictionary_value(
                [
                    file_item("image", variable_ref(imgur.V_UPLOAD)),
                    text_item("type", "file"),
                ]
            ),
            "ShowHeaders": False,
        },
        uuid=U_HTTP,
    )
    return shortcut([a], glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, NAME), build())
