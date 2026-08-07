#!/usr/bin/env python3
"""Build the "Clipboard to TXT" shortcuts.

Two variants of the same idea:

  Clipboard to TXT.shortcut
      Turns the clipboard text into a file in memory and shares it. Nothing is
      written to Files. The trick is Base64 encode -> Base64 decode: the decode
      step hands back a data blob rather than a string, and naming that blob
      `Clipboard.txt` is what makes the share sheet treat it as a text file.

  Clipboard to TXT (Save to Files).shortcut
      Writes /Shortcuts/Clipboard.txt in iCloud Drive, reads it back, shares it.
      Slower and it leaves a file behind, but it hands the share sheet a real
      on-disk file, which is the more predictable path if an uncooperative
      target app ignores the in-memory variant.

Run from anywhere:

    python3 shortcuts/clipboard-to-txt/build.py [OUTPUT_DIR]

OUTPUT_DIR defaults to this directory, which is where the committed copies the
README links to live. CI passes build/unsigned instead so the signing step has
somewhere to read from without touching the committed files.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from shortcut_builder import action, shortcut, text_with_variable, write_shortcut

HERE = os.path.dirname(os.path.abspath(__file__))

# Fixed so rebuilds are byte-identical instead of churning the diff.
CLIPBOARD_UUID = "5B0F1C8A-0F7E-4D3E-9E4B-1B1A2C3D4E5F"

FILENAME = "Clipboard.txt"
ICLOUD_PATH = "Shortcuts/" + FILENAME

# Document glyph, orange.
GLYPH = 59511
COLOR = 4251333119


def get_clipboard_as_text():
    """Get Clipboard, then funnel it through a Text action.

    The Text action is not redundant: it coerces whatever the clipboard holds
    into a string, so a copied URL or rich text lands in the .txt as plain text
    instead of being carried along as its original content type.
    """
    return [
        action("is.workflow.actions.getclipboard", uuid=CLIPBOARD_UUID),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": text_with_variable(CLIPBOARD_UUID, "Clipboard")},
        ),
    ]


def set_name_and_share():
    return [
        action(
            "is.workflow.actions.setitemname",
            {"WFName": FILENAME, "WFDontIncludeFileExtension": False},
        ),
        action("is.workflow.actions.share", {}),
    ]


def build_in_memory():
    actions = get_clipboard_as_text()
    actions += [
        action(
            "is.workflow.actions.base64encode",
            {"WFEncodeMode": "Encode", "WFBase64LineBreakMode": "None"},
        ),
        action("is.workflow.actions.base64encode", {"WFEncodeMode": "Decode"}),
    ]
    actions += set_name_and_share()
    return shortcut(actions, glyph_number=GLYPH, start_color=COLOR)


def build_save_to_files():
    actions = get_clipboard_as_text()
    actions += [
        action(
            "is.workflow.actions.documentpicker.save",
            {
                "WFFileDestinationPath": ICLOUD_PATH,
                "WFAskWhereToSave": False,
                "WFSaveFileOverwrite": True,
            },
        ),
        action(
            "is.workflow.actions.documentpicker.open",
            {
                "WFGetFilePath": ICLOUD_PATH,
                "WFShowFilePicker": False,
                "WFFileErrorIfNotFound": True,
            },
        ),
    ]
    actions += set_name_and_share()
    return shortcut(actions, glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, "Clipboard to TXT.shortcut"), build_in_memory())
    write_shortcut(
        os.path.join(out_dir, "Clipboard to TXT (Save to Files).shortcut"),
        build_save_to_files(),
    )
