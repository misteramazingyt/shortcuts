# Imgur crash bisect — two rungs

**Upload to Imgur** crashes the Shortcuts app the instant it is opened, and I
cannot test on a device. So we bisect. Two shortcuts, same top-level dictionary
as every working shortcut here, differing only in how many actions they carry:

| Rung | What it contains | Download (signed) |
| --- | --- | --- |
| **Imgur A** | The control-flow half: a named variable, If / Otherwise on Shortcut Input, Choose from Menu, Show Notification, Show Result. No image work, no upload, no QR. | [Imgur A](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20A.shortcut) |
| **Imgur B** | The full Upload to Imgur action list, on the same header. The whole thing. | [Imgur B](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B.shortcut) |

## Do this

Open both. Just open them — the crash is on open, and neither uploads anything.
Then tell me which of these happened:

- **A opens, B crashes** → the fault is in the actions B adds (image / upload /
  QR). I split B into two and send the next pair.
- **A crashes** → a core construct (variable, If, or menu) is wrong. I split A
  down toward the single culprit.
- **Both open** → every action is fine; the crash is something the full file has
  that these don't (its header or size). I bring in a modern-header rung next.
- **Both crash** → even the small control-flow shortcut dies, which points at
  something fundamental in how these are built or signed. That too is an answer.

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
