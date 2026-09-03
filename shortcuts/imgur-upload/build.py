#!/usr/bin/env python3
"""Build the "Upload to Imgur" shortcut.

Uploads an image to Imgur anonymously and then asks what to do with the link:
copy it to the clipboard, or save a QR code of it to Photos.

    Client ID -> pick image -> HEIC? convert -> POST /3/upload -> data.link
                                                                     |
                                              Copy Link  <-- menu -->  Save QR Code

Three details of the Imgur side drive the shape of this:

  * The upload endpoint is POST https://api.imgur.com/3/upload, sending the
    image as a multipart form field named `image` (with `type=file`). The older
    /3/image path is the same handler; /3/upload is the current documented one.
  * A client ID is optional in practice. Imgur documents an
    `Authorization: Client-ID <id>` header, but as of 2026-09 the endpoint
    accepts anonymous uploads with no header at all — which is just as well,
    since https://api.imgur.com/oauth2/addclient, the registration page every
    Imgur guide points at, now redirects to the homepage. So the shortcut sends
    the header only when a client ID has actually been pasted in, and works out
    of the box without one. Two upload actions rather than one, because a header
    dictionary is fixed per action and cannot be built conditionally.
  * Imgur accepts JPEG, PNG and GIF — not HEIC, which is what an iPhone camera
    produces by default. So the shortcut checks the file extension and converts
    only in that case, leaving PNG screenshots and animated GIFs untouched.

Run from anywhere:

    python3 shortcuts/imgur-upload/build.py [OUTPUT_DIR]
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from shortcut_builder import (
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
    set_variable,
    shortcut,
    text_item,
    text_token,
    text_with_variable,
    variable_input,
    variable_ref,
    write_shortcut,
)

HERE = os.path.dirname(os.path.abspath(__file__))

OUT_NAME = "Upload to Imgur.shortcut"

# A cut-down build used to bisect the crash described on build_minimal().
MINIMAL_NAME = "Upload to Imgur (Minimal).shortcut"

# Imgur API v3. POST here with the image as multipart form data.
ENDPOINT = "https://api.imgur.com/3/upload"

# What the Text action at the top of the shortcut says until you edit it.
# Leaving it alone is a supported choice: the untouched placeholder is what
# selects the no-client-ID upload. The test below looks for a fragment of this
# string, so change the two together.
CLIENT_ID_PLACEHOLDER = "PASTE_YOUR_IMGUR_CLIENT_ID_HERE"
CLIENT_ID_UNSET_MARKER = "PASTE_YOUR"

# Quality for the HEIC -> JPEG conversion. High enough that the re-encode is not
# visible; low enough to stay well inside Imgur's per-image limit.
JPEG_QUALITY = 0.9

MENU_COPY = "Copy Link"
MENU_QR = "Save QR Code"

# Named variables. Branches of an If cannot hand a value forward the way a
# straight chain of actions does, so anything produced inside one is parked in a
# variable and read back out after the block closes.
V_CLIENT_ID = "ClientID"
V_IMAGE = "Image"
V_UPLOAD = "Upload"
V_RESPONSE = "Response"
V_LINK = "Link"

# Fixed UUIDs and grouping identifiers keep rebuilds byte-identical.
U_CLIENT_ID = "1D0F1C8A-0F7E-4D3E-9E4B-1A1A2C3D4E5F"
U_SELECT = "1D0F1C8A-0F7E-4D3E-9E4B-2A1A2C3D4E5F"
U_EXTENSION = "1D0F1C8A-0F7E-4D3E-9E4B-3A1A2C3D4E5F"
U_CONVERT = "1D0F1C8A-0F7E-4D3E-9E4B-4A1A2C3D4E5F"
U_HTTP_ANON = "1D0F1C8A-0F7E-4D3E-9E4B-5A1A2C3D4E5F"
U_HTTP_KEYED = "1D0F1C8A-0F7E-4D3E-9E4B-9A1A2C3D4E5F"
U_DATA = "1D0F1C8A-0F7E-4D3E-9E4B-6A1A2C3D4E5F"
U_LINK = "1D0F1C8A-0F7E-4D3E-9E4B-7A1A2C3D4E5F"
U_QR = "1D0F1C8A-0F7E-4D3E-9E4B-8A1A2C3D4E5F"

# The minimal build's own UUIDs, disjoint from the full build's.
M_SELECT = "2D0F1C8A-0F7E-4D3E-9E4B-1A1A2C3D4E5F"
M_CONVERT = "2D0F1C8A-0F7E-4D3E-9E4B-2A1A2C3D4E5F"
M_HTTP = "2D0F1C8A-0F7E-4D3E-9E4B-3A1A2C3D4E5F"
M_DATA = "2D0F1C8A-0F7E-4D3E-9E4B-4A1A2C3D4E5F"
M_LINK = "2D0F1C8A-0F7E-4D3E-9E4B-5A1A2C3D4E5F"

G_AUTH = "1D0F1C8A-0F7E-4D3E-9E4B-A11A2C3D4E5F"
G_INPUT = "1D0F1C8A-0F7E-4D3E-9E4B-B11A2C3D4E5F"
G_HEIC = "1D0F1C8A-0F7E-4D3E-9E4B-C11A2C3D4E5F"
G_FAILED = "1D0F1C8A-0F7E-4D3E-9E4B-D11A2C3D4E5F"
G_MENU = "1D0F1C8A-0F7E-4D3E-9E4B-E11A2C3D4E5F"

# Glyph and colour lifted from the golden shortcut: a known-good icon pair.
GLYPH = 59831
COLOR = 2071128575

SETUP_COMMENT = (
    "No setup needed — run it as is.\n\n"
    "Imgur's upload endpoint currently accepts anonymous uploads with no "
    "credentials, so the action below is left as the placeholder on purpose. "
    "Leave it alone and the shortcut uploads without a client ID.\n\n"
    "If you do have an Imgur client ID, replace the whole placeholder with it "
    "(just the ID — the \"Client-ID\" prefix is added for you) and every upload "
    "will be sent under it instead. Imgur's registration page at "
    "api.imgur.com/oauth2/addclient now redirects to the homepage, so there is "
    "currently no way to obtain a new one.\n\n"
    "Either way the upload belongs to no account and cannot be deleted from the "
    "Imgur website afterwards."
)


def client_id():
    """The optional client ID, in an editable Text action, parked in a variable.

    A Text action rather than an Ask Each Time prompt: this shortcut is meant to
    run from the share sheet without questions, and the ID never changes.
    """
    return [
        action("is.workflow.actions.comment", {"WFCommentActionText": SETUP_COMMENT}),
        action(
            "is.workflow.actions.gettext",
            {"WFTextActionText": text_token(CLIENT_ID_PLACEHOLDER)},
            uuid=U_CLIENT_ID,
        ),
        set_variable(V_CLIENT_ID, (U_CLIENT_ID, "Text")),
    ]


def pick_image():
    """Use whatever was shared in, or ask for a photo when run on its own.

    Run from the share sheet the image arrives as Shortcut Input; run from the
    Shortcuts app or the home screen there is no input, so fall through to the
    photo picker.
    """
    return [
        if_start(G_INPUT, SHORTCUT_INPUT, CONDITION_HAS_ANY_VALUE),
        set_variable(V_IMAGE, SHORTCUT_INPUT),
        if_else(G_INPUT),
        action(
            "is.workflow.actions.selectphoto",
            {"WFSelectMultiplePhotos": False},
            uuid=U_SELECT,
        ),
        set_variable(V_IMAGE, (U_SELECT, "Photos")),
        if_end(G_INPUT),
    ]


def normalize_format():
    """Convert to JPEG only when the image is HEIC/HEIF, which Imgur rejects.

    Converting unconditionally would flatten PNG transparency and kill GIF
    animation, so the extension is tested first. "hei" catches both .heic and
    .heif. Metadata is dropped in the conversion, which also strips the GPS
    coordinates the camera wrote into the file before it goes somewhere public.
    """
    return [
        action(
            "is.workflow.actions.properties.images",
            {
                "WFInput": variable_input(variable_ref(V_IMAGE)),
                "WFContentItemPropertyName": "File Extension",
            },
            uuid=U_EXTENSION,
        ),
        if_start(
            G_HEIC,
            (U_EXTENSION, "File Extension"),
            CONDITION_CONTAINS,
            "hei",
        ),
        action(
            "is.workflow.actions.image.convert",
            {
                "WFInput": variable_input(variable_ref(V_IMAGE)),
                "WFImageFormat": "JPEG",
                "WFImageCompressionQuality": JPEG_QUALITY,
                "WFImagePreserveMetadata": False,
            },
            uuid=U_CONVERT,
        ),
        set_variable(V_UPLOAD, (U_CONVERT, "Converted Image")),
        if_else(G_HEIC),
        set_variable(V_UPLOAD, variable_ref(V_IMAGE)),
        if_end(G_HEIC),
    ]


def post(uuid, headers):
    """The upload request. `headers` is the header dictionary, or None for none."""
    parameters = {
        "WFURL": text_token(ENDPOINT),
        "WFHTTPMethod": "POST",
        "WFHTTPBodyType": "Form",
        "WFFormValues": dictionary_value(
            [
                file_item("image", variable_ref(V_UPLOAD)),
                text_item("type", "file"),
            ]
        ),
        "ShowHeaders": False,
    }
    if headers is not None:
        parameters["WFHTTPHeaders"] = headers
    return action("is.workflow.actions.downloadurl", parameters, uuid=uuid)


def upload():
    """POST the image and dig the link out of Imgur's JSON envelope.

    Two requests, differing only in whether they carry an Authorization header,
    because the placeholder being untouched means there is no client ID to send
    and a header dictionary cannot be assembled conditionally within one action.

    The response is {"status": …, "success": …, "data": {"link": …}}, so the
    link needs two hops. Both the raw response and the link are kept: the
    response is what gets shown if the link never materializes.
    """
    return [
        if_start(
            G_AUTH,
            variable_ref(V_CLIENT_ID),
            CONDITION_CONTAINS,
            CLIENT_ID_UNSET_MARKER,
        ),
        post(U_HTTP_ANON, None),
        set_variable(V_RESPONSE, (U_HTTP_ANON, "Contents of URL")),
        if_else(G_AUTH),
        post(
            U_HTTP_KEYED,
            dictionary_value(
                [text_item("Authorization", "Client-ID ", variable_ref(V_CLIENT_ID))]
            ),
        ),
        set_variable(V_RESPONSE, (U_HTTP_KEYED, "Contents of URL")),
        if_end(G_AUTH),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "WFInput": variable_input(variable_ref(V_RESPONSE)),
                "WFDictionaryKey": "data",
                "WFGetDictionaryValueType": "Value",
            },
            uuid=U_DATA,
        ),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "WFInput": action_output_input(U_DATA, "Dictionary Value"),
                "WFDictionaryKey": "link",
                "WFGetDictionaryValueType": "Value",
            },
            uuid=U_LINK,
        ),
        set_variable(V_LINK, (U_LINK, "Dictionary Value")),
        # No link means Imgur refused: bad client ID, rate limit, file too
        # large. Show what it said rather than a generic failure.
        if_start(G_FAILED, variable_ref(V_LINK), CONDITION_DOES_NOT_HAVE_ANY_VALUE),
        action(
            "is.workflow.actions.alert",
            {
                "WFAlertActionTitle": "Imgur upload failed",
                "WFAlertActionMessage": text_token(
                    "Imgur returned:\n\n", variable_ref(V_RESPONSE)
                ),
                "WFAlertActionCancelButtonShown": False,
            },
        ),
        action("is.workflow.actions.exit"),
        if_end(G_FAILED),
    ]


def choose_output():
    """The one question the shortcut asks: clipboard, or QR code in Photos."""
    return [
        menu_start(G_MENU, "Uploaded to Imgur", [MENU_COPY, MENU_QR]),
        menu_item(G_MENU, MENU_COPY),
        action(
            "is.workflow.actions.setclipboard",
            {"WFInput": variable_input(variable_ref(V_LINK))},
        ),
        action(
            "is.workflow.actions.notification",
            {
                "WFNotificationActionTitle": text_token("Imgur link copied"),
                "WFNotificationActionBody": text_token(variable_ref(V_LINK)),
                "WFNotificationActionSound": False,
            },
        ),
        menu_item(G_MENU, MENU_QR),
        action(
            "is.workflow.actions.generatebarcode",
            {
                "WFInput": text_token(variable_ref(V_LINK)),
                "WFQRCodeCorrectionLevel": "Medium",
            },
            uuid=U_QR,
        ),
        action(
            "is.workflow.actions.savetocameraroll",
            {"WFInput": action_output_input(U_QR, "QR Code")},
        ),
        action(
            "is.workflow.actions.notification",
            {
                "WFNotificationActionTitle": text_token("QR code saved to Photos"),
                "WFNotificationActionBody": text_token(variable_ref(V_LINK)),
                "WFNotificationActionSound": False,
            },
        ),
        menu_end(G_MENU),
    ]


def build():
    actions = client_id() + pick_image() + normalize_format() + upload() + choose_output()
    # ActionExtension puts it in the share sheet, which is the point: share an
    # image from Photos or Safari straight into the upload.
    return shortcut(
        actions,
        glyph_number=GLYPH,
        start_color=COLOR,
        workflow_types=["ActionExtension"],
    )


def build_minimal():
    """A deliberately boring build, to bisect a crash in the full one.

    The Shortcuts app crashes on opening the full shortcut, and there are two
    candidate causes: the signed container (this repo's CI signs on Linux with
    shortcut-sign, which HANDBOOK.md flags as never verified against a device),
    or something in the plist. This build isolates the second.

    It keeps only what an upload actually requires, and drops every construct
    the full version introduced to this repo: no If, no menu, no named
    variables, no share-sheet workflow type. What is left is the linear
    output-chaining the repo's three working shortcuts already use, plus the
    two genuinely new things — the File-typed form entry that carries the image
    and Get Dictionary Value.

      Select Photos -> Convert to JPEG -> POST -> data -> link -> clipboard

    So: if this opens and the full one crashes, the fault is in the control
    flow or the workflow type. If this crashes too, the fault is in the upload
    action or the container, and the plist's structure is not the problem.

    It converts to JPEG unconditionally rather than testing the extension —
    lossy for a PNG screenshot, but this is a diagnostic, not the deliverable.
    """
    actions = [
        action(
            "is.workflow.actions.selectphoto",
            {"WFSelectMultiplePhotos": False},
            uuid=M_SELECT,
        ),
        action(
            "is.workflow.actions.image.convert",
            {
                "WFInput": action_output_input(M_SELECT, "Photos"),
                "WFImageFormat": "JPEG",
                "WFImageCompressionQuality": JPEG_QUALITY,
                "WFImagePreserveMetadata": False,
            },
            uuid=M_CONVERT,
        ),
        action(
            "is.workflow.actions.downloadurl",
            {
                "WFURL": text_token(ENDPOINT),
                "WFHTTPMethod": "POST",
                "WFHTTPBodyType": "Form",
                "WFFormValues": dictionary_value(
                    [
                        file_item("image", (M_CONVERT, "Converted Image")),
                        text_item("type", "file"),
                    ]
                ),
                "ShowHeaders": False,
            },
            uuid=M_HTTP,
        ),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "WFInput": action_output_input(M_HTTP, "Contents of URL"),
                "WFDictionaryKey": "data",
                "WFGetDictionaryValueType": "Value",
            },
            uuid=M_DATA,
        ),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "WFInput": action_output_input(M_DATA, "Dictionary Value"),
                "WFDictionaryKey": "link",
                "WFGetDictionaryValueType": "Value",
            },
            uuid=M_LINK,
        ),
        action(
            "is.workflow.actions.setclipboard",
            {"WFInput": action_output_input(M_LINK, "Dictionary Value")},
        ),
        action(
            "is.workflow.actions.showresult",
            {"Text": text_with_variable(M_LINK, "Dictionary Value")},
        ),
    ]
    return shortcut(actions, glyph_number=GLYPH, start_color=COLOR)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    write_shortcut(os.path.join(out_dir, OUT_NAME), build())
    write_shortcut(os.path.join(out_dir, MINIMAL_NAME), build_minimal())
