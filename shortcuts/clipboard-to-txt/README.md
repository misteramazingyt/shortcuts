# Clipboard to TXT

Takes whatever text is on the clipboard, turns it into a `.txt` file, and opens the
share sheet with that file attached. From there you can AirDrop it, mail it, drop it
in Messages, or hand it to any app that accepts files.

Two builds are included. Start with the first.

| File | Writes to disk? | Use when |
| --- | --- | --- |
| [`Clipboard to TXT.shortcut`](Clipboard%20to%20TXT.shortcut) | No | Default. Nothing is left behind. |
| [`Clipboard to TXT (Save to Files).shortcut`](Clipboard%20to%20TXT%20%28Save%20to%20Files%29.shortcut) | `iCloud Drive/Shortcuts/Clipboard.txt` | Fallback, if some app refuses the in-memory file. |

Both produce a file named `Clipboard.txt`. The save-to-Files build overwrites the same
path every run, so it never accumulates copies.

## Install

1. On your iPhone or iPad, signed in to GitHub, tap one of the file links above.
2. Tap **Download raw file** (the ⤓ icon at the top right of the file box). While this
   repo is private, `raw.githubusercontent.com` links return 404 without an access
   token, so this is the way to get the file onto the device.
3. Open the download from Files. Shortcuts will offer to add it.
4. If iOS refuses the import, turn on **Settings → Shortcuts → Allow Untrusted
   Shortcuts** and try again. That toggle only appears once you have run at least one
   shortcut on the device, so run any shortcut first if you don't see it.

## How the no-save build works

The interesting part is getting a *file* out of Shortcuts without saving one:

1. **Get Clipboard**
2. **Text** — the clipboard is passed through a text field, which coerces a copied URL
   or rich text down to plain text instead of carrying its original type forward.
3. **Base64 Encode**
4. **Base64 Decode** — decoding hands back a data blob rather than a string. This is
   the whole trick: the share sheet treats a blob as an attachment, but treats a string
   as message body text.
5. **Set Name** → `Clipboard.txt`, with "Don't include file extension" off, so the
   extension sticks and the blob is typed as text.
6. **Share**

The save-to-Files build swaps steps 3–4 for **Save File** (ask-where-to-save off,
overwrite on) followed by **Get File**, so the share sheet receives a genuine on-disk
file. It needs iCloud Drive enabled.

## Building it by hand

If you would rather assemble it in the Shortcuts app than import a file, the six
actions above are the entire shortcut — add them in that order and leave every input
field untouched. Shortcuts feeds each action the previous one's output automatically.

## Rebuilding the files

```sh
python3 shortcuts/clipboard-to-txt/build.py
```

The build is deterministic — unchanged source produces byte-identical `.shortcut`
files, so a rebuild shows up in `git status` only when something really changed.
