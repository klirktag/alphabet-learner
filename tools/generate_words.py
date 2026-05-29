#!/usr/bin/env python3
"""
Generate per-source word audio + bundle an emoji image for every entry in
the toddler-Swedish word list. Idempotent: re-run any time to refresh assets.

For each word we:
  1. Look up a Twemoji codepoint, download (and cache) its SVG.
  2. Run Piper (one ONNX per voice) to synthesise the spoken word, encode to
     Opus-in-WebM.
  3. Run espeak (-v sv+f3) for the sv-espeak source.
  4. Use the espeak output as a placeholder under sv-recorded.

Run:
    python3 tools/generate_words.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIPER = Path.home() / ".local/piper/piper/piper"
PIPER_MODELS = {
    "sv-piper-nst":  Path.home() / ".local/piper/sv_SE-nst-medium.onnx",
    "sv-piper-alma": Path.home() / ".local/piper/sv_SE-alma-medium.onnx",
    "sv-piper-lisa": Path.home() / ".local/piper/sv_SE-lisa-medium.onnx",
}
ESPEAK_SOURCE = "sv-espeak"
RECORDED_SOURCE = "sv-recorded"  # mirrors espeak output as a placeholder

EMOJI_CACHE = Path("/tmp/alphabet-emoji-cache")
EMOJI_CACHE.mkdir(exist_ok=True)


# (letter_slug, word_folder_slug, display_label, text_to_speak, twemoji_codepoint)
#
# slugs follow our existing ASCII convention (å→aa, ä→ae, ö→oe) so the
# filesystem stays portable. display_label is the proper Swedish word the
# kid sees, text_to_speak is what we hand to Piper / espeak.
WORDS = [
    # A
    ("a", "apa", "Apa", "apa", "1f412"),
    ("a", "ananas", "Ananas", "ananas", "1f34d"),
    ("a", "anka", "Anka", "anka", "1f986"),
    ("a", "apelsin", "Apelsin", "apelsin", "1f34a"),
    # B
    ("b", "bok", "Bok", "bok", "1f4d6"),
    ("b", "banan", "Banan", "banan", "1f34c"),
    ("b", "bil", "Bil", "bil", "1f697"),
    ("b", "boll", "Boll", "boll", "26bd"),
    ("b", "blomma", "Blomma", "blomma", "1f338"),
    ("b", "bjoern", "Björn", "björn", "1f43b"),
    ("b", "baat", "Båt", "båt", "1f6e5"),
    ("b", "buss", "Buss", "buss", "1f68c"),
    # C
    ("c", "cykel", "Cykel", "cykel", "1f6b2"),
    ("c", "citron", "Citron", "citron", "1f34b"),
    # D
    ("d", "docka", "Docka", "docka", "1faa9"),
    ("d", "dator", "Dator", "dator", "1f4bb"),
    ("d", "drake", "Drake", "drake", "1f409"),
    # E
    ("e", "eld", "Eld", "eld", "1f525"),
    ("e", "elefant", "Elefant", "elefant", "1f418"),
    ("e", "ek", "Ek", "ek", "1f333"),
    # F
    ("f", "faagel", "Fågel", "fågel", "1f426"),
    ("f", "fisk", "Fisk", "fisk", "1f41f"),
    ("f", "flicka", "Flicka", "flicka", "1f467"),
    ("f", "flygplan", "Flygplan", "flygplan", "2708"),
    ("f", "fjaeril", "Fjäril", "fjäril", "1f98b"),
    # G
    ("g", "gris", "Gris", "gris", "1f437"),
    ("g", "glass", "Glass", "glass", "1f366"),
    ("g", "giraff", "Giraff", "giraff", "1f992"),
    ("g", "gitarr", "Gitarr", "gitarr", "1f3b8"),
    # H
    ("h", "hus", "Hus", "hus", "1f3e0"),
    ("h", "hund", "Hund", "hund", "1f415"),
    ("h", "hand", "Hand", "hand", "270b"),
    ("h", "haest", "Häst", "häst", "1f434"),
    ("h", "hatt", "Hatt", "hatt", "1f3a9"),
    # I
    ("i", "is", "Is", "is", "1f9ca"),
    ("i", "igelkott", "Igelkott", "igelkott", "1f994"),
    # J
    ("j", "jul", "Jul", "jul", "1f384"),
    ("j", "juice", "Juice", "juice", "1f9c3"),
    ("j", "jordgubbe", "Jordgubbe", "jordgubbe", "1f353"),
    # K
    ("k", "katt", "Katt", "katt", "1f431"),
    ("k", "kaka", "Kaka", "kaka", "1f36a"),
    ("k", "ko", "Ko", "ko", "1f404"),
    ("k", "kanin", "Kanin", "kanin", "1f430"),
    ("k", "klocka", "Klocka", "klocka", "1f553"),
    ("k", "krokodil", "Krokodil", "krokodil", "1f40a"),
    # L
    ("l", "lampa", "Lampa", "lampa", "1f4a1"),
    ("l", "lejon", "Lejon", "lejon", "1f981"),
    ("l", "loek", "Lök", "lök", "1f9c5"),
    # M
    ("m", "mamma", "Mamma", "mamma", "1f469"),
    ("m", "maane", "Måne", "måne", "1f319"),
    ("m", "mus", "Mus", "mus", "1f42d"),
    ("m", "melon", "Melon", "melon", "1f348"),
    ("m", "morot", "Morot", "morot", "1f955"),
    # N
    ("n", "napp", "Napp", "napp", "1f37c"),
    ("n", "nyckel", "Nyckel", "nyckel", "1f511"),
    ("n", "naesa", "Näsa", "näsa", "1f443"),
    # O
    ("o", "orm", "Orm", "orm", "1f40d"),
    ("o", "ost", "Ost", "ost", "1f9c0"),
    ("o", "oxe", "Oxe", "oxe", "1f402"),
    # P
    ("p", "pappa", "Pappa", "pappa", "1f468"),
    ("p", "paeron", "Päron", "päron", "1f350"),
    ("p", "pingvin", "Pingvin", "pingvin", "1f427"),
    ("p", "peng", "Peng", "peng", "1f4b0"),
    ("p", "pizza", "Pizza", "pizza", "1f355"),
    ("p", "panda", "Panda", "panda", "1f43c"),
    # R
    ("r", "ros", "Ros", "ros", "1f339"),
    ("r", "regn", "Regn", "regn", "1f327"),
    ("r", "ring", "Ring", "ring", "1f48d"),
    ("r", "raev", "Räv", "räv", "1f98a"),
    # S
    ("s", "sol", "Sol", "sol", "2600"),
    ("s", "sten", "Sten", "sten", "1faa8"),
    ("s", "saeng", "Säng", "säng", "1f6cf"),
    ("s", "sko", "Sko", "sko", "1f45f"),
    ("s", "snoe", "Snö", "snö", "2744"),
    ("s", "slott", "Slott", "slott", "1f3f0"),
    # T
    ("t", "tand", "Tand", "tand", "1f9b7"),
    ("t", "taag", "Tåg", "tåg", "1f682"),
    ("t", "tiger", "Tiger", "tiger", "1f42f"),
    ("t", "tomte", "Tomte", "tomte", "1f385"),
    ("t", "telefon", "Telefon", "telefon", "1f4de"),
    ("t", "traktor", "Traktor", "traktor", "1f69c"),
    # U
    ("u", "uggla", "Uggla", "uggla", "1f989"),
    ("u", "undulat", "Undulat", "undulat", "1f99c"),
    # V
    ("v", "vatten", "Vatten", "vatten", "1f4a7"),
    ("v", "varg", "Varg", "varg", "1f43a"),
    ("v", "vante", "Vante", "vante", "1f9e4"),
    ("v", "valp", "Valp", "valp", "1f436"),
    ("v", "vindruva", "Vindruva", "vindruva", "1f347"),
    # X — slim pickings; use the piano emoji as the closest "xylofon" visual.
    ("x", "xylofon", "Xylofon", "xylofon", "1f3b9"),
    # Y
    ("y", "yxa", "Yxa", "yxa", "1fa93"),
    ("y", "yoghurt", "Yoghurt", "yoghurt", "1f964"),
    # Z
    ("z", "zebra", "Zebra", "zebra", "1f993"),
    # Å
    ("aa", "aasna", "Åsna", "åsna", "1f434"),  # donkey emoji is too new (Emoji 15) — fallback to horse
    ("aa", "aar", "År", "år", "1f4c5"),
    # Ä
    ("ae", "aegg", "Ägg", "ägg", "1f95a"),
    ("ae", "aepple", "Äpple", "äpple", "1f34e"),
    ("ae", "aelg", "Älg", "älg", "1f98c"),  # moose emoji is too new — fallback to deer
    # Ö
    ("oe", "oega", "Öga", "öga", "1f441"),
    ("oe", "oern", "Örn", "örn", "1f985"),
    ("oe", "oeken", "Öken", "öken", "1f3dc"),
]

TWEMOJI_URL = (
    "https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/{}.svg"
)


def download_emoji(codepoint: str) -> Path | None:
    cache = EMOJI_CACHE / f"{codepoint}.svg"
    if cache.exists() and cache.stat().st_size > 200:
        return cache
    url = TWEMOJI_URL.format(codepoint)
    r = subprocess.run(
        ["curl", "-sSfL", "-o", str(cache), url], capture_output=True, text=True
    )
    if r.returncode != 0 or not cache.exists() or cache.stat().st_size < 200:
        if cache.exists():
            cache.unlink()
        return None
    return cache


def piper_say(model: Path, text: str, out_wav: Path) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(PIPER), "--model", str(model), "--output_file", str(out_wav)],
        input=text,
        text=True,
        check=True,
        capture_output=True,
    )


def espeak_say(text: str, out_wav: Path) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["espeak", "-v", "sv+f3", "-s", "130", "-p", "60",
         "-w", str(out_wav), text],
        check=True,
        capture_output=True,
    )


def encode_webm(in_wav: Path, out_webm: Path) -> None:
    out_webm.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(in_wav),
            "-c:a", "libopus", "-b:a", "32k", "-vbr", "on",
            "-application", "voip",
            str(out_webm),
        ],
        check=True,
    )


def main() -> int:
    missing_emojis: list[str] = []
    generated = 0
    skipped_existing = 0

    for letter, folder, label, say, cp in WORDS:
        svg = download_emoji(cp)
        if svg is None:
            print(f"  ! emoji {cp} for {folder!r}: download failed, skipping image",
                  file=sys.stderr)
            missing_emojis.append(f"{folder}({cp})")

        # Piper voices
        for source, model in PIPER_MODELS.items():
            word_dir = ROOT / "sound" / source / "words" / folder
            wav = word_dir / "originals" / "audio.wav"
            webm = word_dir / "audio.webm"
            img = word_dir / "image.svg"
            if not webm.exists():
                piper_say(model, say, wav)
                encode_webm(wav, webm)
                generated += 1
            else:
                skipped_existing += 1
            if svg and not img.exists():
                shutil.copy(svg, img)

        # espeak voice
        word_dir = ROOT / "sound" / ESPEAK_SOURCE / "words" / folder
        wav = word_dir / "originals" / "audio.wav"
        webm = word_dir / "audio.webm"
        img = word_dir / "image.svg"
        if not webm.exists():
            espeak_say(say, wav)
            encode_webm(wav, webm)
            generated += 1
        else:
            skipped_existing += 1
        if svg and not img.exists():
            shutil.copy(svg, img)

        # sv-recorded mirrors espeak so the user can replace one file at a time
        rec_dir = ROOT / "sound" / RECORDED_SOURCE / "words" / folder
        rec_wav = rec_dir / "originals" / "audio.wav"
        rec_webm = rec_dir / "audio.webm"
        rec_img = rec_dir / "image.svg"
        if not rec_webm.exists():
            rec_dir.mkdir(parents=True, exist_ok=True)
            (rec_dir / "originals").mkdir(exist_ok=True)
            shutil.copy(ROOT / "sound" / ESPEAK_SOURCE / "words" / folder / "originals" / "audio.wav", rec_wav)
            shutil.copy(ROOT / "sound" / ESPEAK_SOURCE / "words" / folder / "audio.webm", rec_webm)
        if svg and not rec_img.exists():
            shutil.copy(svg, rec_img)

        print(f"  ok  {letter} {folder}  ({label})")

    print(
        f"\nDone. generated_audio={generated}, skipped_existing={skipped_existing}, "
        f"missing_emoji_count={len(missing_emojis)}"
    )
    if missing_emojis:
        print("Missing emojis:", ", ".join(missing_emojis))

    # Emit a JS WORDS object that can be pasted into script.js.
    by_letter: dict[str, list[dict]] = {}
    for letter, folder, label, _say, _cp in WORDS:
        by_letter.setdefault(letter, []).append({"folder": folder, "label": label})
    js_obj = json.dumps(by_letter, indent=8, ensure_ascii=False)
    print("\n----- paste into script.js (WORDS.sv = ...) -----")
    print(js_obj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
