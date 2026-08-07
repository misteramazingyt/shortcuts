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

# Ships with iOS 17-era Shortcuts. Anything newer than the minimum below will
# open these files; the version string is informational.
CLIENT_VERSION = "2607.0.6"
MINIMUM_CLIENT_VERSION = 900

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


def shortcut(actions, glyph_number=59511, start_color=463140863, workflow_types=None):
    """Wrap actions in the top-level dictionary the Shortcuts app expects."""
    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": CLIENT_VERSION,
        "WFWorkflowMinimumClientVersion": MINIMUM_CLIENT_VERSION,
        "WFWorkflowMinimumClientVersionString": str(MINIMUM_CLIENT_VERSION),
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": glyph_number,
            "WFWorkflowIconStartColor": start_color,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": ALL_INPUT_CONTENT_ITEM_CLASSES,
        "WFWorkflowTypes": workflow_types or [],
        "WFQuickActionSurfaces": [],
        "WFWorkflowHasOutputParameters": False,
        "WFWorkflowHasShortcutInputVariables": False,
    }


def write_shortcut(path, workflow):
    with open(path, "wb") as handle:
        plistlib.dump(workflow, handle, fmt=plistlib.FMT_BINARY)
    print("wrote", path)
