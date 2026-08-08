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

from shortcut_builder import (
    action,
    action_output_input,
    shortcut,
    text_with_variable,
    write_shortcut,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# Fixed UUIDs so rebuilds are byte-identical. Each action that produces a value
# a later action consumes needs a stable UUID to be referenced by.
U_CLIPBOARD = "5B0F1C8A-0F7E-4D3E-9E4B-1B1A2C3D4E5F"
U_TEXT = "5B0F1C8A-0F7E-4D3E-9E4B-2B1A2C3D4E5F"
U_ENCODE = "5B0F1C8A-0F7E-4D3E-9E4B-3B1A2C3D4E5F"
U_DECODE = "5B0F1C8A-0F7E-4D3E-9E4B-4B1A2C3D4E5F"
U_SAVE = "5B0F1C8A-0F7E-4D3E-9E4B-5B1A2C3D4E5F"
U_OPEN = "5B0F1C8A-0F7E-4D3E-9E4B-6B1A2C3D4E5F"
U_NAME = "5B0F1C8A-0F7E-4D3E-9E4B-7B1A2C3D4E5F"

FILENAME = "Clipboard.txt"
ICLOUD_PATH = "Shortcuts/" + FILENAME

# Document glyph, orange.
GLYPH = 59511
COLOR = 4251333119


def get_clipboard_as_text():
    """Get Clipboard, then coerce it to a string through a Text action.

    The Text action isn't redundant: it flattens a copied URL or rich text to
    plain text, so the file ends up as real .txt rather than the original type.
    Inputs are wired explicitly (WFInput / WFTextActionText) the way real
    serialized shortcuts do, not left to the app's implicit output chaining.
    """
    return [
        action("is.workflow.actions.getclipboard", uuid=U_CLIPBOARD),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": text_with_variable(U_CLIPBOARD, "Clipboard")},
            uuid=U_TEXT,
        ),
    ]


def set_name_and_share(input_uuid, input_name):
    return [
        action(
            "is.workflow.actions.setitemname",
            {
                "WFInput": action_output_input(input_uuid, input_name),
                "WFName": FILENAME,
                "WFDontIncludeFileExtension": False,
            },
            uuid=U_NAME,
        ),
        action(
            "is.workflow.actions.share",
            {"WFInput": action_output_input(U_NAME, "Renamed Item")},
        ),
    ]


def build_in_memory():
    actions = get_clipboard_as_text()
    actions += [
        action(
            "is.workflow.actions.base64encode",
            {
                "WFInput": action_output_input(U_TEXT, "Text"),
                "WFEncodeMode": "Encode",
                "WFBase64LineBreakMode": "None",
            },
            uuid=U_ENCODE,
        ),
        action(
            "is.workflow.actions.base64encode",
            {
                "WFInput": action_output_input(U_ENCODE, "Base64 Encoded"),
                "WFEncodeMode": "Decode",
            },
            uuid=U_DECODE,
        ),
    ]
    actions += set_name_and_share(U_DECODE, "Base64 Encoded")
    return shortcut(actions, glyph_number=GLYPH, start_color=COLOR)


def build_save_to_files():
    actions = get_clipboard_as_text()
    actions += [
        action(
            "is.workflow.actions.documentpicker.save",
            {
                "WFInput": action_output_input(U_TEXT, "Text"),
                "WFFileDestinationPath": ICLOUD_PATH,
                "WFAskWhereToSave": False,
                "WFSaveFileOverwrite": True,
            },
            uuid=U_SAVE,
        ),
        action(
            "is.workflow.actions.documentpicker.open",
            {
                "WFGetFilePath": ICLOUD_PATH,
                "WFShowFilePicker": False,
                "WFFileErrorIfNotFound": True,
            },
            uuid=U_OPEN,
        ),
    ]
    actions += set_name_and_share(U_OPEN, "File")
    return shortcut(actions, glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, "Clipboard to TXT.shortcut"), build_in_memory())
    write_shortcut(
        os.path.join(out_dir, "Clipboard to TXT (Save to Files).shortcut"),
        build_save_to_files(),
    )
