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
DIAG_DIR="$BUILD_DIR/diagnostics"

PYTHON="${PYTHON:-python3}"

die() {
    echo "" >&2
    echo "ERROR: $*" >&2
    exit 1
}

echo "==> Repository: $REPO_ROOT"

# --- Clean ----------------------------------------------------------------
# Wiping these two keeps runs deterministic: a shortcut deleted from the repo
# must not survive in build/ and get signed and published anyway.
#
# build/diagnostics is deliberately NOT removed — the diagnostics step runs
# before this script, and its report has to survive to be published.
echo "==> Cleaning build output"
rm -rf "$UNSIGNED_DIR" "$SIGNED_DIR"
mkdir -p "$UNSIGNED_DIR" "$SIGNED_DIR" "$DIAG_DIR"

# Truncated, not appended: a stale verdict from a previous local run in the
# same checkout would otherwise sit in the artifact next to the current one.
: >"$DIAG_DIR/signing-result.txt"

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

# Is an Apple signing identity actually on this machine? An entry from
# find-identity means the certificate AND its private key are both present, so
# this is the direct test of whether Codemagic's ios_signing injection landed.
# Recorded before signing so the failure report can distinguish CASE A from B.
APPLE_IDENTITY_PRESENT="NO"
APPLE_IDENTITY_COUNT=0
if command -v security >/dev/null 2>&1; then
    identity_list="$(security find-identity -v -p codesigning 2>/dev/null || true)"
    APPLE_IDENTITY_COUNT="$(printf '%s\n' "$identity_list" | grep -cE '^\s+[0-9]+\)' || true)"
    [[ "${APPLE_IDENTITY_COUNT:-0}" -gt 0 ]] && APPLE_IDENTITY_PRESENT="YES"
fi

echo ""
echo "==> Signing with: $(command -v shortcuts)"
echo "==> Apple code signing identities present: $APPLE_IDENTITY_PRESENT ($APPLE_IDENTITY_COUNT found)"

# Classify a signing failure from what the CLI actually said, then stop. The
# distinction decides whether CI signing is salvageable at all, so it is worth
# more than a generic non-zero exit.
report_signing_failure() {
    local base="$1" rc="$2" output_text="$3" mode

    if printf '%s' "$output_text" | grep -qi 'signed into iCloud\|sign in to iCloud\|iCloud account'; then
        mode="iCloud_session_required"
    elif [[ "$rc" -eq 0 ]]; then
        mode="silent_no_output"
    else
        mode="unknown"
    fi

    {
        echo ""
        echo "SHORTCUT_SIGNING_FAILURE=$mode"
        echo "Failed file: $base"
        echo "shortcuts sign exit code: $rc"
        echo "Apple developer certificate was present: $APPLE_IDENTITY_PRESENT"
        echo ""
        echo "--- CLI output ---"
        printf '%s\n' "$output_text"
        echo "------------------"
        echo ""

        case "$mode" in
        iCloud_session_required)
            if [[ "$APPLE_IDENTITY_PRESENT" == "YES" ]]; then
                echo "CASE B: An Apple signing identity IS installed on this runner, and"
                echo "'shortcuts sign' rejected it anyway, demanding an Apple Account"
                echo "session. Shortcut signing does not consume code signing"
                echo "certificates; the two systems are not bridgeable here."
            else
                echo "CASE A: No Apple signing identity reached this runner AND the CLI"
                echo "requires an iCloud session. Fix the certificate injection first,"
                echo "then re-run to find out whether the certificate changes anything."
            fi
            echo ""
            echo "An iCloud session cannot be established non-interactively: sign-in is"
            echo "two-factor gated, the CLI exposes no login command, and this runner is"
            echo "destroyed after the build. See the 'Shortcuts CLI capabilities' section"
            echo "of build/diagnostics/signing-environment.txt for what the CLI does"
            echo "support."
            ;;
        silent_no_output)
            echo "The CLI exited 0 but wrote nothing. That usually means the input is"
            echo "not a valid unsigned shortcut, which would be a bug in the generator"
            echo "rather than a credentials problem."
            ;;
        *)
            echo "Unrecognised failure. The CLI output above is the primary evidence."
            ;;
        esac
    } | tee -a "$DIAG_DIR/signing-result.txt"

    exit 1
}

for input in "${unsigned[@]}"; do
    base="$(basename "$input")"
    output="$SIGNED_DIR/$base"

    echo "    signing $base"

    set +e
    sign_output="$(shortcuts sign --mode anyone --input "$input" --output "$output" 2>&1)"
    sign_rc=$?
    set -e

    [[ -n "$sign_output" ]] && printf '%s\n' "$sign_output"

    if [[ "$sign_rc" -ne 0 ]]; then
        report_signing_failure "$base" "$sign_rc" "$sign_output"
    fi

    # The CLI has been reported to exit 0 while writing nothing, so the exit
    # code alone is not enough to call this a success.
    if [[ ! -s "$output" ]]; then
        report_signing_failure "$base" "$sign_rc" "$sign_output"
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
