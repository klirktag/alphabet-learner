"""
Bypass Piper's espeak G2P by looking each word up in the NST Swedish
Pronunciation Lexicon (CC0) and synthesising directly from the resulting IPA.

Usage:
    from tools.piper_nst import PiperNST
    p = PiperNST(model="…/sv_SE-nst-medium.onnx",
                 lexicon="…/swe030224NST.pron")
    p.synth("juice", "/tmp/out.wav")        # one shot
    ok = p.synth_or_fallback(...)            # see below

The lexicon ships 927k words; ~100% of our toddler vocab is in it. When a
word is missing we currently raise — caller can choose to fall back to the
espeak-driven Piper binary (which is what tools/generate_words.py does).
"""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Iterable

import numpy as np
import onnxruntime as ort
import json
import re


# NST-SAMPA → IPA conversion. The order matters: multi-char patterns must
# be substituted before their single-char prefixes. Symbols not listed here
# pass through unchanged (so plain Latin letters like b, d, f, … just map
# to themselves, which is also what Piper's phoneme alphabet expects).
#
# The NST phoneme set is documented in
# sve.trans-konv.tar.gz / "Transkripsjonskonvensjoner sve". Notable gotchas:
#   - `u0` is a digraph for short /ɵ/ (the Swedish "russ" / "gubbe" vowel).
#     Across all 927k entries in the lexicon, EVERY `0` is preceded by a `u`
#     — it never appears alone. If you read them as separate phonemes you
#     get an extra phantom /u/ before every /ɵ/ (which we did, until we
#     didn't — that's why "jordgubbe" sounded wrong).
#   - `x\` is the Swedish "sj-sound" /ɧ/ (front of "sjuka", or initial in
#     "giraff", "geni", etc.).
#   - `s\`  is alveolo-palatal /ɕ/ ("tj-sound").
#   - Backtick after a consonant = retroflex modifier.
NST_REPLACEMENTS: list[tuple[str, str]] = [
    # Compound stress markers (must come before single ")
    ('""', 'ˈ'),   # accent 2 — Piper doesn't distinguish, both → primary stress
    # Two-char vowel digraph (must come before any rule that touches 'u')
    ('u0', 'ɵ'),   # short Swedish u, as in "russ", "gubbe", "yoghurt"
    # Retroflex modifiers (consonant + ` backtick)
    ('t`', 'ʈ'),
    ('d`', 'ɖ'),
    ('n`', 'ɳ'),
    ('l`', 'ɭ'),
    ('s`', 'ʂ'),
    ('r`', 'ɽ'),
    # SAMPA digraphs with backslash
    ('s\\', 'ɕ'),  # alveolo-palatal "tj-sound"
    ('x\\', 'ɧ'),  # Swedish "sj-sound"
    # Single-char stress / length / boundary
    ('"', 'ˈ'),
    ('%', 'ˌ'),
    (':', 'ː'),
    ('$', ''),      # drop syllable boundary
    # Uppercase vowels (SAMPA "open / lax" variants)
    ('A', 'ɑ'),
    ('E', 'ɛ'),
    ('I', 'ɪ'),
    ('O', 'ɔ'),
    ('U', 'ʊ'),
    ('Y', 'ʏ'),
    # Uppercase consonants
    ('N', 'ŋ'),
    # Swedish-specific vowels
    ('2', 'ø'),     # front-rounded "ö"
    ('9', 'œ'),     # short open front-rounded (allophone of 2)
    ('}', 'ʉ'),     # Swedish long "u"
    ('@', 'ə'),     # schwa, in word-final unstressed syllables
    # IPA glyph for g
    ('g', 'ɡ'),
]


def nst_to_ipa(nst: str) -> str:
    """Convert one NST-SAMPA transcription to its IPA equivalent."""
    s = nst
    for pat, rep in NST_REPLACEMENTS:
        s = s.replace(pat, rep)
    return s


class NSTLexicon:
    """Load the NST Swedish pronunciation lexicon (~177 MB, ~927k entries)."""

    PRON_FIELD = 11  # 0-based index of the SAMPA pronunciation column

    def __init__(self, path: str | Path):
        self._prons: dict[str, str] = {}
        with open(path, encoding="latin-1") as f:
            for line in f:
                fields = line.split(";")
                if len(fields) <= self.PRON_FIELD:
                    continue
                word = fields[0]
                pron = fields[self.PRON_FIELD]
                if not word or not pron:
                    continue
                # Keep the first transcription per word (the lexicon lists
                # the same word multiple times for different POS / inflection
                # tags; pronunciation is usually identical).
                self._prons.setdefault(word, pron)

    def __contains__(self, word: str) -> bool:
        return word in self._prons or word.lower() in self._prons

    def get(self, word: str) -> str | None:
        return self._prons.get(word) or self._prons.get(word.lower())

    def __len__(self) -> int:
        return len(self._prons)


class PiperNST:
    """Direct ONNX inference for a Piper voice with NST-derived phonemes."""

    # Piper input contract: phoneme_ids = [PAD, BOS, PAD, ph1, PAD, ph2, ...,
    # PAD, EOS, PAD]. Symbols below are looked up in the model's
    # phoneme_id_map.
    PAD = "_"
    BOS = "^"
    EOS = "$"

    def __init__(self, model: str | Path, lexicon: str | Path | None = None):
        self.sess = ort.InferenceSession(
            str(model), providers=["CPUExecutionProvider"]
        )
        cfg_path = str(model) + ".json"
        with open(cfg_path) as f:
            self.cfg = json.load(f)
        self.phoneme_ids: dict[str, list[int]] = self.cfg["phoneme_id_map"]
        self.sample_rate: int = int(self.cfg["audio"]["sample_rate"])
        self.scales = np.array(
            [
                self.cfg["inference"]["noise_scale"],
                self.cfg["inference"]["length_scale"],
                self.cfg["inference"]["noise_w"],
            ],
            dtype=np.float32,
        )
        self.lexicon = NSTLexicon(lexicon) if lexicon else None

    # --- phoneme handling -------------------------------------------------

    def _lookup(self, sym: str) -> list[int] | None:
        return self.phoneme_ids.get(sym)

    def _phonemes_to_ids(self, phonemes: Iterable[str]) -> list[int]:
        ids: list[int] = []
        pad = self._lookup(self.PAD)
        bos = self._lookup(self.BOS)
        eos = self._lookup(self.EOS)
        assert pad is not None and bos is not None and eos is not None
        ids.extend(pad)
        ids.extend(bos)
        ids.extend(pad)
        for sym in phonemes:
            got = self._lookup(sym)
            if got is None:
                raise ValueError(f"phoneme {sym!r} not in phoneme_id_map")
            ids.extend(got)
            ids.extend(pad)
        ids.extend(eos)
        ids.extend(pad)
        return ids

    # --- public API ------------------------------------------------------

    def synth_from_ipa(self, ipa: str, out_wav: str | Path) -> None:
        """Synthesise from an IPA phoneme string directly."""
        phonemes = list(ipa)
        ids = self._phonemes_to_ids(phonemes)
        audio = self._run_model(ids)
        self._write_wav(audio, out_wav)

    def synth_from_word(self, word: str, out_wav: str | Path) -> bool:
        """Look the word up in NST, synth, write WAV. Returns False if OOV."""
        if not self.lexicon:
            raise RuntimeError("no lexicon attached")
        pron = self.lexicon.get(word)
        if pron is None:
            return False
        ipa = nst_to_ipa(pron)
        self.synth_from_ipa(ipa, out_wav)
        return True

    # --- inference -------------------------------------------------------

    def _run_model(self, phoneme_ids: list[int]) -> np.ndarray:
        ids = np.array([phoneme_ids], dtype=np.int64)
        lengths = np.array([ids.shape[1]], dtype=np.int64)
        out = self.sess.run(
            None,
            {"input": ids, "input_lengths": lengths, "scales": self.scales},
        )
        audio = out[0].squeeze()
        # Convert from float32 in [-1, 1] to int16 PCM for WAV.
        audio = np.clip(audio, -1.0, 1.0)
        return (audio * 32767.0).astype(np.int16)

    def _write_wav(self, audio: np.ndarray, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sample_rate)
            w.writeframes(audio.tobytes())


if __name__ == "__main__":
    # Smoke test: synthesise a few problem words and dump WAVs.
    import sys

    LEX = "/tmp/nst-sv/NST svensk leksikon/swe030224NST.pron/swe030224NST.pron"
    MODEL = "/home/ekirprivat/.local/piper/sv_SE-nst-medium.onnx"

    p = PiperNST(MODEL, LEX)
    print(f"loaded {len(p.lexicon)} lexicon entries", file=sys.stderr)

    samples = ["apa", "juice", "gitarr", "jul", "öga", "äpple", "tomte",
               "yoghurt", "morot", "elefant"]
    for w in samples:
        nst = p.lexicon.get(w)
        ipa = nst_to_ipa(nst) if nst else "(OOV)"
        print(f"  {w:13s}  NST={nst!s:25s}  IPA={ipa!r}", file=sys.stderr)
        ok = p.synth_from_word(w, f"/tmp/nst-{w}.wav")
        print(f"     -> {'wrote' if ok else 'SKIP'} /tmp/nst-{w}.wav", file=sys.stderr)
