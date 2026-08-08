#!/usr/bin/env python3
"""Control shortcut for the signing experiment.

golden.plist.xml is a real, known-importable shortcut taken verbatim from the
Shortcuts Playground plugin's golden-shortcuts corpus (a Dropbox "pick files,
zip, share" shortcut). We do not care what it does — only whether it imports.

The point: CI signs this with the same key and the same shortcut-sign pipeline
as our own shortcuts. If this control ALSO imports as "invalid", the fault is
the signature, not our generated plist, and no plist fix can help. If it
imports cleanly while ours does not, the fault is our plist and this file is
the template to match.

Emits the golden plist unchanged, as binary — exactly what the signer expects.
"""

import os
import plistlib
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "golden.plist.xml")
OUT_NAME = "Control (Golden).shortcut"


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out_dir, exist_ok=True)
    with open(SOURCE, "rb") as handle:
        workflow = plistlib.load(handle)
    out_path = os.path.join(out_dir, OUT_NAME)
    with open(out_path, "wb") as handle:
        plistlib.dump(workflow, handle, fmt=plistlib.FMT_BINARY)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
