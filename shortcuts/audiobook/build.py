#!/usr/bin/env python3
"""Build the "Read Clipboard (Audiobook)" shortcut.

Sends the clipboard text to an n8n webhook, which runs the Lemonfox
text-to-speech / 2x pipeline and returns an audio file, then hands that audio to
VLC through the share sheet.

    Get Clipboard -> Text -> POST text to the n8n webhook -> Set Name -> Open In

The shortcut holds no credentials. The Lemonfox API key stays in n8n; the only
thing here is the webhook URL, which is safe to publish (add a webhook auth
header in n8n if you want it locked down).

Run from anywhere:

    python3 shortcuts/audiobook/build.py [OUTPUT_DIR]
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from shortcut_builder import (
    action,
    action_output_input,
    dictionary_field,
    shortcut,
    text_token,
    text_with_variable,
    write_shortcut,
)

HERE = os.path.dirname(os.path.abspath(__file__))

# The webhook this shortcut posts to. Must match the n8n Webhook node's path.
WEBHOOK_URL = "https://n8n.shae.dpdns.org/webhook/audiobook"

# The JSON field name the n8n workflow reads the text from ($json.body.text).
BODY_FIELD = "text"

# Downloaded audio is named this so it carries an extension VLC recognizes.
AUDIO_NAME = "audiobook.mp3"

# Fixed UUIDs keep rebuilds byte-identical.
U_CLIPBOARD = "9A0F1C8A-0F7E-4D3E-9E4B-1C1A2C3D4E5F"
U_TEXT = "9A0F1C8A-0F7E-4D3E-9E4B-2C1A2C3D4E5F"
U_HTTP = "9A0F1C8A-0F7E-4D3E-9E4B-3C1A2C3D4E5F"
U_NAME = "9A0F1C8A-0F7E-4D3E-9E4B-4C1A2C3D4E5F"

# Audio waveform glyph, purple.
GLYPH = 59446
COLOR = 3679049983


def build():
    actions = [
        action("is.workflow.actions.getclipboard", uuid=U_CLIPBOARD),
        # Coerce the clipboard to plain text.
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": text_with_variable(U_CLIPBOARD, "Clipboard")},
            uuid=U_TEXT,
        ),
        # POST {"text": <clipboard>} to the webhook; the response is the audio.
        action(
            "is.workflow.actions.downloadurl",
            {
                "WFURL": text_token(WEBHOOK_URL),
                "WFHTTPMethod": "POST",
                "WFHTTPBodyType": "JSON",
                "WFJSONValues": dictionary_field(
                    [(BODY_FIELD, (U_TEXT, "Text"))]
                ),
                "ShowHeaders": False,
            },
            uuid=U_HTTP,
        ),
        # Give the returned audio a filename so VLC treats it as a media file.
        action(
            "is.workflow.actions.setitemname",
            {
                "WFInput": action_output_input(U_HTTP, "Contents of URL"),
                "WFName": AUDIO_NAME,
                "WFDontIncludeFileExtension": False,
            },
            uuid=U_NAME,
        ),
        # Open In… -> pick VLC from the share sheet.
        action(
            "is.workflow.actions.openin",
            {"WFInput": action_output_input(U_NAME, "Renamed Item")},
        ),
    ]
    return shortcut(actions, glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, "Read Clipboard (Audiobook).shortcut"), build())
