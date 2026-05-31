# sv-recorded — your own Swedish letter recordings

This folder is **bootstrapped with the `sv-espeak` audio as placeholders** so
the "Inspelat" option in the in-app *Switch audio* picker has something to play
out of the box. Replace each file with your own voice — record letter by
letter, no need to do them all at once.

## How to record one letter

1. Record yourself saying the letter (phone voice memo, OBS, Audacity, `arecord`
   — anything that makes a WAV or audio file). Keep it short, ~0.5–1 s.

2. Drop the recording into `sound/sv-recorded/originals/` using the slug name
   below as the filename, e.g. `originals/k.wav` for **K**, `originals/aa.wav`
   for **Å**.

   | Letter | Slug | File                       |
   | ------ | ---- | -------------------------- |
   | A–Z    | a–z  | `originals/<lowercase>.wav` |
   | Å      | aa   | `originals/aa.wav`         |
   | Ä      | ae   | `originals/ae.wav`         |
   | Ö      | oe   | `originals/oe.wav`         |

3. Re-encode it to `sound/sv-recorded/<slug>.webm` (Opus, mono, 32 kbit/s):

   ```bash
   ffmpeg -y -i sound/sv-recorded/originals/<slug>.wav \
       -c:a libopus -b:a 32k -vbr on -application voip \
       sound/sv-recorded/<slug>.webm
   ```

   The `.webm` is the file the app actually plays. The `.wav` original is kept
   so the WebM can be re-encoded later with different codec settings.

4. Rebuild the APK (`./android/build.sh run`) and the new recording will be
   bundled into the next install — no other change needed.

You can replace files one at a time; the remaining placeholders will keep
sounding like espeak until you record over them.
