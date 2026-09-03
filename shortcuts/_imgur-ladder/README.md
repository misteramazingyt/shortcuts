# Imgur crash bisect — round 5 (verify the fix)

The bisect landed on the culprit: **the image sent as a Form File field**
(`WFItemType 5`). B1a-2 (image as a text field) opened; B1a-3 (image as a File
field) crashed. The File field's value was serialized with only its inner
`WFTextTokenAttachment` and no outer `WFTokenAttachmentParameterState` wrapper —
the app force-casts that and dies on open.

Ground truth (a documented working Whisper-API multipart upload in the
[julian-englert/apple-shortcuts](https://github.com/julian-englert/apple-shortcuts)
decompiler notes) shows the correct two-layer shape. `tools/shortcut_builder.py`
is fixed to emit it.

| Test | What it is | Download (signed) |
| --- | --- | --- |
| **Imgur File Fixed** | The exact B1a-3 request — single POST, Form body, image as a File field — with the corrected serialization. | [Imgur File Fixed](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20File%20Fixed.shortcut) |

## Do this

Open it. If it **opens**, the File field is fixed — and because the real
**Upload to Imgur v2** uses the same builder, that shortcut is fixed too, so try
it next. If it still **crashes**, tell me; the fix is wrong and I keep going.

Only open it; it does not upload.

## Rebuilding

```sh
python3 shortcuts/_imgur-ladder/build.py
```

Delete this folder once Upload to Imgur v2 is confirmed working on the device.
