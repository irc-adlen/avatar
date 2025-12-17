## Piper TTS — Quick setup and HTTP usage

This project uses Piper TTS with the HTTP server to synthesize speech locally.

Prerequisites

- Python 3.8+ and git

Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install required packages

```bash
pip install setuptools typeguard pyyaml
python3 -m pip install "piper-tts[http]"
```

Download voices

```bash
# male
python3 -m piper.download_voices fr_FR-tom-medium
# female
python3 -m piper.download_voices fr_FR-upmc-medium
```

Run the HTTP server

```bash
python3 -m piper.http_server -m fr_FR-tom-medium --data-dir ./voices
```

Notes on flags

- `-m <VOICE>`: sets the default voice used by the server (example: `fr_FR-tom-medium`).
- `--data-dir <DIR>`: directory that contains downloaded voice data (e.g. `./voices`).

JSON payload format

Send a POST with `Content-Type: application/json` to the server root (e.g. `http://localhost:5000`). Example fields:

- `text` (required): text to synthesize
- `voice` (optional): voice name to use for this request; if omitted the server uses `-m <VOICE>` default
- `speaker` (optional): speaker name for multi-speaker voices
- `speaker_id` (optional): speaker id for multi-speaker voices — overrides `speaker` when provided
- `length_scale` (optional): speaking speed (default: `1`)
- `noise_scale` (optional): speaking variability
- `noise_w_scale` (optional): phoneme width variability

There are sample payloads in the `TTS/examples` directory.

Example: send a payload from a file

Create `payload.json` containing:

```json
{ "text": "Le viaduc-métro de Charenton est un ouvrage d'art ferroviaire ..." }
```

Then run:

```bash
curl -X POST -H "Content-Type: application/json" --data @payload.json -o test.wav http://localhost:5000
```

Alternative: pass JSON inline (escape quotes) — useful for quick tests:

```bash
curl -X POST -H "Content-Type: application/json" -d "{\"text\":\"Bonjour monde\"}" -o test.wav http://localhost:5000
```

Debugging tips

- Add `-v` to `curl` to see the HTTP exchange.
- Use `--fail -sS` for curl to fail on HTTP errors and print useful messages.
- If the server doesn't respond, verify it is running and listening on the expected port.

Troubleshooting dependencies

- If pip reports dependency resolver warnings, ensure the venv is activated and reinstall the missing packages:

```bash
source .venv/bin/activate
pip install pyyaml setuptools typeguard
```

Files of interest

- `TTS/examples/` — example payloads you can reuse

---

Updated: 2025-12-04
