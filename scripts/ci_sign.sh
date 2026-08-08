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

# The dumper saved the auth as an NSKeyedArchiver wrapper; shortcut-sign and iOS
# need a plain plist with the cert chain at the top level. Normalize it here so
# the certificate chain is reachable — otherwise every signature has "no cert
# chain" and iOS rejects the shortcut as invalid. Idempotent: an already-plain
# auth passes through unchanged.
NORM_AUTH="$(mktemp)"
cleanup_norm() { shred -u "$NORM_AUTH" 2>/dev/null || rm -f "$NORM_AUTH"; }
trap 'cleanup; cleanup_norm' EXIT INT TERM
python3 "$REPO_ROOT/scripts/normalize_auth.py" "$AUTHFILE" "$NORM_AUTH"

rm -rf "$SIGNED_OUT"
mkdir -p "$SIGNED_OUT"

echo "==> Signing ${#unsigned[@]} shortcut(s) with shortcut-sign"
for input in "${unsigned[@]}"; do
    base="$(basename "$input")"
    output="$SIGNED_OUT/$base"

    if ! shortcut-sign sign -i "$input" -o "$output" -k "$KEYFILE" -a "$NORM_AUTH"; then
        echo "ERROR: shortcut-sign failed on $base" >&2
        exit 1
    fi
    if [[ ! -s "$output" ]]; then
        echo "ERROR: shortcut-sign produced no output for $base" >&2
        exit 1
    fi

    # Prove the signature before publishing. This is the exact check that caught
    # the broken auth format: "missing cert chain" fails here instead of silently
    # shipping a file iOS calls invalid.
    if ! shortcut-sign verify -i "$output" >/dev/null 2>&1; then
        echo "ERROR: signature failed verification for $base" >&2
        shortcut-sign verify -i "$output" 2>&1 | sed 's/^/       /' >&2
        exit 1
    fi
    echo "    signed + verified $base"
done

echo ""
echo "Signed and verified ${#unsigned[@]} shortcut(s) into signed/."
