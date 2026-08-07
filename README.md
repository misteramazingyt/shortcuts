# Shortcuts

iOS Shortcuts, versioned as source and built into installable `.shortcut` files.

## The shortcuts

| Shortcut | What it does | Get it | Docs |
| --- | --- | --- | --- |
| **Clipboard to TXT** | Turns clipboard text into a `.txt` file and opens the share sheet with it attached. Nothing is saved to disk. | [Download](shortcuts/clipboard-to-txt/Clipboard%20to%20TXT.shortcut) | [Read](shortcuts/clipboard-to-txt/) |
| **Clipboard to TXT (Save to Files)** | Same, but writes `iCloud Drive/Shortcuts/Clipboard.txt` first. Fallback if an app refuses the in-memory file. | [Download](shortcuts/clipboard-to-txt/Clipboard%20to%20TXT%20%28Save%20to%20Files%29.shortcut) | [Read](shortcuts/clipboard-to-txt/) |

## Installing

1. On your iPhone or iPad, signed in to GitHub, tap a **Download** link above. It opens
   the file's page here.
2. Tap **Download raw file** (the ⤓ icon, top right of the file box).
3. Open the download from Files and let Shortcuts add it.

While this repo is private, `raw.githubusercontent.com` links do not work — they return
404 without an access token, which is why the links above point at the file pages
instead. If you make the repo public, direct one-tap links become possible in the form
`https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/<path>`.

These shortcuts are unsigned, so iOS may ask you to enable **Settings → Shortcuts →
Allow Untrusted Shortcuts** first. That toggle only appears after you have run at least
one shortcut on the device.

Every shortcut's docs also list its actions in order, so you can rebuild it by hand in
the Shortcuts app instead of importing anything.

## Layout

```
shortcuts/<name>/
    README.md            what it does, how to install, how it works
    build.py             the shortcut's definition in Python
    *.shortcut           the built, installable files (committed)
tools/
    shortcut_builder.py  shared plist-generation helpers
```

A `.shortcut` file is a property list describing an ordered list of actions. Editing
that by hand is miserable, so each shortcut is defined in a small Python file and the
binary is generated from it. The generated files are committed so they can be
downloaded straight from GitHub.

## Adding a shortcut

1. Create `shortcuts/<name>/build.py` using an existing one as a model.
2. Run it: `python3 shortcuts/<name>/build.py`.
3. Write `shortcuts/<name>/README.md`.
4. Add a row to the table above.

Builds are deterministic — hold action UUIDs fixed rather than generating them at build
time, so rebuilding unchanged source produces byte-identical output.
