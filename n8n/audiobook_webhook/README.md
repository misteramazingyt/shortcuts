# Audiobook Webhook (n8n)

The n8n side of the **Read Clipboard (Audiobook)** shortcut:

```
Webhook (POST /audiobook) → Lemonfox TTS (2x) → Respond to Webhook (audio)
```

The shortcut POSTs `{ "text": "…" }`; this workflow speaks it with Lemonfox at
2× and returns the audio, which the shortcut opens in VLC.

## Deploy it (on the machine with your n8n API key)

Per the `n8n-workflow` skill — this runs against `https://n8n.shae.dpdns.org`
and never touches this repo's secrets.

1. **Put the Lemonfox key in n8n's environment**, not in any file. Set
   `LEMONFOX_API_KEY` on the n8n server (the workflow reads
   `{{ $env.LEMONFOX_API_KEY }}` at run time). Restart n8n so it picks it up.

2. **Build the workflow JSON:**
   ```sh
   python3 build_workflow.py
   ```

3. **Create it in n8n:**
   ```powershell
   $apiKey = [System.Environment]::GetEnvironmentVariable('N8N', 'User')
   curl.exe -s -X POST `
     -H "X-N8N-API-KEY: $apiKey" `
     -H "Content-Type: application/json" `
     --data-binary "@n8n_audiobook_workflow.json" `
     "https://n8n.shae.dpdns.org/api/v1/workflows"
   ```

4. **Activate it** — in the n8n UI, or:
   ```powershell
   curl.exe -s -X PATCH -H "X-N8N-API-KEY: $apiKey" -H "Content-Type: application/json" `
     --data '{"active": true}' "https://n8n.shae.dpdns.org/api/v1/workflows/<ID>"
   ```

The production webhook is then `https://n8n.shae.dpdns.org/webhook/audiobook`,
which is exactly what the shortcut posts to.

## Notes

- `n8n_audiobook_workflow.json` is generated and git-ignored; only the builder is
  committed.
- Voice, model, speed, and format are constants at the top of `build_workflow.py`
  — set them to match your existing audiobook workflow. `SPEED = 2.0` is the 2×.
- This is a fresh, standalone workflow. If you'd rather bolt the webhook onto
  your existing audiobook workflow, add a **Webhook** trigger + **Respond to
  Webhook** node to it instead and keep your current Lemonfox nodes.
- If Lemonfox returns non-audio (e.g. an error JSON), VLC will refuse the file.
  Check the n8n execution log for the Lemonfox response in that case.
