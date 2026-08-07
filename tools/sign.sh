#!/bin/bash
# Sign every built .shortcut file in place. macOS only.
#
# Signing is not certificate-based: `shortcuts sign` uses the Apple ID logged
# into this Mac and sends a copy to Apple for validation. There is no key to
# inject, so this cannot run on a GitHub-hosted runner — it needs a Mac signed
# into iCloud, either yours or a self-hosted runner.
#
# Mode is `anyone` rather than `people-who-know-me`, which would restrict
# importing to people who have the signer in their Contacts.
#
# Usage: tools/sign.sh

set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
    echo "sign.sh: macOS only — the shortcuts CLI does not exist here." >&2
    exit 1
fi

if ! command -v shortcuts >/dev/null; then
    echo "sign.sh: no 'shortcuts' command; needs macOS 12 or later." >&2
    exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
signed=0

while IFS= read -r -d '' file; do
    tmp="${file}.signing"
    # `shortcuts sign` has been seen to exit 0 while writing nothing, so sign to
    # a temporary path and only replace the original once it holds something.
    if shortcuts sign --mode anyone --input "$file" --output "$tmp" && [[ -s "$tmp" ]]; then
        mv "$tmp" "$file"
        echo "signed $(basename "$file")"
        signed=$((signed + 1))
    else
        rm -f "$tmp"
        echo "FAILED  $(basename "$file")" >&2
        exit 1
    fi
done < <(find "$repo_root/shortcuts" -name '*.shortcut' -print0)

echo "$signed file(s) signed."
