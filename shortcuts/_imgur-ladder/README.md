# Imgur crash bisect — round 3 (splitting the upload block)

Trail: round 1 → second half crashes; round 2 → the upload block (B1) crashes,
the menu (B2) opens. This round cuts the upload block at its one seam. Same
header; B1a then B1b is byte-for-byte the upload block.

| Rung | What it contains | Download (signed) |
| --- | --- | --- |
| **Imgur B1a** (the request, 7 actions) | The If choosing anonymous vs client-ID, and inside it the two Get-Contents-of-URL actions whose body is a **Form with the image as a File field**. This is the one construct nothing else in this repo uses — the prime suspect. | [Imgur B1a](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1a.shortcut) |
| **Imgur B1b** (the parse, 7 actions) | Get Dictionary Value for `data` then `link`, Set Variable, and the "no link → alert, stop" If. | [Imgur B1b](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1b.shortcut) |

## Do this

Open both. Tell me which crashes:

- **B1a crashes** → it is the Form / File request body. That is almost certainly
  the bug. Next I test a plain request, then the File field on its own, to fix
  how that field is serialized.
- **B1b crashes** → it is Get Dictionary Value or the alert/stop. I split B1b.

Only open them; neither uploads.

## Rebuilding

```sh
python3 shortcuts/_imgur-ladder/build.py
```

Delete this folder once the culprit is found and fixed.
