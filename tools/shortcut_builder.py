"""Helpers for generating unsigned iOS Shortcuts (.shortcut) files.

A .shortcut file is a property list. The Shortcuts app reads either the XML or
the binary flavour; Apple writes binary, so that is what `write_shortcut` emits.

The only structure that really matters is `WFWorkflowActions`: an ordered list
of `{WFWorkflowActionIdentifier, WFWorkflowActionParameters}` dictionaries. An
action with no explicit input parameter implicitly consumes the output of the
action above it, which is why the shortcuts here mostly chain without wiring up
magic variables by hand. When a value has to be referenced explicitly (dropping
an action's output into a text field, for example) use `text_with_variable`.
"""

import plistlib

# Match the top-level fields of a real, known-importable shortcut (the Shortcuts
# Playground golden corpus). Those files carry a client release + version and an
# empty icon image-data blob, and omit the minimum-version / quick-action /
# output-fallback keys we had been adding.
CLIENT_RELEASE = "2.1.1"
CLIENT_VERSION = "736"

# Every content type Shortcuts knows about, so a shortcut will accept whatever
# is handed to it rather than refusing input it could have coerced.
ALL_INPUT_CONTENT_ITEM_CLASSES = [
    "WFAppStoreAppContentItem",
    "WFArticleContentItem",
    "WFContactContentItem",
    "WFDateContentItem",
    "WFEmailAddressContentItem",
    "WFGenericFileContentItem",
    "WFImageContentItem",
    "WFiTunesProductContentItem",
    "WFLocationContentItem",
    "WFDCMapsLinkContentItem",
    "WFAVAssetContentItem",
    "WFPDFContentItem",
    "WFPhoneNumberContentItem",
    "WFRichTextContentItem",
    "WFSafariWebPageContentItem",
    "WFStringContentItem",
    "WFURLContentItem",
]


def action(identifier, parameters=None, uuid=None):
    """One entry in WFWorkflowActions.

    Pass `uuid` when a later action needs to reference this one's output.
    """
    params = dict(parameters or {})
    if uuid:
        params["UUID"] = uuid
    return {
        "WFWorkflowActionIdentifier": identifier,
        "WFWorkflowActionParameters": params,
    }


def text_with_variable(uuid, output_name):
    """A text field whose entire contents are one action's output.

    Shortcuts stores attachments as an object-replacement character in the
    string plus a range map pointing at the action that produced the value.
    Verified against real shortcuts extracted with shortcut-sign: an
    ActionOutput attachment carries Type/OutputUUID/OutputName exactly so.
    """
    return {
        "WFSerializationType": "WFTextTokenString",
        "Value": {
            "string": "￼",
            "attachmentsByRange": {
                "{0, 1}": {
                    "Type": "ActionOutput",
                    "OutputUUID": uuid,
                    "OutputName": output_name,
                }
            },
        },
    }


def action_output_input(uuid, output_name):
    """An explicit WFInput pointing at a prior action's output.

    Real serialized shortcuts wire each action's input this way rather than
    relying on the app's implicit "use previous output" convenience. Verified
    against the WFInput on real base64encode and setitemname actions:
    a WFTextTokenAttachment whose Value is an ActionOutput reference.
    """
    return {
        "WFSerializationType": "WFTextTokenAttachment",
        "Value": {
            "Type": "ActionOutput",
            "OutputUUID": uuid,
            "OutputName": output_name,
        },
    }


def shortcut(actions, glyph_number=59511, start_color=463140863, workflow_types=None):
    """Wrap actions in the top-level dictionary, matching a golden shortcut.

    Deliberately the exact key set of a known-importable shortcut: actions, the
    client release/version pair, an icon carrying an empty image-data blob, the
    import-questions and input-content-item-classes arrays, and workflow types.
    Nothing else — extra keys are what distinguished our earlier, rejected files.
    """
    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientRelease": CLIENT_RELEASE,
        "WFWorkflowClientVersion": CLIENT_VERSION,
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": glyph_number,
            # Empty, but present: golden shortcuts always carry this key.
            "WFWorkflowIconImageData": b"",
            "WFWorkflowIconStartColor": start_color,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": ALL_INPUT_CONTENT_ITEM_CLASSES,
        "WFWorkflowTypes": workflow_types or [],
    }


def write_shortcut(path, workflow):
    with open(path, "wb") as handle:
        plistlib.dump(workflow, handle, fmt=plistlib.FMT_BINARY)
    print("wrote", path)
