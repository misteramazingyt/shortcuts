#!/usr/bin/env bash
#
# Build every shortcut in this repository and sign it for distribution.
#
#   ./scripts/build_and_sign.sh
#
# Generation runs anywhere Python 3 does. Signing is macOS-only: `shortcuts` is
# an Apple CLI built into macOS 12 and later, so on Linux this script builds the
# unsigned files and then stops with an explicit error rather than pretending.
#
# Adding a shortcut needs no change here. Any shortcuts/<name>/build.py is
# discovered automatically and asked to write into build/unsigned.
#
# Nothing under shortcuts/ is modified. Generated output goes to build/, which
# is git-ignored; the signed files are collected by CI as artifacts.

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
# not survive in build/ and get signed and published anyway.
echo "==> Cleaning build directory"
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

# --- Sign -----------------------------------------------------------------
if ! command -v shortcuts >/dev/null 2>&1; then
    die "Apple's 'shortcuts' CLI was not found.
       Signing requires macOS 12 or later — the CLI ships with the OS and has no
       Linux or Windows equivalent. The unsigned files are in build/unsigned.
       On this machine, run generation only:  python3 shortcuts/<name>/build.py"
fi

echo ""
echo "==> Signing with: $(command -v shortcuts)"

for input in "${unsigned[@]}"; do
    base="$(basename "$input")"
    output="$SIGNED_DIR/$base"

    echo "    signing $base"
    if ! shortcuts sign --mode anyone --input "$input" --output "$output"; then
        die "shortcuts sign failed for: $base"
    fi

    # `shortcuts sign` has been reported to exit 0 while writing nothing, so the
    # exit code alone is not enough to call this a success.
    if [[ ! -s "$output" ]]; then
        die "shortcuts sign reported success but wrote no output for: $base
       This usually means the input is not a valid unsigned shortcut."
    fi
done

signed=("$SIGNED_DIR"/*.shortcut)
if [[ ${#signed[@]} -eq 0 ]]; then
    die "Signing loop completed but build/signed is empty."
fi

if [[ ${#signed[@]} -ne ${#unsigned[@]} ]]; then
    die "Signed ${#signed[@]} file(s) but generated ${#unsigned[@]}. Counts must match."
fi

# --- Summary --------------------------------------------------------------
echo ""
echo "Successfully generated and signed ${#signed[@]} shortcuts:"
echo ""
for file in "${signed[@]}"; do
    echo "  ${file#"$REPO_ROOT"/}"
done
echo ""
