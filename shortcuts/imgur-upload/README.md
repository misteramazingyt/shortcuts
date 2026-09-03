# Upload to Imgur

Uploads an image to Imgur anonymously, then asks what you want out of it:

- **Copy Link** — the `https://i.imgur.com/…` URL goes to the clipboard.
- **Save QR Code** — a QR code of that URL is saved to Photos.

Share an image into it from Photos, Safari, Messages — anywhere with a share
sheet — or run it on its own and it opens the photo picker.

```
image in  →  HEIC? convert to JPEG  →  POST /3/upload  →  data.link  →  menu
```

## Setup — get a client ID first

Imgur's "anonymous" upload means *not attached to an account*. It still needs a
client ID, because the API identifies the app making the request.

1. Go to [api.imgur.com/oauth2/addclient](https://api.imgur.com/oauth2/addclient)
   (you need an Imgur account to register, but nothing you upload is tied to it).
2. Pick **Anonymous usage without user authorization** as the type. Any name and
   any URL will do — the callback URL is unused for this flow.
3. Imgur shows you a **Client ID**. Copy it.
4. Open the shortcut and paste it into the **Text** action at the very top,
   replacing `PASTE_YOUR_IMGUR_CLIENT_ID_HERE`. Paste the ID alone — the
   `Client-ID` prefix is added by the header, not by you.

Until you do, the shortcut stops on the first run and tells you so, rather than
failing with a bare `403` from Imgur.

A client ID is not a password — it goes out in the clear with every request any
Imgur web client makes — but it is yours and it carries your rate limit, so
don't publish the edited shortcut.

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

## The API it talks to

Imgur API v3, the current documented upload path:

```
POST https://api.imgur.com/3/upload
Authorization: Client-ID <your client ID>
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
- **Size.** Keep uploads under 10 MB; anonymous quotas are per client ID and per
  hour, and a large batch will hit them.

## Building it by hand

Every action in order, if you would rather assemble it in the Shortcuts app than
import a file. Steps 4 and 11 are guards — skip them and everything still works,
you just get worse errors.

1. **Text** — your client ID.
2. **Set Variable** `ClientID` to the Text output.
3. **If** `ClientID` *contains* `PASTE_YOUR` → **Show Alert** ("paste your client
   ID") → **Stop This Shortcut**. **End If**.
4. **If** `Shortcut Input` *has any value* → **Set Variable** `Image` to Shortcut
   Input. **Otherwise** → **Select Photos** (Select Multiple off) → **Set
   Variable** `Image`. **End If**.
5. **Get Details of Images** — *File Extension* of `Image`.
6. **If** that *contains* `hei` → **Convert Image** `Image` to **JPEG**, Preserve
   Metadata off → **Set Variable** `Upload`. **Otherwise** → **Set Variable**
   `Upload` to `Image`. **End If**.
7. **Get Contents of URL** — `https://api.imgur.com/3/upload`, Method **POST**.
   - Headers: `Authorization` = `Client-ID ` followed by the `ClientID` variable
     (one space between them, inside the same field).
   - Request Body: **Form**. Field `image`, type **File**, value the `Upload`
     variable. Field `type`, type Text, value `file`.
8. **Set Variable** `Response` to Contents of URL.
9. **Get Dictionary Value** — *Value* for `data` in `Response`.
10. **Get Dictionary Value** — *Value* for `link` in that. **Set Variable**
    `Link`.
11. **If** `Link` *does not have any value* → **Show Alert** with `Response` →
    **Stop This Shortcut**. **End If**.
12. **Choose from Menu** "Uploaded to Imgur":
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
