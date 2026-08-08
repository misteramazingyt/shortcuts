# Handoff: deploy the Audiobook Webhook

For a Claude Code instance running on the Windows machine (which has the `N8N`
API key, the SSH key, and network access to n8n). A cloud session built the iOS
shortcut but can't reach the private n8n box; you finish the n8n side.

## Goal

Stand up the webhook that the **Read Clipboard (Audiobook)** shortcut calls, so
copying text + running the shortcut returns spoken audio into VLC.

Chain: `Webhook (POST /audiobook) → Lemonfox TTS @ 2× → Respond to Webhook (audio)`

The shortcut POSTs `{ "text": "…" }` to
`https://n8n.shae.dpdns.org/webhook/audiobook` and expects the response body to
be the audio file (`Content-Type: audio/mpeg`).

## Context already done (in this repo)

- iOS shortcut built, signed, live: `shortcuts/audiobook/` and the README table.
  It has **no credentials** — only the webhook URL. Don't put secrets in it.
- A standalone builder for the n8n workflow: `build_workflow.py` here. It works,
  but see the recommended path below — reusing the user's existing Lemonfox
  config is better than my guessed defaults.

## Infra facts (from the n8n-workflow / n8n-ssh skills)

| Thing | Value |
|---|---|
| n8n base URL | `https://n8n.shae.dpdns.org` |
| API key | `[System.Environment]::GetEnvironmentVariable('N8N','User')` |
| HTTP tool | `curl.exe` (not Invoke-RestMethod) |
| n8n server SSH | `ubuntu@64.181.226.55`, key `D:\Inbox\00 Now\202603251119 - n8n\n8n_ssh.key` |
| Writes | REST API only (`update_workflow` MCP is broken) |

## Recommended path — reuse the existing audiobook workflow

1. Find the user's existing audiobook workflow: `GET /api/v1/workflows`, locate
   the one with the Lemonfox TTS node.
2. Read its Lemonfox node: exact URL, auth (credential name or header), voice,
   model, response format, and how it does "2×" (likely `speed: 2`). That's the
   ground truth — copy it verbatim.
3. Build a new **Audiobook Webhook** workflow (or add a Webhook trigger +
   Respond-to-Webhook onto a copy of the existing one) that:
   - reads text via `{{ $json.body.text }}`,
   - feeds it to that exact Lemonfox node,
   - returns the audio binary with `Content-Type: audio/mpeg`.
4. POST it to create, then PATCH `{"active": true}`.

Use `build_workflow.py` as the skeleton; replace its Lemonfox node params with
the real ones from step 2 so voice/format/auth match what already works.

## Credentials

- Prefer the **existing** Lemonfox credential the user's current workflow already
  uses — no new key handling needed.
- If you must set the key fresh, put it in the n8n **server environment**
  (`LEMONFOX_API_KEY`, via SSH to the box) and reference `{{ $env.LEMONFOX_API_KEY }}`.
  Never write the key into the workflow JSON, this repo, or a commit.
- `n8n_audiobook_workflow.json` is git-ignored; keep it that way.

## Verify

```powershell
curl.exe -s -X POST -H "Content-Type: application/json" `
  --data '{"text":"This is a test."}' `
  "https://n8n.shae.dpdns.org/webhook/audiobook" --output test.mp3
```

`test.mp3` should be playable audio. Then run the shortcut on the phone with
something on the clipboard — it should open the audio in VLC.

## If you change the contract

The shortcut's URL, JSON field (`text`), and output filename are constants at the
top of `shortcuts/audiobook/build.py`. If the webhook path or field differs,
edit those, run `python3 shortcuts/audiobook/build.py`, and push — CI re-signs.
