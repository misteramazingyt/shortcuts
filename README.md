# Shortcuts

iOS Shortcuts, versioned as source and built into installable `.shortcut` files.

## The shortcuts

Newest at the top — the first row is always whatever was worked on most recently.
The **Last edited** column is the time of the most recent commit to that
shortcut's folder; each one links to the folder's commit history on GitHub, so
the exact change is one click away.

| Shortcut | What it does | Get it | Docs | Last edited |
| --- | --- | --- | --- | --- |
| **Imgur crash bisect** — _diagnostic_ | Two shortcuts to find what crashes Upload to Imgur, both on the working header so they differ only in how many actions they carry. **A** is the control-flow half (variable, If, menu); **B** is the whole thing. **Open both, tell me which crashes** — then I split that one and we repeat. Only open them; neither uploads. | Download [A](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20A.shortcut) · [B](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B.shortcut) | [Read](shortcuts/_imgur-ladder/) | **2026-09-03 01:14 UTC** · [history](https://github.com/misteramazingyt/shortcuts/commits/main/shortcuts/_imgur-ladder) |
| **Upload to Imgur v2** — _crashes on open; being bisected by the ladder above_ | Uploads an image to Imgur anonymously (API v3, `POST /3/upload`) and offers the link on the clipboard or a QR code of it saved to Photos. No setup, no account, no client ID. **v2** fixes a crash on open in the first build (menu items were serialized in an obsolete format); it imports under the name *Upload to Imgur v2*, so you can tell at a glance which build you have. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Upload%20to%20Imgur%20v2.shortcut) | [Read](shortcuts/imgur-upload/) | **2026-09-03 01:03 UTC** · [history](https://github.com/misteramazingyt/shortcuts/commits/main/shortcuts/imgur-upload) |
| **Clipboard to TXT (Save to Files)** | Turns clipboard text into a `.txt` file and opens the share sheet with it, writing `iCloud Drive/Shortcuts/Clipboard.txt` first. Fallback if an app refuses the in-memory file. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Clipboard%20to%20TXT%20%28Save%20to%20Files%29.shortcut) | [Read](shortcuts/clipboard-to-txt/) | 2026-08-09 19:53 UTC · [history](https://github.com/misteramazingyt/shortcuts/commits/main/shortcuts/clipboard-to-txt) |
| **Clipboard to TXT** | Same, entirely in memory. Nothing is saved to disk. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Clipboard%20to%20TXT.shortcut) | [Read](shortcuts/clipboard-to-txt/) | 2026-08-09 19:53 UTC · [history](https://github.com/misteramazingyt/shortcuts/commits/main/shortcuts/clipboard-to-txt) |
| **Read Clipboard (Audiobook)** | Sends clipboard text to an n8n webhook (Lemonfox TTS at 2×) and opens the returned audio in VLC. Holds no credentials — the API key stays in n8n. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Read%20Clipboard%20%28Audiobook%29.shortcut) | [Read](shortcuts/audiobook/) | 2026-08-08 02:08 UTC · [history](https://github.com/misteramazingyt/shortcuts/commits/main/shortcuts/audiobook) |
| **Control (Golden)** — _signing test_ | A known-importable Apple-ecosystem shortcut, signed by the same pipeline. Import it next to Clipboard to TXT: if this one works and that one doesn't, the fault is our shortcut; if both say "invalid", the fault is the signing method. | [Download](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Control%20%28Golden%29.shortcut) | [Read](shortcuts/_control-golden/) | 2026-08-08 01:30 UTC · [history](https://github.com/misteramazingyt/shortcuts/commits/main/shortcuts/_control-golden) |

> The **Download** links serve the **signed** builds from [`signed/`](signed), produced
> automatically by CI. The unsigned source plists live under each shortcut's folder.

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
4. Add a row at the **top** of the table above, with today's date. The table is
   newest-first; when you rework an existing shortcut, move its row to the top
   and update the date.

Nothing needs to change in the CI workflow or `build_and_sign.sh` — any
`shortcuts/*/build.py` is discovered and built automatically.

Builds are deterministic — hold action UUIDs fixed rather than generating them at build
time, so rebuilding unchanged source produces byte-identical output.
