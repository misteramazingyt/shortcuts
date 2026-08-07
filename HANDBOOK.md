# The Mac Day Handbook

Every step from powering on the Mac to running a signed shortcut on your phone,
and how your Apple credentials stay safe.

There are two phases:

- **Phase 1 — Sign today.** Guaranteed. No system changes. Gets working, signed
  shortcuts onto your phone. Do this first, always.
- **Phase 2 — Free future signing.** Experimental. Extracts a signing identity so
  CI signs every future shortcut with no Mac. Requires temporarily disabling two
  macOS protections. Untested — budget time to debug.

> **Before you start, tell me which shortcuts you want.** Phase 1 only signs what
> exists in the repo when you run it. Give me the list and I'll build the whole
> batch so one Mac session signs all of them.

---

## What you need

- A Mac you can make system changes on (Phase 2). If it isn't yours, get
  permission before Part 2 — you'll be toggling SIP.
- Your iPhone, for the two-factor prompt and for installing the result.
- The Apple Account you want shortcuts signed under, signed in on both.
- About 30 minutes for Phase 1; another hour for Phase 2 if you attempt it.

At the end of Phase 1 you have a signed `.shortcut` installed and running on your
phone. At the end of Phase 2, GitHub signs everything you push, forever, for free.

---

# PHASE 1 — Sign today

### Step 1 — Power on and sign into iCloud

1. Turn on the Mac, log in.
2.  → System Settings → **Sign in** (top of the sidebar). Sign in with your
   Apple Account and approve the code on your iPhone.
3. Confirm it took: System Settings should show your name at the top.

### Step 2 — Install the command-line tools

Open **Terminal** (⌘-Space, type "Terminal", Enter) and run:

```sh
xcode-select --install
```

Click **Install** in the popup and wait for it to finish. This provides `git`,
`python3`, `clang`, and `codesign` — Phase 1 needs the first two, Phase 2 needs
all four. `shortcuts` itself is already built into macOS.

### Step 3 — Clone the repository

```sh
cd ~
git clone https://github.com/misteramazingyt/shortcuts.git
cd shortcuts
```

### Step 4 — Sign everything

```sh
./scripts/sign_on_mac.sh
```

This generates every shortcut, signs each with `shortcuts sign --mode anyone`,
copies the results into `signed/`, commits, and pushes. It refuses to start if
the Mac isn't signed into iCloud, and tells you so plainly.

Expected tail of the output:

```
==> Publishing 2 signed shortcut(s) to signed/
Done. Install on the iPhone from the signed/ directory:
  https://github.com/misteramazingyt/shortcuts/tree/main/signed
```

If it asks for GitHub credentials on push, use your GitHub username and a
[personal access token](https://github.com/settings/tokens) as the password.

### Step 5 — Install on your phone and run it

1. On the iPhone, open **Safari** (not the GitHub app — it can't download files).
2. Go to `https://github.com/misteramazingyt/shortcuts/tree/main/signed`.
3. Open a shortcut, tap the **⋯** menu → **Download raw file** (or **Download**).
4. Open it from Safari's downloads. Shortcuts offers to add it. Because it's
   signed, it imports instead of being rejected.
5. Run it.

**Phase 1 is done.** You have a signed, working shortcut. If you stop here, spin
the Mac up again next time you want new shortcuts signed — or do Phase 2 now and
never need it again.

---

# PHASE 2 — Free future signing (experimental)

Goal: extract two files — a private key and an auth blob — that let GitHub sign
shortcuts on Linux. After this, you push, GitHub signs, done. No Mac.

**Read this first.** Phase 2 temporarily disables System Integrity Protection
(SIP) and AMFI. Both are reversible and Step 10 puts them back. Both are real
security features; do not leave them off, and don't do this on a Mac that isn't
yours without permission. If any step fails, Phase 1's result still stands — you
lose nothing by trying.

### Step 6 — Disable SIP (from Recovery)

1. Shut down the Mac fully.
2. Enter Recovery:
   - **Apple silicon (M1/M2/M3/M4):** hold the **power button** until "Loading
     startup options" appears → click **Options** → **Continue**.
   - **Intel:** turn on and immediately hold **⌘R** until the Apple logo.
3. Menu bar → **Utilities → Terminal**. Run:
   ```sh
   csrutil disable
   ```
   Confirm with `y` and your password if asked.
4. **Apple silicon only:** Utilities → **Startup Security Utility** → select your
   disk → **Security Policy** → choose **Reduced Security** → tick **Allow user
   management of kernel extensions**.
5.  → **Restart**.

### Step 7 — Disable AMFI

Back on the normal desktop, in Terminal:

```sh
sudo nvram boot-args="amfi_get_out_of_my_way=0x1"
sudo reboot
```

AMFI is what normally stops a self-signed binary from claiming the entitlement
this needs. It has to be off for Step 8, and back on in Step 10.

### Step 8 — Build the dumper and extract the identity

```sh
cd ~/shortcuts/tools/appleid-key-dumper-macos
./build_and_dump.sh
```

On success it prints your account email and writes two files to `~/appleid-dump`:

```
SUCCESS. Two files written to /Users/you/appleid-dump:
  privateKey.bin
  authData.plist
```

If it says `copyPrivateKey returned NULL`, AMFI is still on or the binary wasn't
signed with the entitlement — recheck Step 7. If it can't read the account, the
Mac isn't signed into iCloud. The tool's
[README](tools/appleid-key-dumper-macos/README.md) has the full troubleshooting.

### Step 9 — Verify the files are real

```sh
ls -l ~/appleid-dump
```

Both files should be non-empty. `privateKey.bin` is a few hundred bytes;
`authData.plist` is larger. Do **not** open them in anything that might sync them
to a cloud service.

### Step 10 — Restore SIP and AMFI (do not skip)

```sh
sudo nvram -d boot-args          # re-enable AMFI
```

Then shut down, re-enter Recovery (Step 6), open Terminal, and:

```sh
csrutil enable
```

Apple silicon: in Startup Security Utility, set the policy back to **Full
Security**. Restart. Your Mac is now exactly as it was.

### Step 11 — Store the credentials securely in GitHub

This is the step your credentials' safety depends on. **The private key is your
Apple identity. Anyone who has it can sign as you. It must never touch the
repository.**

1. Base64-encode each file and copy it:
   ```sh
   base64 -i ~/appleid-dump/privateKey.bin | pbcopy
   ```
2. In a browser, go to
   **github.com/misteramazingyt/shortcuts → Settings → Secrets and variables →
   Actions → New repository secret**.
3. Name it `APPLE_SIGNING_KEY`, paste, **Add secret**.
4. Repeat for the auth data:
   ```sh
   base64 -i ~/appleid-dump/authData.plist | pbcopy
   ```
   Name it `APPLE_AUTH_DATA`.
5. Delete the local copies once the secrets are saved:
   ```sh
   rm -P ~/appleid-dump/privateKey.bin ~/appleid-dump/authData.plist
   ```

GitHub encrypts these at rest, never shows them again, and masks them in build
logs. See **Part 3** for exactly why this is safe on a public repo.

### Step 12 — Prove CI signing works

The moment both secrets exist, the next push signs automatically. Trigger one:

1. github.com/misteramazingyt/shortcuts → **Actions** → **Build & sign
   shortcuts** → **Run workflow** → branch `main`.
2. Watch it: it builds `shortcut-sign`, signs, and commits to `signed/`.
3. Install the newly signed file on your phone (Step 5) and confirm it imports.

If that import succeeds, you are done forever: tell me a shortcut, I build it,
GitHub signs it, you install it. **If the signed file is rejected by iOS**, tell
me the exact message — `shortcut-sign`'s output format for iOS 26 is the one
thing no one here has been able to verify, and that message is what lets me fix
it.

---

# PART 3 — Keeping your credentials secure

The rules, in priority order:

1. **The key never enters the repository.** Not in a commit, not in a branch, not
   in a build log. `.gitignore` already blocks `privateKey.bin`, `authData.plist`
   and `appleid-dump/` as a backstop, but the real defense is that they only ever
   live in GitHub Secrets and your local `~/appleid-dump`, which you delete in
   Step 11.

2. **GitHub Secrets are safe even though the repo is public.** They're encrypted
   at rest and revealed only to workflows running in *your* repository. Pull
   requests from forks — the way a stranger would try to run code here — are
   denied access to secrets by GitHub. Our workflow also never prints them:
   `ci_sign.sh` decodes them to temp files readable only by the build user and
   shreds those files on exit.

3. **Guard the workflow file.** The one way a secret could leak from a public repo
   is a malicious change to `.github/workflows/build.yml` that echoes it. You are
   the only one who can merge to `main`, so simply read any change to that file
   before merging it. Don't run workflows from PRs you haven't reviewed.

4. **If the key is ever exposed, revoke it.** It's tied to your Apple Account —
   signing out of iCloud on your devices and back in rotates the identity, which
   invalidates a leaked key. Then re-run Phase 2 to mint a fresh one.

5. **The signed shortcuts themselves are not secret.** Only the key and auth data
   are. Publishing signed `.shortcut` files is the whole point.

---

# PART 4 — Quick troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `sign_on_mac.sh`: "no Apple Account signed in" | Not signed into iCloud | Step 1 |
| `git clone` / push asks for a password | GitHub needs a token | Use a [PAT](https://github.com/settings/tokens) as the password |
| `copyPrivateKey returned NULL` | AMFI still on, or entitlement missing | Recheck Step 7, rerun Step 8 |
| dumper: "could not read AppleIDAccount" | Not signed into iCloud on the Mac | Step 1 |
| iOS: "unsigned shortcut not supported" | The file wasn't signed | It came from `shortcuts/`, not `signed/` — install from `signed/` |
| iOS rejects a `signed/` file after Phase 2 | `shortcut-sign` output may not suit iOS 26 | Send me the exact message |
| Actions run skips signing | Secrets not set | Step 11 |

Everything here is committed in the repo, so it's on the Mac the moment you
finish Step 3.
