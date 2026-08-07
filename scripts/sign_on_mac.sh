#!/usr/bin/env bash
#
# Sign every shortcut and commit the results. Run this on a rented bare-metal
# Mac that is signed into iCloud.
#
#   ./scripts/sign_on_mac.sh
#
# Why a rented Mac: iOS 26 refuses to import unsigned shortcut files at all
# ("importing unsigned shortcut files is not supported"), so signing is now
# mandatory. `shortcuts sign` needs an Apple Account session, and macOS VMs
# cannot hold one — which rules out every CI runner, Codemagic included. Only
# real hardware works.
#
# Signed files land in signed/ and are committed, so the iPhone can install
# them straight from GitHub. One session signs an unlimited number of
# shortcuts, so batch them up and rent the machine rarely.

set -euo pipefail
shopt -s nullglob

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIGNED_OUT="$REPO_ROOT/signed"

cd "$REPO_ROOT"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: macOS only. This is the step that needs real Apple hardware." >&2
    exit 1
fi

if ! command -v shortcuts >/dev/null 2>&1; then
    echo "ERROR: Apple's 'shortcuts' CLI is missing. Needs macOS 12 or later." >&2
    exit 1
fi

# Fail early and clearly rather than midway through signing.
if [[ "$(defaults read MobileMeAccounts Accounts 2>/dev/null | grep -c 'AccountID' || true)" -eq 0 ]]; then
    cat >&2 <<'MSG'
ERROR: no Apple Account is signed in on this Mac.

  Open System Settings, sign in with your Apple Account, and approve the
  two-factor prompt on your iPhone. Then run this script again.

  If sign-in hangs or reports an unknown error, this machine is a virtual
  machine, not real hardware. Signing cannot work there — no setting fixes it.
MSG
    exit 1
fi

echo "==> Generating and signing"
./scripts/build_and_sign.sh

signed=("$REPO_ROOT"/build/signed/*.shortcut)
if [[ ${#signed[@]} -eq 0 ]]; then
    echo "ERROR: nothing was signed. See the output above." >&2
    exit 1
fi

echo ""
echo "==> Publishing ${#signed[@]} signed shortcut(s) to signed/"
rm -rf "$SIGNED_OUT"
mkdir -p "$SIGNED_OUT"
for file in "${signed[@]}"; do
    cp "$file" "$SIGNED_OUT/"
    echo "    $(basename "$file")"
done

echo ""
echo "==> Committing"
git add signed
if git diff --cached --quiet; then
    echo "    no changes — signed files already up to date"
else
    git -c user.name="Shortcut Signer" -c user.email="noreply@example.com" \
        commit -q -m "Publish signed shortcuts"
    git push -u origin HEAD
    echo "    pushed"
fi

cat <<'DONE'

================================================================
  Done. Install on the iPhone from the signed/ directory:

    https://github.com/misteramazingyt/shortcuts/tree/main/signed

  Open a file's raw link in Safari on the phone. Because these are
  signed, they now import instead of being rejected.
================================================================
DONE
