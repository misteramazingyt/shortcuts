#!/usr/bin/env bash
#
# Compile the macOS key dumper, self-sign it with the entitlement it needs, and
# run it. Produces authData.plist and privateKey.bin — the two files that let
# shortcut-sign sign shortcuts on Linux, with no Apple hardware, forever after.
#
#   ./build_and_dump.sh [OUTPUT_DIR]     (default: ~/appleid-dump)
#
# PREREQUISITES, in order — the dump fails without all three:
#   1. This Mac is signed into iCloud (System Settings > Apple Account).
#   2. SIP is disabled          (csrutil disable, from Recovery).
#   3. AMFI is disabled         (sudo nvram boot-args="amfi_get_out_of_my_way=0x1"; reboot).
# See README.md in this directory for the full walkthrough and how to undo them.
#
# Untested: written from upstream source without a Mac to run it on. If a step
# fails, the error text and README are your guide.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${1:-$HOME/appleid-dump}"
BIN="$HERE/appleid-key-dumper"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: macOS only." >&2
    exit 1
fi

echo "==> Compiling"
# Link the private Sharing framework that defines SFAppleIDAccount.
clang -fobjc-arc \
    -framework Foundation \
    -framework Security \
    -F /System/Library/PrivateFrameworks \
    -framework Sharing \
    -I "$HERE" \
    "$HERE/main.m" \
    -o "$BIN"

echo "==> Self-signing with entitlement"
# Ad-hoc signature carrying the keychain-access-group entitlement. This is the
# claim that only runs with AMFI disabled.
codesign --force --sign - --entitlements "$HERE/entitlements.plist" "$BIN"

echo "==> Entitlements on the binary:"
codesign -d --entitlements :- "$BIN" 2>/dev/null || true

echo "==> Running"
"$BIN" "$OUT_DIR"

echo ""
if [[ -s "$OUT_DIR/privateKey.bin" && -s "$OUT_DIR/authData.plist" ]]; then
    echo "SUCCESS. Two files written to $OUT_DIR:"
    ls -l "$OUT_DIR/privateKey.bin" "$OUT_DIR/authData.plist"
    echo ""
    echo "These are secret. Do not commit them. Base64 them into GitHub Actions"
    echo "secrets APPLE_SIGNING_KEY and APPLE_AUTH_DATA — see ../../scripts/mac_day.md."
else
    echo "Did not produce both files. Read the errors above against README.md." >&2
    exit 1
fi
