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


# --- References -----------------------------------------------------------
# The three things a field can point at. Each is the `Value` of an attachment:
# an earlier action's output, a named variable set by Set Variable, or the
# input the shortcut was handed (the share sheet item, "Shortcut Input").

SHORTCUT_INPUT = {"Type": "ExtensionInput"}


def output_ref(uuid, output_name):
    return {"Type": "ActionOutput", "OutputUUID": uuid, "OutputName": output_name}


def variable_ref(name):
    return {"Type": "Variable", "VariableName": name}


def _as_ref(value):
    """Normalize the ways this module accepts a reference into one dict."""
    if isinstance(value, tuple):
        return output_ref(*value)
    if isinstance(value, dict) and "Type" in value:
        return value
    raise TypeError("not a reference: %r" % (value,))


def variable_input(value):
    """An explicit WFInput pointing at a variable or the shortcut's input.

    The named-variable counterpart of `action_output_input`; both serialize as a
    WFTextTokenAttachment and differ only in the Type of the value inside.
    """
    return {"WFSerializationType": "WFTextTokenAttachment", "Value": _as_ref(value)}


def _text_value(*parts):
    """Build the string + attachment range map for a run of literals and refs.

    Attachments live in the string as an object-replacement character, and
    `attachmentsByRange` maps each one's position to what it points at. One part
    is the common case; several parts are how a field mixes literal text with a
    variable, as in the "Client-ID <ClientID>" authorization header.
    """
    string = ""
    attachments = {}
    for part in parts:
        if isinstance(part, str):
            string += part
        else:
            attachments["{%d, 1}" % len(string)] = _as_ref(part)
            string += "￼"
    value = {"string": string}
    if attachments:
        value["attachmentsByRange"] = attachments
    return value


def text_token(*parts):
    """A WFTextTokenString whose content is literal text, variables, or both.

    Each part is a plain string, an (output_uuid, output_name) tuple, or a
    reference from `variable_ref` / `output_ref` / `SHORTCUT_INPUT`.
    """
    return {"WFSerializationType": "WFTextTokenString", "Value": _text_value(*parts)}


# WFItemType picks how one entry of a dictionary field is interpreted. 0 is a
# text value; 5 is the "File" option a Get-Contents-of-URL form field offers,
# whose value is a whole attachment (an image, say) rather than a text token.
ITEM_TYPE_TEXT = 0
ITEM_TYPE_FILE = 5


def text_item(key, *parts):
    """One text entry of a dictionary field."""
    return {
        "WFItemType": ITEM_TYPE_TEXT,
        "WFKey": text_token(key),
        "WFValue": text_token(*parts),
    }


def file_item(key, value):
    """One file entry of a form body — the field an image is uploaded in.

    Unlike a text entry the value is not a text token: it is the attachment
    itself, so Shortcuts sends the file's bytes as that multipart part instead
    of a string rendering of it.
    """
    return {
        "WFItemType": ITEM_TYPE_FILE,
        "WFKey": text_token(key),
        "WFValue": variable_input(value),
    }


def dictionary_value(items):
    """Wrap `text_item` / `file_item` entries as a WFDictionaryFieldValue."""
    return {
        "WFSerializationType": "WFDictionaryFieldValue",
        "Value": {"WFDictionaryFieldValueItems": items},
    }


def dictionary_field(pairs):
    """A WFDictionaryFieldValue — the serialized form of a key/value dictionary.

    `pairs` is a list of (key, value); each value may be a literal string or an
    (output_uuid, output_name) tuple for a variable. Verified against the JSON
    body and header dictionaries of real Get-Contents-of-URL actions. For a
    body that mixes in a file, build the items with `text_item` / `file_item`
    and pass them to `dictionary_value` instead.
    """
    return dictionary_value([text_item(key, value) for key, value in pairs])


# --- Control flow ---------------------------------------------------------
# If and Choose-from-Menu are not nested structures in the plist: each is a run
# of sibling actions sharing a GroupingIdentifier, distinguished by
# WFControlFlowMode — 0 opens the block, 1 starts a branch (Otherwise, or a menu
# item), 2 closes it. Every action between two markers belongs to the branch the
# earlier marker opened.
CONTROL_FLOW_START = 0
CONTROL_FLOW_BRANCH = 1
CONTROL_FLOW_END = 2

# WFCondition values. Shortcuts writes these as integers.
CONDITION_EQUALS = 4
CONDITION_CONTAINS = 99
CONDITION_HAS_ANY_VALUE = 100
CONDITION_DOES_NOT_HAVE_ANY_VALUE = 101


def if_start(group_id, value, condition, comparand=None, uuid=None):
    """Open an If block testing `value` against `comparand`.

    An If wires its input differently from every other action: rather than a
    bare attachment, WFInput is a dict naming the kind of input and carrying the
    attachment under `Variable`. `comparand` is omitted for the has-any-value
    conditions, which compare against nothing.
    """
    parameters = {
        "GroupingIdentifier": group_id,
        "WFControlFlowMode": CONTROL_FLOW_START,
        "WFCondition": condition,
        "WFInput": {"Type": "Variable", "Variable": variable_input(value)},
    }
    if comparand is not None:
        parameters["WFConditionalActionString"] = text_token(comparand)
    return action("is.workflow.actions.conditional", parameters, uuid=uuid)


def if_else(group_id):
    return action(
        "is.workflow.actions.conditional",
        {"GroupingIdentifier": group_id, "WFControlFlowMode": CONTROL_FLOW_BRANCH},
    )


def if_end(group_id):
    return action(
        "is.workflow.actions.conditional",
        {"GroupingIdentifier": group_id, "WFControlFlowMode": CONTROL_FLOW_END},
    )


def menu_start(group_id, prompt, items):
    """Open a Choose from Menu block. `items` are the option titles, in order."""
    return action(
        "is.workflow.actions.choosefrommenu",
        {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": CONTROL_FLOW_START,
            "WFMenuPrompt": prompt,
            "WFMenuItems": list(items),
        },
    )


def menu_item(group_id, title):
    """Start the branch run when `title` is picked. Must match a `menu_start` item."""
    return action(
        "is.workflow.actions.choosefrommenu",
        {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": CONTROL_FLOW_BRANCH,
            "WFMenuItemTitle": title,
        },
    )


def menu_end(group_id):
    return action(
        "is.workflow.actions.choosefrommenu",
        {"GroupingIdentifier": group_id, "WFControlFlowMode": CONTROL_FLOW_END},
    )


def set_variable(name, value):
    return action(
        "is.workflow.actions.setvariable",
        {"WFVariableName": name, "WFInput": variable_input(value)},
    )


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
