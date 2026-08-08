#!/usr/bin/env python3
"""Build the n8n "Audiobook Webhook" workflow JSON.

Creates the workflow the Read Clipboard (Audiobook) shortcut talks to:

    Webhook (POST /audiobook) -> Lemonfox TTS (2x) -> Respond to Webhook (audio)

Run this on the machine that has your n8n API key (see the n8n-workflow skill),
then POST the output to n8n. It writes n8n_audiobook_workflow.json next to
itself.

    python3 build_workflow.py

CREDENTIALS: the Lemonfox API key is NOT written into this file or the workflow.
The workflow reads it at run time from an n8n environment variable,
LEMONFOX_API_KEY, so nothing secret ever reaches this repo. Set it on the n8n
server (e.g. in the container's environment) before running the workflow.

Adjust VOICE / MODEL / SPEED / FORMAT below to match your existing audiobook
setup. SPEED = 2.0 is the "2x".
"""

import json
import os

VOICE = "sarah"          # any Lemonfox voice
MODEL = "tts-1"          # OpenAI-compatible model name Lemonfox accepts
SPEED = 2.0              # 0.5 - 4.0; 2.0 == "2x"
FORMAT = "mp3"           # mp3 / opus / aac / flac / wav / ogg / pcm
WEBHOOK_PATH = "audiobook"

# Lemonfox is OpenAI-compatible; the key is injected from n8n's environment.
LEMONFOX_URL = "https://api.lemonfox.ai/v1/audio/speech"

json_body = json.dumps(
    {
        "model": MODEL,
        "input": "={{ $json.body.text }}",
        "voice": VOICE,
        "response_format": FORMAT,
        "speed": SPEED,
    }
)

nodes = [
    {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [400, 300],
        "parameters": {
            "path": WEBHOOK_PATH,
            "httpMethod": "POST",
            "responseMode": "responseNode",
        },
    },
    {
        "id": "22222222-2222-4222-8222-222222222222",
        "name": "Lemonfox TTS",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": [660, 300],
        "parameters": {
            "url": LEMONFOX_URL,
            "method": "POST",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Authorization",
                        # Key comes from the n8n server environment, never the repo.
                        "value": "=Bearer {{ $env.LEMONFOX_API_KEY }}",
                    }
                ]
            },
            "sendBody": True,
            "contentType": "json",
            "jsonBody": json_body,
            # Return the response as binary so the audio survives intact.
            "options": {
                "response": {
                    "response": {
                        "responseFormat": "file",
                        "outputPropertyName": "data",
                    }
                }
            },
        },
    },
    {
        "id": "33333333-3333-4333-8333-333333333333",
        "name": "Respond to Webhook",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [920, 300],
        "parameters": {
            "respondWith": "binary",
            "options": {
                "responseHeaders": {
                    "entries": [
                        {"name": "Content-Type", "value": "audio/mpeg"}
                    ]
                }
            },
        },
    },
]

connections = {
    "Webhook": {"main": [[{"node": "Lemonfox TTS", "type": "main", "index": 0}]]},
    "Lemonfox TTS": {
        "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
    },
}

body = {
    "name": "Audiobook Webhook",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"},
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "n8n_audiobook_workflow.json")
with open(out, "w", encoding="utf-8") as handle:
    json.dump(body, handle)
print(f"Wrote {out} ({len(nodes)} nodes)")
