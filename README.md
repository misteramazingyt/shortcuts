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

Shortcut source lives in this repository. Generating the `.shortcut` files is pure
Python and runs anywhere. **Signing is the hard part** — Apple's `shortcuts sign`
requires an Apple Account session that no CI runner can hold, because macOS VMs cannot
sign into iCloud. Signing therefore needs real Apple hardware, at least once.

The whole plan, step by step, is in **[HANDBOOK.md](HANDBOOK.md)** — from powering on a
Mac to running a signed shortcut on your phone. In short:

- **Phase 1:** on a Mac signed into iCloud, `scripts/sign_on_mac.sh` signs everything
  with Apple's own CLI and commits the results to `signed/`. Guaranteed to work.
- **Phase 2 (experimental):** `tools/appleid-key-dumper-macos/` extracts an Apple ID
  signing identity so [`shortcut-sign`](https://github.com/0xilis/shortcut-sign) can
  sign on Linux. If it works, GitHub Actions signs every future push for free.

### CI

`.github/workflows/build.yml` runs on every push to `main`:

1. `scripts/build_and_sign.sh` generates unsigned shortcuts and uploads them as an
   artifact.
2. If the secrets `APPLE_SIGNING_KEY` and `APPLE_AUTH_DATA` exist (set after Phase 2),
   it builds `shortcut-sign`, signs via `scripts/ci_sign.sh`, and commits `signed/`.
3. Without those secrets it just publishes the unsigned artifact — no failure.

The signing secrets never leak: decoded only to temp files readable by the build user,
shredded on exit, never printed, masked in logs. Full security model in
[HANDBOOK.md Part 3](HANDBOOK.md). Installable, signed files live in [`signed/`](signed).

### Running it locally

```sh
./scripts/build_and_sign.sh
```

Generation works on any OS with Python 3. Signing is best effort: on a Mac signed into
iCloud it runs `shortcuts sign --mode anyone`; anywhere else it skips signing and leaves
the unsigned files in `build/unsigned/`. `--mode anyone` rather than `people-who-know-me`,
which would restrict import to the signer's contacts.

## Layout

```
.github/workflows/     CI: build unsigned always, sign when secrets exist
scripts/
    build_and_sign.sh    generate all shortcuts (+ sign locally on macOS)
    sign_on_mac.sh       Phase 1: sign with Apple's CLI on a real Mac
    ci_sign.sh           sign on Linux with shortcut-sign + secrets
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

Nothing needs to change in the CI workflow or `build_and_sign.sh` — any
`shortcuts/*/build.py` is discovered and built automatically.

Builds are deterministic — hold action UUIDs fixed rather than generating them at build
time, so rebuilding unchanged source produces byte-identical output.
