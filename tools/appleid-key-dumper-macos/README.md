# appleid-key-dumper — macOS port

Extracts the two files [`shortcut-sign`](https://github.com/0xilis/shortcut-sign)
needs to sign shortcuts on Linux:

| File | `shortcut-sign` flag | What it is |
| --- | --- | --- |
| `privateKey.bin` | `-k` | a fresh ECDSA-P256 private key, endorsed by your Apple ID |
| `authData.plist` | `-a` | your certificate chain + validation record proving that endorsement |

Get these once, and CI signs every future shortcut for free. No Mac ever again.

This is a port of [0xilis/appleid-key-dumper](https://github.com/0xilis/appleid-key-dumper),
which targets jailbroken iOS. The four `Sharing/*.h` headers and
`entitlements.plist` are upstream, unmodified. `main.m` differs from upstream
only in writing to a configurable path instead of a hardcoded iOS one.

## It never exports your Apple ID key

Worth understanding, because it's why this can work at all. The Apple ID private
key is very likely non-exportable — Secure Enclave or keychain-bound. This tool
does not try to copy it. It generates a **new** keypair, uses the Apple ID key
to make a **single signature** over the new key, and exports the new key. Using
a key is permitted where exporting it is not, so the usual "you can't extract
Secure Enclave keys" wall does not apply.

## Why SIP and AMFI have to come off

Reaching the Apple ID key needs the `keychain-access-groups` entitlement for
`com.apple.sharing.appleidauthentication`. macOS only honors that entitlement on
Apple-signed binaries. Disabling AMFI lets a self-signed binary claim it;
disabling SIP is what lets you disable AMFI. Both are reversible, and the steps
to restore them are below. **If this Mac is not yours, get permission first.**

## Steps

### 1. Confirm iCloud

System Settings → Apple Account. Must be signed in, 2FA approved.

### 2. Disable SIP (from Recovery)

- Apple silicon: hold the power button → **Options** → Utilities → Terminal.
- Intel: hold ⌘R during boot → Utilities → Terminal.

```sh
csrutil disable
```

Apple silicon also needs, in **Startup Security Utility**, the disk set to
**Reduced Security**. Reboot back to the desktop.

### 3. Disable AMFI

```sh
sudo nvram boot-args="amfi_get_out_of_my_way=0x1"
sudo reboot
```

### 4. Build and dump

```sh
cd tools/appleid-key-dumper-macos
./build_and_dump.sh
```

Success prints the account email and writes both files to `~/appleid-dump`.

If `copyPrivateKey returned NULL`: the entitlement was not honored — AMFI is
still on, or the binary was not signed with `entitlements.plist`. If it cannot
read `AppleIDAccount`: the Mac is not signed into iCloud.

### 5. Restore SIP and AMFI

Do not skip this, especially on a machine that is not yours.

```sh
sudo nvram -d boot-args          # re-enable AMFI
```
Then reboot to Recovery and:
```sh
csrutil enable
```
Apple silicon: set Startup Security back to **Full Security**.

### 6. Hand the files off — without committing them

The private key is your Apple identity: anyone with it can sign as you.
`.gitignore` blocks the obvious names as a backstop, but the plan is to keep
them out of the repo entirely. Base64 into GitHub Actions secrets:

```sh
base64 -i ~/appleid-dump/privateKey.bin | pbcopy   # secret: APPLE_SIGNING_KEY
base64 -i ~/appleid-dump/authData.plist | pbcopy   # secret: APPLE_AUTH_DATA
```

Then tell me the secrets exist and I'll wire CI signing. I never see the values.

## This is untested

I built it from source without a Mac to run it on. The compile flags, the
private-framework link, and the entitlement claim are all reasoned from the
upstream project, not verified. Budget time on your Mac day to debug it, and do
the guaranteed signing pass (`scripts/sign_on_mac.sh`) first so the day is not
wasted if this fights back.
