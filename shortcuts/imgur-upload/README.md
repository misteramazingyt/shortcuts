# Upload to Imgur

Uploads an image to Imgur anonymously, then asks what you want out of it:

- **Copy Link** — the `https://i.imgur.com/…` URL goes to the clipboard.
- **Save QR Code** — a QR code of that URL is saved to Photos.

Share an image into it from Photos, Safari, Messages — anywhere with a share
sheet — or run it on its own and it opens the photo picker.

```
image in  →  HEIC? convert to JPEG  →  POST /3/upload  →  data.link  →  menu
```

## Setup

None. Install it and run it.

Every Imgur guide tells you to register an app first and paste in a client ID.
That is no longer possible and no longer necessary:

- **You can't get one.** `api.imgur.com/oauth2/addclient`, the registration page
  the API docs point at, now `301`s to the Imgur homepage.
- **You don't need one.** As of September 2026 `POST /3/upload` accepts an
  anonymous upload with no `Authorization` header at all. Verified against the
  live endpoint.

So the Text action at the top of the shortcut ships holding its placeholder, and
the shortcut treats that as "no client ID" and sends no header. **Leave it
alone** and everything works.

If you *do* have a client ID from before registration closed, replace the whole
placeholder with it — just the ID, the `Client-ID` prefix is added for you — and
every upload goes out under it instead. The shortcut picks the path by looking
at whether the placeholder is still there, so replace it, don't empty it.

Should Imgur start enforcing client IDs again, the shortcut will show you their
error verbatim rather than failing silently. There is currently no way to
register a new app; if that changes it will be under your Imgur account settings
while signed in.

## Install

1. Tap the download link **in Safari, not the GitHub mobile app** — the app
   can't download binary files and shows a blank preview instead.

   [`Upload to Imgur.shortcut`](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/imgur-upload/Upload%20to%20Imgur.shortcut)

2. Open it from Safari's downloads, or from Files, and Shortcuts offers to add
   it.
3. If iOS refuses the import, turn on **Settings → Shortcuts → Private Sharing**
   (called **Allow Untrusted Shortcuts** before iOS 26; it stays hidden until
   you have run at least one shortcut on the device). The
   [signed builds](../../signed) import without that toggle.

To get it into the share sheet, open the shortcut's settings (ⓘ) and check
**Show in Share Sheet** — the built file already asks for this, but confirm it
survived the import.

## If the Shortcuts app crashes when you open it

A crash is different from a rejection, and it narrows things down. Two things
can cause it, and one test tells them apart.

First, get the app back: don't tap the shortcut again. Force-quit Shortcuts,
then long-press its tile in the grid and **Delete** — deleting from the grid
never opens it.

Then work through these in order. Each is one download.

| # | Open this | If it crashes | If it opens |
| --- | --- | --- | --- |
| 1 | The **unsigned** [`Upload to Imgur.shortcut`](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/imgur-upload/Upload%20to%20Imgur.shortcut) (needs Private Sharing on) | The plist is at fault, not the signature → test 3 | The **signature** is at fault. The unsigned file is your working copy |
| 2 | The signed [`Control (Golden)`](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/signed/Control%20%28Golden%29.shortcut) | Signing is broken for *every* shortcut here, including ones that predate this one | Signing is fine; the fault is specific to this shortcut |
| 3 | [`Upload to Imgur (Minimal).shortcut`](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/imgur-upload/Upload%20to%20Imgur%20%28Minimal%29.shortcut) | The upload action itself, not the structure around it | The If blocks, the menu, or the share-sheet type |

Test 2 is what [`_control-golden`](../_control-golden/) exists for: a real Apple
shortcut pushed through the same signing pipeline. If it crashes, nothing about
this shortcut's contents is implicated — see
[HANDBOOK.md](../../HANDBOOK.md), which flags CI signing as never verified
against a device.

**Upload to Imgur (Minimal)** is the same upload with everything else stripped
out — no If, no menu, no named variables, no share-sheet type, just
`Select Photos → Convert to JPEG → POST → link → clipboard`. It is a diagnostic
rather than the deliverable (it converts every image to JPEG, and it always
copies rather than asking), but if it is the one that survives, it is also a
perfectly usable uploader. Delete both it and this section once the crash is
pinned down.

Whatever the outcome, **building it by hand always works** — see the action list
at the end of this file. Ten actions, no import, no signature.

## The API it talks to

Imgur API v3, the current documented upload path:

```
POST https://api.imgur.com/3/upload
Authorization: Client-ID <your client ID>    ← sent only if you pasted one in
Content-Type: multipart/form-data

image=<the image file>
type=file
```

The older `POST /3/image` is the same handler under a different name and still
works; `/3/upload` is what Imgur documents now.

The response is the standard v3 envelope, and the shortcut reads `data` → `link`
from it:

```json
{ "status": 200, "success": true,
  "data": { "link": "https://i.imgur.com/abc1234.png",
            "deletehash": "…", "width": 1, "height": 1 } }
```

If `link` is missing the shortcut shows the raw response instead of a generic
failure — that body is where Imgur explains a bad client ID, a rate limit, or an
oversized file.

`deletehash` is the only way to remove an anonymous upload later. This shortcut
throws it away; if you want it, add a **Get Dictionary Value** for `deletehash`
next to the one for `link` and append it to what gets copied.

## Things worth knowing

- **Imgur takes JPEG, PNG and GIF — not HEIC**, which is what an iPhone camera
  shoots by default. So the shortcut checks the file extension and converts to
  JPEG only in that case. PNG screenshots keep their transparency and GIFs keep
  their animation, which an unconditional convert would destroy.
- **Location data.** The HEIC conversion runs with *Preserve Metadata* off, so
  the GPS coordinates the camera embedded are dropped before the upload. An
  image that is already JPEG is uploaded untouched, EXIF and all. To strip that
  too, add a **Convert Image** action with metadata off in the Otherwise branch.
- **Anonymous is not private.** Anyone with the link can view it, Imgur can
  remove it, and you can't delete it from the website without the `deletehash`.
- **Size.** Keep uploads under 10 MB.
- **Rate limits.** Imgur meters anonymous uploads per hour — against your client
  ID if you sent one, otherwise against your IP address. Normal use won't come
  near it; uploading a whole album in a loop will.

## Building it by hand

Every action in order, if you would rather assemble it in the Shortcuts app than
import a file. Building it without a client ID is simpler: skip steps 1–2 and
build only the no-header half of step 6.

1. **Text** — `PASTE_YOUR_IMGUR_CLIENT_ID_HERE`, or your client ID if you have
   one.
2. **Set Variable** `ClientID` to the Text output.
3. **If** `Shortcut Input` *has any value* → **Set Variable** `Image` to Shortcut
   Input. **Otherwise** → **Select Photos** (Select Multiple off) → **Set
   Variable** `Image`. **End If**.
4. **Get Details of Images** — *File Extension* of `Image`.
5. **If** that *contains* `hei` → **Convert Image** `Image` to **JPEG**, Preserve
   Metadata off → **Set Variable** `Upload`. **Otherwise** → **Set Variable**
   `Upload` to `Image`. **End If**.
6. **If** `ClientID` *contains* `PASTE_YOUR` → upload **without** a header.
   **Otherwise** → the same upload **with** one. **End If**. Both are a **Get
   Contents of URL** — `https://api.imgur.com/3/upload`, Method **POST** —
   followed by **Set Variable** `Response`.
   - Request Body (both): **Form**. Field `image`, type **File**, value the
     `Upload` variable. Field `type`, type Text, value `file`.
   - Headers (Otherwise branch only): `Authorization` = `Client-ID ` followed by
     the `ClientID` variable, one space between them, inside the same field.
7. **Get Dictionary Value** — *Value* for `data` in `Response`.
8. **Get Dictionary Value** — *Value* for `link` in that. **Set Variable**
   `Link`.
9. **If** `Link` *does not have any value* → **Show Alert** with `Response` →
   **Stop This Shortcut**. **End If**. (A guard — skip it and a failed upload
   just gives you a worse error.)
10. **Choose from Menu** "Uploaded to Imgur":
    - **Copy Link** → **Copy to Clipboard** `Link` → **Show Notification**.
    - **Save QR Code** → **Generate QR Code** from `Link` → **Save to Photo
      Album** → **Show Notification**.

Wanting both at once is a one-line change: add a third menu item and put both
branches' actions under it.

## Rebuilding the file

```sh
python3 shortcuts/imgur-upload/build.py
```

The endpoint, the JPEG quality and the two menu titles are constants at the top
of [`build.py`](build.py). The build is deterministic — unchanged source
produces a byte-identical `.shortcut`.
