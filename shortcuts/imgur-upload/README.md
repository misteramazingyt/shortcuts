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

   [`Upload to Imgur v2.shortcut`](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/imgur-upload/Upload%20to%20Imgur%20v2.shortcut)
   — or the signed build from the table on the repo homepage, which needs no
   settings change.

2. Open it from Safari's downloads, or from Files, and Shortcuts offers to add
   it.
3. If iOS refuses the import, turn on **Settings → Shortcuts → Private Sharing**
   (called **Allow Untrusted Shortcuts** before iOS 26; it stays hidden until
   you have run at least one shortcut on the device). The
   [signed builds](../../signed) import without that toggle.

**To get it into the share sheet**, open the shortcut's settings (ⓘ) after
importing and switch on **Show in Share Sheet**. The file deliberately does not
ask for this itself — see [`build.py`](build.py); the flag that does was the
prime suspect in a crash on import, and letting the app set it is both safer and
exactly equivalent.

## Which build do you have?

The first build crashed the Shortcuts app on open. The fixed build is a
different file with a different name, so there is no way to mistake one for the
other:

| | First build | Fixed build |
| --- | --- | --- |
| File and link | `Upload to Imgur.shortcut` (deleted from this repo) | `Upload to Imgur v2.shortcut` |
| Name it imports under | *Upload to Imgur* | *Upload to Imgur v2* |
| Unsigned plist | 6518–7161 bytes | 7161 bytes, SHA-256 `fffe8614…835237` |
| Menu items in the plist | `<array><string>Copy Link</string>…` | `<array><dict>WFItemType 0 / WFValue "Copy Link"</dict>…` |

The signed downloads are all ~29 KB regardless — the signature adds about
22 KB to every shortcut here, so the size of a signed file says nothing about
which build it is. The name after import does.

If *Upload to Imgur v2* also crashes, that is new information, because every
structure in it now matches a file the Shortcuts app wrote itself. Say so.

## The first build crashed the Shortcuts app — what that was

The signed Control (Golden) opened and this one didn't, which put the fault in
the plist. Checked against a shortcut exported by the Shortcuts app itself and
against the output of the [Cherri](https://github.com/electrikmilk/cherri)
compiler for an equivalent program, the first build had these wrong:

- **Menu items were a bare array of strings.** The real format is an array of
  `{WFItemType: 0, WFValue: "…"}` entries, and each item's branch marker also
  carries `WFMenuItemAttributedTitle`. This is the one that crashes rather than
  errors — the app force-casts the array.
- **Generate QR Code** takes its text in `WFText`, not `WFInput`.
- Set Variable carries a `WFSerializationType`, Shortcut Input references carry a
  `VariableName`, block-closing markers carry a `UUID`, and a shortcut that
  reads Shortcut Input sets `WFWorkflowHasShortcutInputVariables`.

All of those are fixed in [`build.py`](build.py) and in the shared
[`tools/shortcut_builder.py`](../../tools/shortcut_builder.py). The If blocks,
the upload action, and the file-typed form field were already right.

[`Upload to Imgur (Minimal).shortcut`](https://raw.githubusercontent.com/misteramazingyt/shortcuts/main/shortcuts/imgur-upload/Upload%20to%20Imgur%20%28Minimal%29.shortcut)
is the same upload with no If, no menu and no variables — `Select Photos →
Convert to JPEG → POST → link → clipboard`. It exists from the bisect and it's a
perfectly usable uploader if you only ever want the link copied.

And whatever happens, **building it by hand always works** — see the action list
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
