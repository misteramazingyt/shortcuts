# Imgur crash ladder

**Upload to Imgur** crashes the Shortcuts app the moment it is opened, in two
builds, while every other shortcut in this repository opens. Comparing them,
thirteen action types in the Imgur shortcut have never appeared in a working
file here — and without a device there is no way to know which one the app dies
on. This ladder finds out.

Seven shortcuts. Rung 1 is the exact skeleton of a working shortcut plus the
first new construct. Each rung after it adds one more. **Open them in order.
The first one that crashes names the culprit**, and everything below it is
cleared for good.

| Rung | Adds | Download (signed) |
| --- | --- | --- |
| 1 | a named variable — Set Variable, Show Result | [Imgur Ladder 1](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%201.shortcut) |
| 2 | If / Otherwise on Shortcut Input | [Imgur Ladder 2](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%202.shortcut) |
| 3 | Choose from Menu, Show Notification | [Imgur Ladder 3](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%203.shortcut) |
| 4 | Select Photos, Get Details of Images, Convert Image | [Imgur Ladder 4](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%204.shortcut) |
| 5 | the upload: Get Contents of URL with a Form body and a File field, Get Dictionary Value, Copy to Clipboard | [Imgur Ladder 5](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%205.shortcut) |
| 6 | Show Alert, Stop This Shortcut, Generate QR Code, Save to Photo Album | [Imgur Ladder 6](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%206.shortcut) |
| 7 | nothing new in the actions — this is **Upload to Imgur v2**'s full action list under the *top-level dictionary a current Shortcuts app writes* (client version 4033) instead of the 2018-era one every other file here carries | [Imgur Ladder 7](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Imgur%20Ladder%207.shortcut) |

Rungs 1–6 keep the same top-level dictionary as the working shortcuts, so from
one rung to the next only the actions change. Rung 7 keeps the actions and
changes only the top-level.

You only need to **open** each one — the crash is on open. Don't run rung 5 or
later to the end; from there on they would upload a photo.

## What to report

Just the number of the first rung that crashes — or "all seven open", which
would itself be an answer, because rung 7 *is* Upload to Imgur v2 with a
different top-level, and rung 6 is nearly all of it with the old one.

## Why rung 7 exists

Every working shortcut here, and the golden control, is stamped as a 2018-era
file (`WFWorkflowClientVersion` 736). The Imgur shortcut carries that same stamp
but is full of constructs from later versions — menus, Ifs, named variables. A
file that old is a candidate for the app's migration path for old shortcuts,
and a migrator that meets a modern structure where it expects a legacy one is a
plausible way to crash rather than error. Rung 7 removes that variable by using
the exact key set of a shortcut the current app exported itself.

## Rebuilding

```sh
python3 shortcuts/_imgur-ladder/build.py
```

Delete this folder once the culprit is found and fixed.
