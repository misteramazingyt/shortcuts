# Imgur crash bisect — round 2 (splitting the second half)

**Round 1:** the first half of Upload to Imgur (pick image, convert) **opened**;
the second half (upload + menu) **crashed**. So the culprit is in the second
half. This round cuts that in two. Same header; B1 then B2 is byte-for-byte the
second half.

| Rung | What it contains | Download (signed) |
| --- | --- | --- |
| **Imgur B1** (the upload, 14 actions) | The If that chooses anonymous vs client-ID, the two Get-Contents-of-URL requests (Form body, image as a File field), the two dictionary lookups (`data` → `link`), the failure alert. | [Imgur B1](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B1.shortcut) |
| **Imgur B2** (the menu, 9 actions) | Choose from Menu; Copy to Clipboard + notification on one branch; Generate QR Code + Save to Photo Album + notification on the other. | [Imgur B2](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20B2.shortcut) |

## Do this

Open both. Tell me which crashes:

- **B1 crashes** → the fault is in the upload actions (the Form/File request, the
  dictionary lookups, or the alert/exit). I split B1 next.
- **B2 crashes** → the fault is in the menu actions (Choose from Menu, the QR
  code, Save to Photo Album). I split B2 next.
- **Both crash** → each half has a problem, or one they share; I cut the simpler
  one (B2) first.

Only open them; neither uploads.

## Rebuilding

```sh
python3 shortcuts/_imgur-ladder/build.py
```

Delete this folder once the culprit is found and fixed.
