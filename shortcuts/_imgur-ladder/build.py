#!/usr/bin/env python3
"""Bisect the "Upload to Imgur" crash. Round 4: four revisions of the request.

Trail:
  Round 1 — second half crashed.
  Round 2 — the upload block (B1) crashed.
  Round 3 — the request half (B1a) crashed; the parse half (B1b) opened.

B1a is an If(auth) around two Get-Contents-of-URL requests with a Form body.
We know If blocks open (the first half and B1b use them), so the suspect is the
request. Rather than halve it again, this round is FOUR revisions of a single
request, each adding one thing to the last. Open them in order; the first that
crashes names the exact addition responsible.

  B1a-1  bare POST to the URL, no body at all.                (is downloadurl ok?)
  B1a-2  + a Form body of TEXT items only (image as text).    (is a Form body ok?)
  B1a-3  + the image as a FILE field, WFItemType 5.           (is the File field it?)
  B1a-4  + the Authorization headers dictionary.              (do headers compound?)

  1 crashes            -> Get-Contents-of-URL itself is serialized wrong here.
  1 ok, 2 crashes      -> the Form body is the problem, not the File field.
  2 ok, 3 crashes      -> the File field (WFItemType 5) is the bug. Fix how the
                          image is attached, from ground truth.
  3 ok, 4 crashes      -> the headers dictionary is the bug.
  all four open        -> the crash needs the If wrapper or both requests
                          together; go back and split B1a that way.

The real shortcut's request is B1a-3 (anonymous) and B1a-4 (client-ID). So
whichever of 3/4 first crashes is the actual defect.

Only OPEN them; the crash is on open. Nothing uploads (the image and client-ID
variables are undefined here, which only matters if run).

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

import build as imgur  # noqa: E402  (ENDPOINT, V_UPLOAD, V_CLIENT_ID)

GLYPH = 59511
COLOR = 4251333119

U1 = "4D0F1C8A-0F7E-4D3E-9E4B-0111A2C3D4E5"
U2 = "4D0F1C8A-0F7E-4D3E-9E4B-0211A2C3D4E5"
U3 = "4D0F1C8A-0F7E-4D3E-9E4B-0311A2C3D4E5"
U4 = "4D0F1C8A-0F7E-4D3E-9E4B-0411A2C3D4E5"


def _wrap(a):
    return shortcut([a], glyph_number=GLYPH, start_color=COLOR)


def rev1():
    # Bare POST, no body. Baseline for downloadurl itself.
    return _wrap(
        action(
            "is.workflow.actions.downloadurl",
            {"WFURL": imgur.ENDPOINT, "WFHTTPMethod": "POST"},
            uuid=U1,
        )
    )


def rev2():
    # + Form body of text items only (image sent as text).
    return _wrap(
        action(
            "is.workflow.actions.downloadurl",
            {
                "WFURL": imgur.ENDPOINT,
                "WFHTTPMethod": "POST",
                "WFHTTPBodyType": "Form",
                "WFFormValues": dictionary_value(
                    [
                        text_item("image", variable_ref(imgur.V_UPLOAD)),
                        text_item("type", "file"),
                    ]
                ),
                "ShowHeaders": False,
            },
            uuid=U2,
        )
    )


def rev3():
    # + the image as a FILE field (WFItemType 5) — the real shortcut's form.
    return _wrap(
        action(
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
            uuid=U3,
        )
    )


def rev4():
    # + the Authorization headers dictionary (the client-ID request).
    return _wrap(
        action(
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
                "WFHTTPHeaders": dictionary_value(
                    [text_item("Authorization", "Client-ID ", variable_ref(imgur.V_CLIENT_ID))]
                ),
                "ShowHeaders": False,
            },
            uuid=U4,
        )
    )


BUILDS = {
    "Imgur B1a-1.shortcut": rev1,
    "Imgur B1a-2.shortcut": rev2,
    "Imgur B1a-3.shortcut": rev3,
    "Imgur B1a-4.shortcut": rev4,
}


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in BUILDS.items():
        write_shortcut(os.path.join(out_dir, name), fn())
