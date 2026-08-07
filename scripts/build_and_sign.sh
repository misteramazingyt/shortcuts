#!/usr/bin/env bash
#
# Build every shortcut in this repository and sign it for distribution.
#
#   ./scripts/build_and_sign.sh
#
# Generation runs anywhere Python 3 does. Signing is macOS-only and additionally
# needs an Apple Account signed in on the machine, so it is best effort: when a
# signer is unavailable the unsigned files are still the deliverable.
#
# Adding a shortcut needs no change here. Any shortcuts/<name>/build.py is
# discovered automatically and asked to write into build/unsigned.
#
# Nothing under shortcuts/ is modified. Generated output goes to build/, which
# is git-ignored and collected by CI as artifacts.

set -euo pipefail
shopt -s nullglob

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build"
UNSIGNED_DIR="$BUILD_DIR/unsigned"
SIGNED_DIR="$BUILD_DIR/signed"

PYTHON="${PYTHON:-python3}"

die() {
    echo "" >&2
    echo "ERROR: $*" >&2
    exit 1
}

echo "==> Repository: $REPO_ROOT"

# --- Clean ----------------------------------------------------------------
# A full wipe keeps runs deterministic: a shortcut deleted from the repo must
# not survive in build/ and get published anyway.
echo "==> Cleaning build output"
rm -rf "$BUILD_DIR"
mkdir -p "$UNSIGNED_DIR" "$SIGNED_DIR"

# --- Generate -------------------------------------------------------------
command -v "$PYTHON" >/dev/null 2>&1 || die "'$PYTHON' not found; Python 3 is required to generate shortcuts."
echo "==> Using $("$PYTHON" --version 2>&1)"

# Globs rather than find: the shell sorts them, so build order is stable, and
# paths containing spaces survive without any -print0 plumbing.
generators=("$REPO_ROOT"/shortcuts/*/build.py)

if [[ ${#generators[@]} -eq 0 ]]; then
    die "No shortcut generators found. Expected at least one shortcuts/<name>/build.py."
fi

echo "==> Found ${#generators[@]} generator(s)"
for generator in "${generators[@]}"; do
    echo "    - ${generator#"$REPO_ROOT"/}"
done

for generator in "${generators[@]}"; do
    name="$(basename "$(dirname "$generator")")"
    echo ""
    echo "==> Generating: $name"
    "$PYTHON" "$generator" "$UNSIGNED_DIR" || die "Generator failed: ${generator#"$REPO_ROOT"/}"
done

unsigned=("$UNSIGNED_DIR"/*.shortcut)
if [[ ${#unsigned[@]} -eq 0 ]]; then
    die "Generators ran but produced no .shortcut files in build/unsigned."
fi

echo ""
echo "==> Generated ${#unsigned[@]} unsigned shortcut(s)"
for file in "${unsigned[@]}"; do
    echo "    - $(basename "$file") ($(wc -c <"$file" | tr -d ' ') bytes)"
done

# --- Sign (best effort) ---------------------------------------------------
# Signing is optional. It needs Apple's `shortcuts` CLI, which exists only on
# macOS, AND an Apple Account signed in on that machine. Neither is available
# in CI: macOS VMs cannot hold an iCloud session, which is why Codemagic's
# runner fails here regardless of what certificates are injected.
#
# So a missing signer is not an error. The unsigned files are the deliverable;
# they install on iOS with Settings > Shortcuts > Private Sharing turned on.
SIGNED_COUNT=0
SIGNING_NOTE=""

if ! command -v shortcuts >/dev/null 2>&1; then
    SIGNING_NOTE="skipped: Apple's 'shortcuts' CLI is macOS-only and is not on this machine"
else
    echo ""
    echo "==> Signing with: $(command -v shortcuts)"

    for input in "${unsigned[@]}"; do
        base="$(basename "$input")"
        output="$SIGNED_DIR/$base"

        set +e
        sign_output="$(shortcuts sign --mode anyone --input "$input" --output "$output" 2>&1)"
        sign_rc=$?
        set -e

        if [[ "$sign_rc" -ne 0 || ! -s "$output" ]]; then
            rm -f "$output"
            if printf '%s' "$sign_output" | grep -qi 'iCloud'; then
                SIGNING_NOTE="skipped: no Apple Account signed in on this machine"
            else
                SIGNING_NOTE="failed: $(printf '%s' "$sign_output" | head -1)"
            fi
            break
        fi

        echo "    signed $base"
        SIGNED_COUNT=$((SIGNED_COUNT + 1))
    done
fi

# --- Summary --------------------------------------------------------------
echo ""
echo "Generated ${#unsigned[@]} unsigned shortcut(s):"
echo ""
for file in "${unsigned[@]}"; do
    echo "  ${file#"$REPO_ROOT"/}"
done

echo ""
if [[ "$SIGNED_COUNT" -gt 0 ]]; then
    signed=("$SIGNED_DIR"/*.shortcut)
    echo "Signed ${#signed[@]} shortcut(s):"
    echo ""
    for file in "${signed[@]}"; do
        echo "  ${file#"$REPO_ROOT"/}"
    done
else
    echo "Signing $SIGNING_NOTE"
    echo ""
    echo "This is not a failure. Unsigned shortcuts install on iOS with"
    echo "Settings > Shortcuts > Private Sharing turned on."
fi
echo ""
