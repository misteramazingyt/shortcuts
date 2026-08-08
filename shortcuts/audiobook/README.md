# Read Clipboard (Audiobook)

Sends whatever text is on the clipboard to an n8n webhook, which runs the
Lemonfox text-to-speech / 2x pipeline and returns an audio file, then hands that
audio to VLC through the share sheet.

```
Get Clipboard → Text → POST to n8n webhook → Set Name → Open In (VLC)
```

The shortcut holds **no credentials**. The Lemonfox API key stays inside n8n; the
only thing baked in is the webhook URL, which is safe to publish. Lock it down
with a webhook auth header in n8n if you want to.

## Endpoint

The shortcut POSTs to:

```
https://n8n.shae.dpdns.org/webhook/audiobook
```

with a JSON body:

```json
{ "text": "<the clipboard text>" }
```

and expects the response body to be the **audio file itself** (e.g.
`Content-Type: audio/mpeg`). It renames that to `audiobook.mp3` and opens the
share sheet so you can send it to VLC.

## The n8n side

This shortcut is only the front end. The matching workflow needs, at minimum:

1. **Webhook** node — method `POST`, path `audiobook`, response mode
   *"Using Respond to Webhook node"*. Read the text with `{{ $json.body.text }}`.
2. Your existing **Lemonfox TTS + 2x** logic, fed that text.
3. **Respond to Webhook** node — respond with **binary**, the audio from the
   previous step, `Content-Type: audio/mpeg`.

A ready-to-run builder for this workflow is in
[`../../n8n/audiobook_webhook/`](../../n8n/audiobook_webhook/). It runs on your
own machine (it needs your n8n API key and never touches this repo).

## Changing the URL, field name, or filename

All three are constants at the top of [`build.py`](build.py) — `WEBHOOK_URL`,
`BODY_FIELD`, `AUDIO_NAME`. Edit and rebuild:

```sh
python3 shortcuts/audiobook/build.py
```
