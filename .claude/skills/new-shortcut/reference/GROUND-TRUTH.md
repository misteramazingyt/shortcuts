# Ground truth: how a `.shortcut` plist is really serialized

Every shape in this file was taken from a shortcut a real tool produced, not
from memory. The Shortcuts app crashes on open when a serialization is wrong, so
"looks right" is not good enough — these are the bytes that actually work.

Two sources back everything here:

- **`shortcuts/_control-golden/golden.plist.xml`** — a shortcut the Shortcuts app
  exported itself. Authoritative for the top-level dictionary and for the shapes
  it happens to contain.
- **The Cherri compiler** (`github.com/electrikmilk/cherri`, GPL) — a maintained
  compiler/decompiler for `.shortcut`, current to iOS 26. Its `actions/*.cherri`
  give exact parameter names and enum values; `shortcut.go` / `shortcutgen.go`
  give the serialization of control flow, variables and the top level.

The XML blocks below are the `WFWorkflowActionParameters` of each action,
verbatim from a generated-and-verified shortcut in this repo. Binary and XML
plists are interchangeable; the app reads both.

---

## Rule 0

If you cannot name the source of a shape, you do not write it. There is no
"probably." A guess here does not error — it crashes the app on the owner's
device, and you cannot see that from CI.

---

## The two known-good top-level dictionaries

Pick one; do not mix, and do not add keys "to be safe" — extra top-level keys
have caused rejections in this repo.

**Legacy (client version 736)** — what `shortcut()` in `tools/shortcut_builder.py`
emits and every simple shortcut here uses. Matches the golden export. Keys:
`WFWorkflowActions`, `WFWorkflowClientRelease`, `WFWorkflowClientVersion`,
`WFWorkflowIcon` (with an empty `WFWorkflowIconImageData`),
`WFWorkflowImportQuestions`, `WFWorkflowInputContentItemClasses`,
`WFWorkflowTypes`. Add `WFWorkflowHasShortcutInputVariables` = true iff any
action references Shortcut Input.

**Modern (client version 4033)** — what `modern_shortcut()` emits, copied from a
current Shortcuts export. Keys: `WFWorkflowActions`, `WFWorkflowClientVersion`
`"4033.0.4.3"`, `WFWorkflowHasOutputFallback` false,
`WFWorkflowHasShortcutInputVariables`, `WFWorkflowIcon` (glyph + start color, **no**
image-data key), `WFWorkflowInputContentItemClasses` (the 20-class modern list),
`WFWorkflowMinimumClientVersion` 900, `WFWorkflowMinimumClientVersionString`
`"900"`.

> Open question under test: whether a modern-construct shortcut stamped with the
> legacy 736 version triggers the app's migration path and crashes. If a shortcut
> full of menus/Ifs/variables crashes under the legacy top-level, try
> `modern_shortcut()`. `shortcuts/_imgur-ladder/` rung 7 is exactly this test.

---

## Verified action serializations

### Set Variable — `is.workflow.actions.setvariable`
```xml
<dict>
	<key>WFInput</key>
	<dict>
		<key>Value</key>
		<dict>
			<key>OutputName</key>
			<string>Text</string>
			<key>OutputUUID</key>
			<string>1D0F1C8A-0F7E-4D3E-9E4B-1A1A2C3D4E5F</string>
			<key>Type</key>
			<string>ActionOutput</string>
		</dict>
		<key>WFSerializationType</key>
		<string>WFTextTokenAttachment</string>
	</dict>
	<key>WFSerializationType</key>
	<string>WFTextTokenAttachment</string>
	<key>WFVariableName</key>
	<string>ClientID</string>
</dict>
```

### If start (contains) — `is.workflow.actions.conditional`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-C11A2C3D4E5F</string>
	<key>WFCondition</key>
	<integer>99</integer>
	<key>WFConditionalActionString</key>
	<string>hei</string>
	<key>WFControlFlowMode</key>
	<integer>0</integer>
	<key>WFInput</key>
	<dict>
		<key>Type</key>
		<string>Variable</string>
		<key>Variable</key>
		<dict>
			<key>Value</key>
			<dict>
				<key>OutputName</key>
				<string>File Extension</string>
				<key>OutputUUID</key>
				<string>1D0F1C8A-0F7E-4D3E-9E4B-3A1A2C3D4E5F</string>
				<key>Type</key>
				<string>ActionOutput</string>
			</dict>
			<key>WFSerializationType</key>
			<string>WFTextTokenAttachment</string>
		</dict>
	</dict>
</dict>
```

### If start (has any value) — `is.workflow.actions.conditional`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-B11A2C3D4E5F</string>
	<key>WFCondition</key>
	<integer>100</integer>
	<key>WFControlFlowMode</key>
	<integer>0</integer>
	<key>WFInput</key>
	<dict>
		<key>Type</key>
		<string>Variable</string>
		<key>Variable</key>
		<dict>
			<key>Value</key>
			<dict>
				<key>Type</key>
				<string>ExtensionInput</string>
				<key>VariableName</key>
				<string>ShortcutInput</string>
			</dict>
			<key>WFSerializationType</key>
			<string>WFTextTokenAttachment</string>
		</dict>
	</dict>
</dict>
```

### If else — `is.workflow.actions.conditional`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-B11A2C3D4E5F</string>
	<key>WFControlFlowMode</key>
	<integer>1</integer>
</dict>
```

### If end — `is.workflow.actions.conditional`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-B11A2C3D4E5F</string>
	<key>UUID</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-B11A2C3D4E5F</string>
	<key>WFControlFlowMode</key>
	<integer>2</integer>
</dict>
```

### Menu start — `is.workflow.actions.choosefrommenu`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-E11A2C3D4E5F</string>
	<key>WFControlFlowMode</key>
	<integer>0</integer>
	<key>WFMenuItems</key>
	<array>
		<dict>
			<key>WFItemType</key>
			<integer>0</integer>
			<key>WFValue</key>
			<string>Copy Link</string>
		</dict>
		<dict>
			<key>WFItemType</key>
			<integer>0</integer>
			<key>WFValue</key>
			<string>Save QR Code</string>
		</dict>
	</array>
	<key>WFMenuPrompt</key>
	<string>Uploaded to Imgur</string>
</dict>
```

### Menu item — `is.workflow.actions.choosefrommenu`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-E11A2C3D4E5F</string>
	<key>WFControlFlowMode</key>
	<integer>1</integer>
	<key>WFMenuItemAttributedTitle</key>
	<string>Copy Link</string>
	<key>WFMenuItemTitle</key>
	<string>Copy Link</string>
</dict>
```

### Menu end — `is.workflow.actions.choosefrommenu`
```xml
<dict>
	<key>GroupingIdentifier</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-E11A2C3D4E5F</string>
	<key>UUID</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-E11A2C3D4E5F</string>
	<key>WFControlFlowMode</key>
	<integer>2</integer>
</dict>
```

### Get Dictionary Value — `is.workflow.actions.getvalueforkey`
```xml
<dict>
	<key>UUID</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-6A1A2C3D4E5F</string>
	<key>WFDictionaryKey</key>
	<string>data</string>
	<key>WFGetDictionaryValueType</key>
	<string>Value</string>
	<key>WFInput</key>
	<dict>
		<key>Value</key>
		<dict>
			<key>Type</key>
			<string>Variable</string>
			<key>VariableName</key>
			<string>Response</string>
		</dict>
		<key>WFSerializationType</key>
		<string>WFTextTokenAttachment</string>
	</dict>
</dict>
```

### Form+File upload — `is.workflow.actions.downloadurl`
```xml
<dict>
	<key>ShowHeaders</key>
	<false/>
	<key>UUID</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-5A1A2C3D4E5F</string>
	<key>WFFormValues</key>
	<dict>
		<key>Value</key>
		<dict>
			<key>WFDictionaryFieldValueItems</key>
			<array>
				<dict>
					<key>WFItemType</key>
					<integer>5</integer>
					<key>WFKey</key>
					<dict>
						<key>Value</key>
						<dict>
							<key>string</key>
							<string>image</string>
						</dict>
						<key>WFSerializationType</key>
						<string>WFTextTokenString</string>
					</dict>
					<key>WFValue</key>
					<dict>
						<key>Value</key>
						<dict>
							<key>Type</key>
							<string>Variable</string>
							<key>VariableName</key>
							<string>Upload</string>
						</dict>
						<key>WFSerializationType</key>
						<string>WFTextTokenAttachment</string>
					</dict>
				</dict>
				<dict>
					<key>WFItemType</key>
					<integer>0</integer>
					<key>WFKey</key>
					<dict>
						<key>Value</key>
						<dict>
							<key>string</key>
							<string>type</string>
						</dict>
						<key>WFSerializationType</key>
						<string>WFTextTokenString</string>
					</dict>
					<key>WFValue</key>
					<dict>
						<key>Value</key>
						<dict>
							<key>string</key>
							<string>file</string>
						</dict>
						<key>WFSerializationType</key>
						<string>WFTextTokenString</string>
					</dict>
				</dict>
			</array>
		</dict>
		<key>WFSerializationType</key>
		<string>WFDictionaryFieldValue</string>
	</dict>
	<key>WFHTTPBodyType</key>
	<string>Form</string>
	<key>WFHTTPMethod</key>
	<string>POST</string>
	<key>WFURL</key>
	<string>https://api.imgur.com/3/upload</string>
</dict>
```

### QR code — `is.workflow.actions.generatebarcode`
```xml
<dict>
	<key>UUID</key>
	<string>1D0F1C8A-0F7E-4D3E-9E4B-8A1A2C3D4E5F</string>
	<key>WFText</key>
	<dict>
		<key>Value</key>
		<dict>
			<key>attachmentsByRange</key>
			<dict>
				<key>{0, 1}</key>
				<dict>
					<key>Type</key>
					<string>Variable</string>
					<key>VariableName</key>
					<string>Link</string>
				</dict>
			</dict>
			<key>string</key>
			<string>￼</string>
		</dict>
		<key>WFSerializationType</key>
		<string>WFTextTokenString</string>
	</dict>
</dict>
```

### Save to camera roll — `is.workflow.actions.savetocameraroll`
```xml
<dict>
	<key>WFInput</key>
	<dict>
		<key>Value</key>
		<dict>
			<key>OutputName</key>
			<string>QR Code</string>
			<key>OutputUUID</key>
			<string>1D0F1C8A-0F7E-4D3E-9E4B-8A1A2C3D4E5F</string>
			<key>Type</key>
			<string>ActionOutput</string>
		</dict>
		<key>WFSerializationType</key>
		<string>WFTextTokenAttachment</string>
	</dict>
</dict>
```

---

## Things that specifically bite

- **Menu items are dictionaries, not strings.** `WFMenuItems` is an array of
  `{WFItemType: 0, WFValue: "<title>"}`. A bare array of strings is the iOS-12
  form; the current app force-casts it and **crashes**. Each item's branch
  marker (mode 1) carries both `WFMenuItemTitle` and `WFMenuItemAttributedTitle`.
- **Condition codes are integers**, from Cherri's `shortcut.go`: equals 4,
  contains 99, has-any-value 100, does-not-have-any-value 101, begins-with 8,
  ends-with 9, greater 2/3, less 0/1. The has/does-not-have conditions carry no
  comparand.
- **An If's input is wrapped**: `WFInput = {Type: "Variable", Variable: <attachment>}`,
  not a bare attachment like every other action.
- **Block-closing markers** (If end, Menu end; `WFControlFlowMode` 2) carry a
  `UUID` equal to the `GroupingIdentifier`.
- **Set Variable** carries a top-level `WFSerializationType: WFTextTokenAttachment`
  in addition to the one inside `WFInput`.
- **Shortcut Input** references serialize as
  `{Type: "ExtensionInput", VariableName: "ShortcutInput"}`, and the shortcut
  sets `WFWorkflowHasShortcutInputVariables` at the top level.
- **A file in a form body** is `WFItemType: 5` and its `WFValue` is the attachment
  itself (the image variable), not a text token. Text fields are `WFItemType: 0`.
- **Generate QR Code** takes its text in `WFText`, not `WFInput`.
- **Literal text fields are plain strings** (e.g. `WFURL`, `WFTextActionText`,
  alert titles). The `WFTextTokenString` wrapper appears only when the field
  carries a variable attachment.

---

## How to produce a fresh reference with Cherri

For any construct not already proven in this repo, do this rather than guess.
Requires Go.

```sh
git clone --depth 1 https://github.com/electrikmilk/cherri
cd cherri && go build -o /tmp/cherri .
```

Write the shortcut in Cherri (see `actions/*.cherri` for names, `tests/*.cherri`
for syntax), then:

```sh
/tmp/cherri yourfile.cherri --skip-sign --derive-uuids
```

`--derive-uuids` makes the output deterministic so you can diff it. Load the
resulting `.shortcut` with `plistlib` and compare its action parameters to what
your `build.py` emits. Where they differ, Cherri is right. Cherri needs an
`#include 'actions/<lib>'` line per action library (it names the missing one in
the error); action definitions live in `actions/*.cherri`.

---

## Validation checklist before committing a generator

1. Control flow balances: every `WFControlFlowMode` 0 has a matching 2 in the
   same group; groups nest, never interleave.
2. No dangling `OutputUUID`: every `ActionOutput` reference points at an action
   that exists and has that `UUID`.
3. Top-level key set equals one of the two known-good sets above, exactly.
4. Rebuild is byte-identical (UUIDs are fixed constants, not generated).
5. For any construct new to this repo, its shape was confirmed by a Cherri
   compile, not by inspection alone.
6. It is not described as "working" until it has opened on a real device. If a
   new construct is involved, ship a ladder (see `shortcuts/_imgur-ladder/`) and
   let the owner bisect.
