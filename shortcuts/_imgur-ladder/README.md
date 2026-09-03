# Imgur crash bisect — round 4 (four revisions of the request)

Trail: second half → upload block → request half (B1a) crashes; the parse half
(B1b) opens. B1a is an If around two Get-Contents-of-URL requests with a Form
body. Instead of halving again, here are **four revisions of a single request**,
each adding one thing to the last. Open them in order; the first that crashes
names the exact addition responsible.

| # | Adds | Download (signed) |
| --- | --- | --- |
| **B1a-1** | a bare POST to the URL, no body at all | [B1a-1](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1a-1.shortcut) |
| **B1a-2** | + a Form body of text items (image sent as text) | [B1a-2](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1a-2.shortcut) |
| **B1a-3** | + the image as a **File field** (`WFItemType 5`) — what the real shortcut does | [B1a-3](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1a-3.shortcut) |
| **B1a-4** | + the Authorization headers dictionary | [B1a-4](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1a-4.shortcut) |

## What each outcome means

- **B1a-1 crashes** → Get-Contents-of-URL itself is serialized wrong here.
- **1 opens, B1a-2 crashes** → the Form body is the problem, not the File field.
- **2 opens, B1a-3 crashes** → the **File field** (`WFItemType 5`) is the bug —
  the value I took from a web claim instead of ground truth. I replace how the
  image is attached and the real shortcut is fixed.
- **3 opens, B1a-4 crashes** → the headers dictionary is the bug.
- **all four open** → the crash needs the If wrapper or both requests together;
  I go back and split B1a that way.

The real shortcut's two requests are B1a-3 (anonymous) and B1a-4 (client-ID), so
whichever of those first crashes is the actual defect.

Only open them; none upload.

## Rebuilding

```sh
python3 shortcuts/_imgur-ladder/build.py
```

Delete this folder once the culprit is found and fixed.
