#!/usr/bin/env python3
"""Generate an ElevenLabs audio pack (letters + Visa-ord words) for the app.

This is the ElevenLabs sibling of tools/generate_words.py. Where that script
drives local engines (Piper / espeak), this one calls the ElevenLabs cloud TTS
API. It writes a complete audio pack under audio-packs/sv-<pack>/ so the app's
Settings popup can switch to it like any other pack.

Built to be re-run with a different voice in one line — that's the whole point
of it being a script:

    # default female voice into audio-packs/sv-elevenlabs/
    ELEVENLABS_API_KEY=sk_... python3 tools/generate_elevenlabs.py

    # try another voice into its own pack so you can A/B them in the app
    ELEVENLABS_API_KEY=sk_... python3 tools/generate_elevenlabs.py \
        --voice 21m00Tcm4TlvDq8ikWAM --pack elevenlabs-rachel

    # see which voices your account has (copy a voice_id from the list)
    ELEVENLABS_API_KEY=sk_... python3 tools/generate_elevenlabs.py --list-voices

For each LETTER it POSTs the Swedish letter name, saves the MP3 under
originals/, and encodes it to Opus-in-WebM at audio-packs/sv-<pack>/<slug>.webm.
For each WORD (reused verbatim from generate_words.py so the two packs stay in
sync) it does the same into words/<folder>/audio.webm and copies the shared
image.svg over from an existing pack.

Idempotent: existing .webm files are skipped. Pass --force to regenerate.

ElevenLabs bills per character; a full pack is ~700 characters (~30 for the
letters + ~650 for the 100 words), a trivial slice of the free monthly quota.

Required:  ELEVENLABS_API_KEY   (Settings -> API Keys on elevenlabs.io)
Optional:  ELEVENLABS_VOICE_ID  default voice (overridden by --voice)
           ELEVENLABS_MODEL     default model (overridden by --model)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Reuse the canonical word list so the ElevenLabs pack matches the others
# exactly (same folders, same Swedish text). generate_words.py guards its work
# behind `if __name__ == "__main__"`, so importing it is side-effect free
# beyond creating the emoji cache dir.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_words import WORDS, ROOT  # noqa: E402

AUDIO_PACKS = ROOT / "audio-packs"

# Default voice: "Sarah" — a female multilingual ElevenLabs voice, chosen to
# sit alongside the existing female espeak/Piper voices. Swap it per-run with
# --voice (or ELEVENLABS_VOICE_ID) to audition any other voice.
DEFAULT_VOICE = "EXAVITQu4vr4xnSDxMaL"
# eleven_multilingual_v2 is ElevenLabs' top-quality stable model and handles
# Swedish well. flash/turbo models also accept a `language_code` if you ever
# need to force a language for tricky single-letter pronunciation.
DEFAULT_MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"  # available on the free tier

# (slug, text-to-speak). The text is the Swedish *name* of the letter, not the
# bare glyph: handing a real Swedish syllable to the multilingual model yields
# Swedish pronunciation where a lone "A" would otherwise be read in English.
# Slugs follow the app's ASCII convention (å->aa, ä->ae, ö->oe).
LETTERS = [
    ("a", "a"), ("b", "be"), ("c", "se"), ("d", "de"), ("e", "e"),
    ("f", "eff"), ("g", "ge"), ("h", "hå"), ("i", "i"), ("j", "ji"),
    ("k", "kå"), ("l", "ell"), ("m", "emm"), ("n", "enn"), ("o", "o"),
    ("p", "pe"), ("q", "ku"), ("r", "err"), ("s", "ess"), ("t", "te"),
    ("u", "u"), ("v", "ve"), ("w", "dubbel-ve"), ("x", "eks"), ("y", "y"),
    ("z", "säta"), ("aa", "å"), ("ae", "ä"), ("oe", "ö"),
]


def api(url, api_key, data=None, method="GET"):
    """Make an ElevenLabs API request; returns the open response object."""
    headers = {"xi-api-key": api_key}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    return urllib.request.urlopen(req)


def list_voices(api_key):
    """Print every voice on this account: id, name, gender/accent labels."""
    with api("https://api.elevenlabs.io/v1/voices", api_key) as r:
        data = json.load(r)
    for v in data.get("voices", []):
        labels = v.get("labels", {})
        meta = "/".join(x for x in (labels.get("gender"), labels.get("accent")) if x)
        print(f"  {v['voice_id']}  {v['name']:<18} {meta}")


def synth(text, mp3_path, api_key, voice, model):
    """Synthesize <text> with the given voice/model; write MP3 to mp3_path."""
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
           f"?output_format={OUTPUT_FORMAT}")
    payload = {"text": text, "model_id": model}
    try:
        with api(url, api_key, payload, method="POST") as r:
            audio = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"ERROR {e.code} synthesizing {text!r}: {detail}\n"
                 "Tip: --list-voices to see valid voice ids, or check key/quota.")
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    mp3_path.write_bytes(audio)


def encode_opus(src_path, webm_path):
    """Encode any audio file to Opus-in-WebM (matches every other pack)."""
    webm_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src_path),
        "-c:a", "libopus", "-b:a", "32k", "-vbr", "on", "-application", "voip",
        str(webm_path),
    ], check=True)


def find_shared_image(folder):
    """Find an existing pack's image.svg for a word folder (it's identical
    across packs). Returns a Path or None."""
    for pack_dir in sorted(AUDIO_PACKS.glob("sv-*")):
        img = pack_dir / "words" / folder / "image.svg"
        if img.exists():
            return img
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE),
                        help="ElevenLabs voice_id (default: a female multilingual voice)")
    parser.add_argument("--model", default=os.environ.get("ELEVENLABS_MODEL", DEFAULT_MODEL),
                        help=f"model_id (default: {DEFAULT_MODEL})")
    parser.add_argument("--pack", default="elevenlabs",
                        help="pack id -> audio-packs/sv-<pack>/ (default: elevenlabs)")
    parser.add_argument("--letters-only", action="store_true", help="skip the words")
    parser.add_argument("--words-only", action="store_true", help="skip the letters")
    parser.add_argument("--force", action="store_true",
                        help="regenerate even if the .webm already exists")
    parser.add_argument("--list-voices", action="store_true",
                        help="list the account's voices and exit")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ERROR: set ELEVENLABS_API_KEY in the environment first.")

    if args.list_voices:
        list_voices(api_key)
        return

    pack = AUDIO_PACKS / f"sv-{args.pack}"
    print(f"Pack {pack.relative_to(ROOT)}  voice={args.voice}  model={args.model}")
    made = skipped = 0

    if not args.words_only:
        for slug, text in LETTERS:
            webm = pack / f"{slug}.webm"
            if webm.exists() and not args.force:
                skipped += 1
                continue
            mp3 = pack / "originals" / f"{slug}.mp3"
            synth(text, mp3, api_key, args.voice, args.model)
            encode_opus(mp3, webm)
            made += 1
            print(f"  letter {slug} ({text})")

    if not args.letters_only:
        # WORDS rows are (letter, folder, label, say, codepoint).
        for _letter, folder, label, say, _cp in WORDS:
            wdir = pack / "words" / folder
            webm = wdir / "audio.webm"
            if not (webm.exists() and not args.force):
                mp3 = wdir / "originals" / "audio.mp3"
                synth(say, mp3, api_key, args.voice, args.model)
                encode_opus(mp3, webm)
                made += 1
                print(f"  word   {folder} ({label})")
            else:
                skipped += 1
            # Copy the shared image if this pack doesn't have it yet.
            img = wdir / "image.svg"
            if not img.exists():
                shared = find_shared_image(folder)
                if shared:
                    img.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(shared, img)

    print(f"Done — {made} generated, {skipped} already present.")
    print(f'If new, ensure SOURCES.sv in script.js has: '
          f'{{ id: "{args.pack}", label: "ElevenLabs" }}')


if __name__ == "__main__":
    main()
