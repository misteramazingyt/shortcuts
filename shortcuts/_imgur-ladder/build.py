#!/usr/bin/env python3
"""Build the Imgur crash ladder: seven shortcuts, each one construct bigger.

"Upload to Imgur" crashes the Shortcuts app on open, in two builds with
different menu formats, while every other shortcut in this repository opens.
Diffing them, thirteen action types in the Imgur shortcut have never appeared
in a working file here. Without a device there is no way to know which of them
the app dies on, so this ladder finds out empirically: rung 1 is the exact
skeleton of a working shortcut with the first new construct added, and each
rung after adds one more. Open them in order on the phone; the first rung that
crashes names the culprit, and the rungs before it are cleared for good.

  1  named variable          setvariable, showresult
  2  If / Otherwise           conditional (flat form), Shortcut Input reference
  3  Choose from Menu         choosefrommenu, notification
  4  image handling           selectphoto, properties.images, image.convert
  5  the upload               downloadurl with a Form body and a File field,
                              getvalueforkey, setclipboard
  6  the error path + QR      alert, exit, generatebarcode, savetocameraroll
  7  modern top-level keys    the full "Upload to Imgur v2" action list under
                              the top-level dictionary a current Shortcuts app
                              writes (client version 4033), instead of the
                              2018-era one every other file here uses

Rungs 1-6 keep the same top-level dictionary as the working shortcuts, so the
only thing that changes from one rung to the next is the actions. Rung 7 keeps
the actions and changes only the top-level.

None of these need to be *run* — the crash is on *open*. Rung 5 onwards would
upload a photo if run to the end; don't.

Run from anywhere:

    python3 shortcuts/_imgur-ladder/build.py [OUTPUT_DIR]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "imgur-upload"))

from shortcut_builder import (  # noqa: E402
    CONDITION_CONTAINS,
    CONDITION_DOES_NOT_HAVE_ANY_VALUE,
    CONDITION_HAS_ANY_VALUE,
    SHORTCUT_INPUT,
    action,
    action_output_input,
    dictionary_value,
    file_item,
    if_else,
    if_end,
    if_start,
    menu_end,
    menu_item,
    menu_start,
    modern_shortcut,
    set_variable,
    shortcut,
    text_item,
    text_token,
    text_with_variable,
    variable_input,
    variable_ref,
    write_shortcut,
)

# The real shortcut's pieces, so rung 7 is exactly its action list.
import build as imgur  # noqa: E402

NAME = "Imgur Ladder {n}.shortcut"

# Same icon as the working Clipboard to TXT shortcut.
GLYPH = 59511
COLOR = 4251333119

# Fixed UUIDs keep rebuilds byte-identical. One block per rung.
U = {
    "text": "3D0F1C8A-0F7E-4D3E-9E4B-0111A2C3D4E5",
    "note": "3D0F1C8A-0F7E-4D3E-9E4B-0211A2C3D4E5",
    "select": "3D0F1C8A-0F7E-4D3E-9E4B-0411A2C3D4E5",
    "ext": "3D0F1C8A-0F7E-4D3E-9E4B-0421A2C3D4E5",
    "convert": "3D0F1C8A-0F7E-4D3E-9E4B-0431A2C3D4E5",
    "http": "3D0F1C8A-0F7E-4D3E-9E4B-0511A2C3D4E5",
    "data": "3D0F1C8A-0F7E-4D3E-9E4B-0521A2C3D4E5",
    "link": "3D0F1C8A-0F7E-4D3E-9E4B-0531A2C3D4E5",
    "qr": "3D0F1C8A-0F7E-4D3E-9E4B-0611A2C3D4E5",
}
G = {
    "input": "3D0F1C8A-0F7E-4D3E-9E4B-A211A2C3D4E5",
    "menu": "3D0F1C8A-0F7E-4D3E-9E4B-A311A2C3D4E5",
    "heic": "3D0F1C8A-0F7E-4D3E-9E4B-A411A2C3D4E5",
    "failed": "3D0F1C8A-0F7E-4D3E-9E4B-A611A2C3D4E5",
}


def rung1():
    """A named variable. Text -> Set Variable -> Show Result of the variable."""
    return [
        action(
            "is.workflow.actions.comment",
            {"WFCommentActionText": "Ladder rung 1: named variable."},
        ),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": "hello from rung 1"},
            uuid=U["text"],
        ),
        set_variable("Greeting", (U["text"], "Text")),
        action(
            "is.workflow.actions.showresult",
            {"Text": text_token(variable_ref("Greeting"))},
        ),
    ]


def rung2():
    """+ If / Otherwise on Shortcut Input, setting a variable in each branch."""
    return rung1() + [
        if_start(G["input"], SHORTCUT_INPUT, CONDITION_HAS_ANY_VALUE),
        set_variable("Note", SHORTCUT_INPUT),
        if_else(G["input"]),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": "run directly, no input"},
            uuid=U["note"],
        ),
        set_variable("Note", (U["note"], "Text")),
        if_end(G["input"]),
        action(
            "is.workflow.actions.showresult",
            {"Text": text_token(variable_ref("Note"))},
        ),
    ]


def rung3():
    """+ Choose from Menu with two items, each showing a notification."""
    return rung2() + [
        menu_start(G["menu"], "Ladder rung 3", ["Option A", "Option B"]),
        menu_item(G["menu"], "Option A"),
        action(
            "is.workflow.actions.notification",
            {
                "WFNotificationActionTitle": "You chose A",
                "WFNotificationActionBody": text_token(variable_ref("Note")),
                "WFNotificationActionSound": False,
            },
        ),
        menu_item(G["menu"], "Option B"),
        action(
            "is.workflow.actions.notification",
            {
                "WFNotificationActionTitle": "You chose B",
                "WFNotificationActionBody": text_token(variable_ref("Note")),
                "WFNotificationActionSound": False,
            },
        ),
        menu_end(G["menu"]),
    ]


def rung4():
    """+ Select Photos, Get Details of Images, conditional Convert Image."""
    return rung3() + [
        action(
            "is.workflow.actions.selectphoto",
            {"WFSelectMultiplePhotos": False},
            uuid=U["select"],
        ),
        set_variable("Image", (U["select"], "Photos")),
        action(
            "is.workflow.actions.properties.images",
            {
                "WFInput": variable_input(variable_ref("Image")),
                "WFContentItemPropertyName": "File Extension",
            },
            uuid=U["ext"],
        ),
        if_start(G["heic"], (U["ext"], "File Extension"), CONDITION_CONTAINS, "hei"),
        action(
            "is.workflow.actions.image.convert",
            {
                "WFInput": variable_input(variable_ref("Image")),
                "WFImageFormat": "JPEG",
                "WFImageCompressionQuality": 0.9,
                "WFImagePreserveMetadata": False,
            },
            uuid=U["convert"],
        ),
        set_variable("Upload", (U["convert"], "Converted Image")),
        if_else(G["heic"]),
        set_variable("Upload", variable_ref("Image")),
        if_end(G["heic"]),
    ]


def rung5():
    """+ the upload: Form body with a File field, two dictionary lookups, clipboard."""
    return rung4() + [
        action(
            "is.workflow.actions.downloadurl",
            {
                "WFURL": imgur.ENDPOINT,
                "WFHTTPMethod": "POST",
                "WFHTTPBodyType": "Form",
                "WFFormValues": dictionary_value(
                    [
                        file_item("image", variable_ref("Upload")),
                        text_item("type", "file"),
                    ]
                ),
                "ShowHeaders": False,
            },
            uuid=U["http"],
        ),
        set_variable("Response", (U["http"], "Contents of URL")),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "WFInput": variable_input(variable_ref("Response")),
                "WFDictionaryKey": "data",
                "WFGetDictionaryValueType": "Value",
            },
            uuid=U["data"],
        ),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "WFInput": action_output_input(U["data"], "Dictionary Value"),
                "WFDictionaryKey": "link",
                "WFGetDictionaryValueType": "Value",
            },
            uuid=U["link"],
        ),
        set_variable("Link", (U["link"], "Dictionary Value")),
        action(
            "is.workflow.actions.setclipboard",
            {"WFInput": variable_input(variable_ref("Link"))},
        ),
    ]


def rung6():
    """+ the error path (Show Alert, Stop) and the QR code (generate, save)."""
    return rung5() + [
        if_start(G["failed"], variable_ref("Link"), CONDITION_DOES_NOT_HAVE_ANY_VALUE),
        action(
            "is.workflow.actions.alert",
            {
                "WFAlertActionTitle": "Upload failed",
                "WFAlertActionMessage": text_token("Imgur returned: ", variable_ref("Response")),
                "WFAlertActionCancelButtonShown": False,
            },
        ),
        action("is.workflow.actions.exit"),
        if_end(G["failed"]),
        action(
            "is.workflow.actions.generatebarcode",
            {"WFText": text_token(variable_ref("Link"))},
            uuid=U["qr"],
        ),
        action(
            "is.workflow.actions.savetocameraroll",
            {"WFInput": action_output_input(U["qr"], "QR Code")},
        ),
        action(
            "is.workflow.actions.showresult",
            {"Text": text_with_variable(U["link"], "Dictionary Value")},
        ),
    ]


def rung7_actions():
    """The real shortcut's action list, exactly."""
    return (
        imgur.client_id()
        + imgur.pick_image()
        + imgur.normalize_format()
        + imgur.upload()
        + imgur.choose_output()
    )


def build_all():
    base = dict(glyph_number=GLYPH, start_color=COLOR)
    return {
        1: shortcut(rung1(), **base),
        2: shortcut(rung2(), **base),
        3: shortcut(rung3(), **base),
        4: shortcut(rung4(), **base),
        5: shortcut(rung5(), **base),
        6: shortcut(rung6(), **base),
        7: modern_shortcut(rung7_actions(), uses_shortcut_input=True, **base),
    }


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    for n, workflow in build_all().items():
        write_shortcut(os.path.join(out_dir, NAME.format(n=n)), workflow)
