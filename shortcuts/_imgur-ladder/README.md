# Imgur crash bisect — two rungs

**Upload to Imgur** crashes the Shortcuts app the instant it is opened, and I
cannot test on a device. So we bisect. Two shortcuts, same top-level dictionary
as every working shortcut here, differing only in how many actions they carry:

These are the real Upload to Imgur action list cut in two. A followed by B is
byte-for-byte the same 39 actions as the shortcut on the homepage; each half is
balanced on its own and opens on its own.

| Rung | What it contains | Download (signed) |
| --- | --- | --- |
| **Imgur A** (first half, 16 actions) | The setup: client-ID text + Set Variable, pick the image (If on Shortcut Input), convert to JPEG if HEIC (If on the extension). Ends having chosen what to upload. | [Imgur A](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20A.shortcut) |
| **Imgur B** (second half, 23 actions) | The upload (Form request with the image as a File field, two dictionary lookups, failure alert) and the menu (Copy Link / Save QR Code, with its notification and QR-code actions). | [Imgur B](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B.shortcut) |

## Do this

Open both. Just open them — the crash is on open, and neither uploads anything.
Then tell me which of these happened:

- **A opens, B crashes** → the culprit is in the second half (upload / menu /
  QR). I cut B in two and send the next pair.
- **A crashes, B opens** → the culprit is in the first half (pick image /
  convert). I cut A in two.
- **Both crash** → each half has a problem, or the problem is a construct both
  share (both use If blocks). I cut whichever is simpler first.
- **Both open** → neither half alone crashes, so the crash needs the whole
  thing present — size, or the header. I bring in a modern-header rung next.

Whichever rung misbehaves, I subdivide *that* rung and we repeat. Each round
halves what's left, so this converges fast.

## Why same header on both

The full shortcut carries the same legacy top-level (`WFWorkflowClientVersion`
736) as every working shortcut in this repo. Keeping both rungs on that header
means the only variable between them is the action list — so when one crashes,
it is the actions, not the header. The header is a separate hypothesis, tested
on its own later if both rungs open.

## Rebuilding

```sh
python3 shortcuts/_imgur-ladder/build.py
```

Delete this folder once the culprit is found and fixed.
