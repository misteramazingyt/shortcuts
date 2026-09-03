---
name: new-shortcut
description: >-
  Build, change, or debug an iOS Shortcut (.shortcut file) in this repository.
  Use this WHENEVER the task touches anything under shortcuts/, tools/shortcut_builder.py,
  or a .shortcut file — creating a new shortcut, editing an existing one, or diagnosing
  one that iOS rejects or crashes on. It exists because a .shortcut is a binary plist
  whose exact serialization the Shortcuts app is brutally unforgiving of: a plausible-looking
  guess crashes the app on open rather than erroring. This skill forces you to start
  from ground truth instead of guessing.
---

# Building a shortcut in this repo — start from ground truth

A `.shortcut` file is a binary property list describing an ordered list of
actions. The Shortcuts app does **not** validate and reject a malformed one
gracefully — a wrong serialization can **crash the app the instant the file is
opened**, before anything renders. This has happened here, twice, from
plausible guesses. So the rule for this repo is absolute:

> **Never hand-invent a serialization. Every action shape, every parameter key,
> every enum value must come from a file a real tool actually produced. If you
> cannot point to where a shape came from, you do not ship it.**

You are a coding agent. Guessing a plist shape from memory and committing it as
a working shortcut is the specific failure this skill exists to stop. Do not do
it.

## The three ground-truth sources, in order of authority

1. **A shortcut the Shortcuts app exported itself.**
   `shortcuts/_control-golden/golden.plist.xml` is a real Apple export, checked
   into this repo precisely as a known-importable reference. Its top-level key
   set and its action shapes are authoritative. When in doubt, match it.

2. **The Cherri compiler** (`github.com/electrikmilk/cherri`, GPL). Cherri
   compiles a small language to `.shortcut` files and decompiles real ones, so
   its source is a maintained, tested map from "action" to "plist shape",
   current to iOS 26. Use it two ways:
   - Read `actions/*.cherri` for an action's exact parameter names and its enum
     values, and `shortcut.go` / `shortcutgen.go` for the serialization of
     control flow, variables, dictionaries and the top-level.
   - **Build the equivalent program and compile it.** For anything non-trivial,
     write the shortcut in Cherri, compile it with `--skip-sign --derive-uuids`,
     and diff the resulting plist against what your `build.py` emits. This is
     how the reference plist beside this skill was produced. Steps are in
     [`reference/GROUND-TRUTH.md`](reference/GROUND-TRUTH.md).

3. **`reference/GROUND-TRUTH.md`** beside this skill: the verified serializations
   already extracted from sources 1 and 2 — control flow, menus, conditionals,
   variable references, form/file bodies, the two valid top-level dictionaries —
   with the exact bytes and the reason each matters. Read it before writing a
   generator. It is the distilled result so you do not have to re-derive what is
   already known.

Memory, blog posts, and "this looks right" are **not** sources. shortcuts-js is
a useful cross-check but is years old; where it disagrees with a fresh Cherri
compile or the golden file, it loses.

## The process, every time

1. **Read `reference/GROUND-TRUTH.md` and skim `tools/shortcut_builder.py`.**
   The builder already encodes verified shapes for actions, control flow
   (`if_start`/`menu_start`/…), variables, dictionaries and file-upload form
   fields. Reuse them. If you need an action the builder doesn't cover, get its
   shape from a ground-truth source and add a helper — do not inline a guess.
2. **Model an existing shortcut.** Copy the structure of the closest working
   `shortcuts/*/build.py`. Hold UUIDs fixed so rebuilds are byte-identical.
3. **For any construct not already used by a working shortcut in this repo,
   confirm its shape with a Cherri compile before writing it.** "Working in this
   repo" is the bar: a construct no committed shortcut uses is unproven here,
   regardless of how sure you feel.
4. **Validate structurally.** Control flow balances (every `WFControlFlowMode` 0
   has a matching 2, groups nest); no dangling output UUIDs; the top-level key
   set matches one of the two known-good sets in the reference. There is a
   checklist at the end of the reference doc.
5. **Prove it against the app before calling it done — you cannot test on a
   device from here, so do not claim it works.** Build it, sign via CI, and have
   the owner open it. If a new construct is involved and there is any doubt, ship
   a **ladder**: a series of shortcuts starting from a known-working skeleton,
   each adding one construct, so the first one that crashes names the culprit.
   `shortcuts/_imgur-ladder/` is the worked example. Bisecting on-device beats
   guessing every time.
6. **Only after it opens on the device**, describe it as working. Until then it
   is a candidate.

## Repo conventions (also in `CLAUDE.md`)

- Work on `main`, commit to `main`, push to `main`. No branches, no PRs.
- Every `shortcuts/*/build.py` is discovered and built by CI automatically;
  pushing to `main` is what signs and publishes. Rebuild the committed copy with
  `python3 shortcuts/<name>/build.py` whenever a generator changes.
- Add a shortcut's row to the **top** of the table in `README.md` (newest-first)
  with today's date in the Last edited column.
- Do not create throwaway shortcuts elsewhere on the system. Everything lives
  under `shortcuts/<name>/` with a `build.py` and a `README.md`, generated from
  source, so nothing is an orphan.

## Do not

- Do not write a `.shortcut` plist by hand or from memory.
- Do not invent a parameter key or an enum value. Find it in a source.
- Do not tell the owner a shortcut works before it has opened on their device.
- Do not leave generated shortcuts scattered outside `shortcuts/`.
- Do not add top-level keys "to be safe" — extra keys have caused rejections
  here. Match a known-good key set exactly.
