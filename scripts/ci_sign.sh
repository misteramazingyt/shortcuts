#!/usr/bin/env bash
#
# Sign shortcuts on Linux with shortcut-sign, using the Apple ID signing key and
# auth data supplied as base64 in two environment variables:
#
#   APPLE_SIGNING_KEY   base64 of privateKey.bin   (shortcut-sign -k)
#   APPLE_AUTH_DATA     base64 of authData.plist   (shortcut-sign -a)
#
# These come from GitHub Actions secrets. They are the private half of your
# Apple identity, so this script goes to some length never to expose them:
#
#   * they are written only to mktemp files under a umask that denies group/other,
#   * those files are shredded on any exit,
#   * their contents are never echoed, and the secrets are masked in Actions logs.
#
# Requires: shortcut-sign on PATH, and build/unsigned already populated by
# scripts/build_and_sign.sh.

set -euo pipefail
shopt -s nullglob

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNSIGNED_DIR="$REPO_ROOT/build/unsigned"
SIGNED_OUT="$REPO_ROOT/signed"

: "${APPLE_SIGNING_KEY:?APPLE_SIGNING_KEY is not set}"
: "${APPLE_AUTH_DATA:?APPLE_AUTH_DATA is not set}"

command -v shortcut-sign >/dev/null 2>&1 || { echo "ERROR: shortcut-sign not on PATH" >&2; exit 1; }

unsigned=("$UNSIGNED_DIR"/*.shortcut)
if [[ ${#unsigned[@]} -eq 0 ]]; then
    echo "ERROR: no unsigned shortcuts in build/unsigned. Run build_and_sign.sh first." >&2
    exit 1
fi

# Deny group/other on everything created from here on, before the secrets touch
# disk. Any temp file inheriting this mode is readable only by us.
umask 077

KEYFILE="$(mktemp)"
AUTHFILE="$(mktemp)"

cleanup() {
    # shred if available; plain rm is the fallback.
    shred -u "$KEYFILE" "$AUTHFILE" 2>/dev/null || rm -f "$KEYFILE" "$AUTHFILE"
}
trap cleanup EXIT INT TERM

# Decode straight from the environment. No `echo`, no here-string that could be
# captured; the values never appear as command arguments.
printf '%s' "$APPLE_SIGNING_KEY" | base64 -d > "$KEYFILE"
printf '%s' "$APPLE_AUTH_DATA"   | base64 -d > "$AUTHFILE"

if [[ ! -s "$KEYFILE" || ! -s "$AUTHFILE" ]]; then
    echo "ERROR: a secret decoded to an empty file. Check the base64 in the GitHub secret." >&2
    exit 1
fi

rm -rf "$SIGNED_OUT"
mkdir -p "$SIGNED_OUT"

echo "==> Signing ${#unsigned[@]} shortcut(s) with shortcut-sign"
for input in "${unsigned[@]}"; do
    base="$(basename "$input")"
    output="$SIGNED_OUT/$base"

    if ! shortcut-sign sign -i "$input" -o "$output" -k "$KEYFILE" -a "$AUTHFILE"; then
        echo "ERROR: shortcut-sign failed on $base" >&2
        exit 1
    fi
    if [[ ! -s "$output" ]]; then
        echo "ERROR: shortcut-sign produced no output for $base" >&2
        exit 1
    fi
    echo "    signed $base"
done

echo ""
echo "Signed ${#unsigned[@]} shortcut(s) into signed/."
