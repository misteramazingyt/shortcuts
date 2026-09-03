#!/usr/bin/env python3
"""Two signed rungs to bisect the "Upload to Imgur" crash on a device.

The shortcut crashes the Shortcuts app on open. I cannot test on a device, so
we bisect. Both rungs use the SAME top-level dictionary the working shortcuts
here use (legacy, client 736), so the only thing that differs between them is
how many actions they contain. That keeps the search on one axis: open both,
and whichever crashes gets split in half next.

  A — the control-flow half of the real shortcut: named variable, If/Otherwise
      on Shortcut Input, Choose from Menu, Show Notification, Show Result. No
      image work, no upload, no QR.

  B — the full "Upload to Imgur" action list (same actions as the shortcut on
      the homepage), on the same header. This is the whole thing; we expect it
      to crash, which confirms the download reproduces what you see.

The protocol:

  A opens, B crashes -> the fault is in the actions that B adds (image / upload
                        / QR). Split B: next pair adds those in halves.
  A crashes          -> a core construct (variable / If / menu) is wrong. Split
                        A: next pair pares it down toward the single culprit.
  A opens, B opens   -> the actions are all fine; the crash is something the
                        full file has that these don't (its header/size). We
                        bring in the modern-header rung next.

Only OPEN them; the crash is on open. Neither uploads anything.

Run from anywhere:

    python3 shortcuts/_imgur-ladder/build.py [OUTPUT_DIR]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "imgur-upload"))

from shortcut_builder import (  # noqa: E402
    CONDITION_HAS_ANY_VALUE,
    SHORTCUT_INPUT,
    action,
    if_else,
    if_end,
    if_start,
    menu_end,
    menu_item,
    menu_start,
    modern_shortcut,  # noqa: F401  (reserved for the A-opens-B-opens branch)
    set_variable,
    shortcut,
    text_token,
    variable_ref,
    write_shortcut,
)

import build as imgur  # noqa: E402  (the real shortcut's action builders)

NAME_A = "Imgur A.shortcut"
NAME_B = "Imgur B.shortcut"

# Same icon as the working Clipboard to TXT shortcut.
GLYPH = 59511
COLOR = 4251333119

# Fixed UUIDs and group ids keep rebuilds byte-identical.
U_TEXT = "3D0F1C8A-0F7E-4D3E-9E4B-0111A2C3D4E5"
U_NOTE = "3D0F1C8A-0F7E-4D3E-9E4B-0211A2C3D4E5"
G_INPUT = "3D0F1C8A-0F7E-4D3E-9E4B-A211A2C3D4E5"
G_MENU = "3D0F1C8A-0F7E-4D3E-9E4B-A311A2C3D4E5"


def build_a():
    """Control-flow half: named variable, If/Otherwise, menu, notification."""
    actions = [
        action(
            "is.workflow.actions.comment",
            {"WFCommentActionText": "Imgur bisect A: control flow only, legacy header."},
        ),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": "start"},
            uuid=U_TEXT,
        ),
        set_variable("Seed", (U_TEXT, "Text")),
        # If/Otherwise on Shortcut Input, a variable set in each branch.
        if_start(G_INPUT, SHORTCUT_INPUT, CONDITION_HAS_ANY_VALUE),
        set_variable("Note", SHORTCUT_INPUT),
        if_else(G_INPUT),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": "run directly, no input"},
            uuid=U_NOTE,
        ),
        set_variable("Note", (U_NOTE, "Text")),
        if_end(G_INPUT),
        # Choose from Menu with two items, each a notification.
        menu_start(G_MENU, "Imgur bisect A", ["Option A", "Option B"]),
        menu_item(G_MENU, "Option A"),
        action(
            "is.workflow.actions.notification",
            {
                "WFNotificationActionTitle": "You chose A",
                "WFNotificationActionBody": text_token(variable_ref("Note")),
                "WFNotificationActionSound": False,
            },
        ),
        menu_item(G_MENU, "Option B"),
        action(
            "is.workflow.actions.notification",
            {
                "WFNotificationActionTitle": "You chose B",
                "WFNotificationActionBody": text_token(variable_ref("Note")),
                "WFNotificationActionSound": False,
            },
        ),
        menu_end(G_MENU),
        action(
            "is.workflow.actions.showresult",
            {"Text": text_token(variable_ref("Note"))},
        ),
    ]
    # Legacy top-level, exactly like the working shortcuts here.
    return shortcut(
        actions, glyph_number=GLYPH, start_color=COLOR, uses_shortcut_input=True
    )


def build_b():
    """The full Upload to Imgur action list, on the same legacy header as A.

    Same header as A and as every working shortcut here, so the only difference
    from A is the added actions. (modern_shortcut, imported below, is held in
    reserve for the A-opens-B-opens branch, where the header becomes suspect.)
    """
    actions = (
        imgur.client_id()
        + imgur.pick_image()
        + imgur.normalize_format()
        + imgur.upload()
        + imgur.choose_output()
    )
    return shortcut(
        actions, glyph_number=GLYPH, start_color=COLOR, uses_shortcut_input=True
    )


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, NAME_A), build_a())
    write_shortcut(os.path.join(out_dir, NAME_B), build_b())
