# Shortcuts

iOS Shortcuts, versioned as source and built into installable `.shortcut` files.

## The shortcuts

| Shortcut | What it does | Get it | Docs |
| --- | --- | --- | --- |
| **Clipboard to TXT** | Turns clipboard text into a `.txt` file and opens the share sheet with it attached. Nothing is saved to disk. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/clipboard-to-txt/Clipboard%20to%20TXT.shortcut) | [Read](shortcuts/clipboard-to-txt/) |
| **Clipboard to TXT (Save to Files)** | Same, but writes `iCloud Drive/Shortcuts/Clipboard.txt` first. Fallback if an app refuses the in-memory file. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/clipboard-to-txt/Clipboard%20to%20TXT%20%28Save%20to%20Files%29.shortcut) | [Read](shortcuts/clipboard-to-txt/) |

## Installing

Tap a **Download** link on your iPhone or iPad. Safari saves the file, and opening it
from Safari's downloads (or from Files) hands it to Shortcuts, which offers to add it.

Two things that trip this up:

- **Use Safari, not the GitHub mobile app.** The app cannot download binary files and
  shows a blank preview instead. If you are reading this in the app, long-press a
  Download link and choose *Open in Safari*.
- These are unsigned shortcuts, so iOS needs **Settings → Shortcuts → Private Sharing**
  turned on. On iOS 26 and later that toggle replaced the old *Allow Untrusted
  Shortcuts* setting; on earlier versions look for the old name, which stays hidden
  until you have run at least one shortcut on the device.

Every shortcut's docs also list its actions in order, so you can rebuild it by hand in
the Shortcuts app instead of importing anything.

## Building and signing Apple Shortcuts

Shortcut source lives in this repository, and signed builds are produced by Codemagic
on a macOS runner. The lifecycle:

1. Edit a shortcut's source under `shortcuts/<name>/`.
2. Push to `main`.
3. Codemagic starts a Mac mini M2 runner automatically.
4. `scripts/build_and_sign.sh` runs every generator, writing unsigned files to
   `build/unsigned/`.
5. Apple's `shortcuts sign --mode anyone` signs each one into `build/signed/`.
6. The signed `.shortcut` files are downloadable from that build's **Artifacts** in
   Codemagic.

Signed files are artifacts only — CI never commits them back, which would retrigger
itself. Source belongs in Git, build products belong in Codemagic.

Documentation-only pushes are skipped so they do not spend Mac minutes. Any change to
shortcut source, a generator, the build script, or `codemagic.yaml` builds normally.

### Running it locally

```sh
./scripts/build_and_sign.sh
```

Generation works on any OS with Python 3. **Signing requires macOS** — `shortcuts` is
an Apple CLI built into macOS 12 and later with no Linux or Windows equivalent. On a
non-Mac the script generates `build/unsigned/` and then stops with an explicit error
rather than appearing to succeed.

Signing uses `--mode anyone`. The alternative, `people-who-know-me`, only lets people
who have the signer in their Contacts import the file.

## Layout

```
codemagic.yaml           CI definition: trigger, build, publish artifacts
scripts/
    build_and_sign.sh    the single build + sign entrypoint
shortcuts/<name>/
    README.md            what it does, how to install, how it works
    build.py             the shortcut's definition in Python — the source of truth
    *.shortcut           unsigned build, committed so the links above work
tools/
    shortcut_builder.py  shared plist-generation helpers
build/                   generated, git-ignored
    unsigned/            output of the generators
    signed/              output of `shortcuts sign`, collected as CI artifacts
```

A `.shortcut` file is a property list describing an ordered list of actions. Editing
that by hand is miserable, so each shortcut is defined in a small Python file and the
binary is generated from it.

The unsigned `.shortcut` files stay committed next to their source because the download
links above serve them straight from GitHub. `build_and_sign.sh` never touches them: it
directs the generators at `build/unsigned/` instead, so signing cannot modify source.

## Adding a shortcut

1. Create `shortcuts/<name>/build.py` using an existing one as a model. It must accept
   an optional output-directory argument and default to its own directory.
2. Run `python3 shortcuts/<name>/build.py` to refresh the committed copy.
3. Write `shortcuts/<name>/README.md`.
4. Add a row to the table above.

Nothing needs to change in `codemagic.yaml` or `build_and_sign.sh` — any
`shortcuts/*/build.py` is discovered and built automatically.

Builds are deterministic — hold action UUIDs fixed rather than generating them at build
time, so rebuilding unchanged source produces byte-identical output.
