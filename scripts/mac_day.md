# The Mac day

You have a Mac for one day. Two things are worth getting from it, in this order.
Phase 1 is certain and quick. Phase 2 is the one that means you never need a Mac
again — attempt it only once Phase 1 is safely committed.

Phase 2 involves disabling SIP and AMFI, which is reversible but is a real change
to the machine. If the Mac is not yours, ask first.

---

## Phase 1 — sign what exists (30 minutes, no system changes)

Guaranteed to work. Gets installable shortcuts onto your phone today.

```sh
git clone https://github.com/misteramazingyt/shortcuts.git
cd shortcuts
./scripts/sign_on_mac.sh
```

Requires the Mac to be signed into iCloud (System Settings → Apple Account). The
script refuses to start otherwise, and says so plainly.

It signs every shortcut, commits them to `signed/`, and pushes. Install on the
phone from GitHub afterwards.

**Before starting, tell me to build every shortcut you want.** One session signs
an unlimited number, and Phase 1 only ever covers shortcuts that exist at the
moment you run it.

---

## Phase 2 — extract the signing identity (the prize)

Two files make Linux and CI able to sign forever:

| File | What it is |
| --- | --- |
| private key | ASN.1 private ECDSA-P256 key — `shortcut-sign -k` |
| auth data | Apple ID auth blob — `shortcut-sign -a` |

Source: [`appleid-key-dumper`](https://github.com/0xilis/appleid-key-dumper). It
targets jailbroken iOS, but its README states it can be compiled for an
AMFI-disabled Mac by changing the hardcoded output path in `main.m` and writing a
Makefile for it.

**I cannot verify any of this.** I have no Mac and no way to test it. Treat the
steps below as the documented route, not a tested one, and expect to improvise.

### Disabling SIP and AMFI

The dumper needs private keychain entitlements it is not normally allowed, which
is why AMFI has to be off.

1. Boot into Recovery — Apple silicon: hold the power button until "Loading
   startup options". Intel: hold ⌘R during boot.
2. Apple silicon only: Startup Security Utility → your disk → **Reduced
   Security**, and allow user management of kernel extensions.
3. Recovery → Utilities → Terminal:
   ```sh
   csrutil disable
   ```
4. Reboot, then from the normal desktop:
   ```sh
   sudo nvram boot-args="amfi_get_out_of_my_way=0x1"
   ```
5. Reboot again.

### Dumping

```sh
git clone https://github.com/0xilis/appleid-key-dumper.git
cd appleid-key-dumper
# Edit main.m: change the hardcoded /var/mobile/Documents path to something
# writable on macOS, e.g. $HOME/signing-identity
# Then compile — no Makefile ships for macOS:
clang -framework Foundation -framework Security main.m -o appleid-key-dumper
./appleid-key-dumper
```

### Put SIP back

```sh
sudo nvram -d boot-args
# then reboot to Recovery and:
csrutil enable
```
On Apple silicon also set Startup Security back to **Full Security**.

### Getting the files to me

Do **not** commit them. `.gitignore` already blocks the obvious names, but that
is a safety net, not a plan.

The private key is your Apple identity — anyone holding it can sign as you. Put
both files in GitHub Actions secrets, base64-encoded:

```sh
base64 -i private.key | pbcopy   # paste into a secret named APPLE_SIGNING_KEY
base64 -i auth_data  | pbcopy    # paste into a secret named APPLE_AUTH_DATA
```

Tell me when they exist and I will wire up CI signing with `shortcut-sign`. I
never need to see the values.

---

## If Phase 2 works

CI signs every future shortcut on Linux for free. You describe what you want, I
build it, it lands signed in the repo, you install from your phone. No Mac, no
Codemagic Mac minutes, no rental.

## If Phase 2 fails

Phase 1 still stands, and the fallback is a €2.60 Scaleway bare-metal day per
batch. Not free, but not blocking.

One more caveat I cannot resolve without a device: whether a `shortcut-sign`
signature is actually accepted by iOS 26. It signs with your own Apple ID, and
your phone has Private Sharing on, so it should be — but "should" is doing real
work in that sentence, and the first signed file you try will settle it.
