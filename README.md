# צלילים פותחים — Words Starting with the Same Sound

A Hebrew reading exercise for Nevo. Every question shows a picture and **four words that
all begin with the same sound** (same first letter, or first two/three letters) — so the
only way to pick the right one is to read the word *to the end*. The difference is always
in the final letter: `סוס · סוד · סוג · סוף`.

## What's here

| File | What it is |
| --- | --- |
| `index.html` | The interactive app — open it in a browser, tap the right word. |
| `worksheet.html` | Print version: 6 × A4 pages, 4 questions each, plus an answer key page. |
| `worksheet.pdf` | The same worksheet already rendered — 7 pages, ready to print. |
| `words.js` | The 24 questions. **Single source of truth** for both the app and the worksheet. |
| `build-worksheet.py` | Regenerates `worksheet.html` (and optionally the PDF) from `words.js`. |

## Run it

Just open the file — there is no build step and no server needed:

```bash
open index.html
```

Speech (the app reads words aloud) needs a Hebrew system voice. On macOS: System Settings →
Accessibility → Spoken Content → System Voice → Manage Voices → **Carmit (Hebrew)**. Without
it everything still works, just silently. The 🔊 button toggles all sound.

## Playing

- Tap a word, or press **1–4**; **Enter** / **Space** moves on.
- Correct → the word turns green and is read aloud. Wrong → the app reads back *what you
  chose* and then the right word, so the ending difference is audible.
- The end screen lists exactly which words were missed, and remembers a personal best.
- Question order and answer positions are shuffled on every run.

## Editing the questions

Edit `words.js`, then rebuild the printable sheet:

```bash
python3 build-worksheet.py --pdf
```

The app picks up `words.js` on reload — no rebuild needed for it.

Each entry must satisfy the rules the build script asserts: exactly four distinct options,
the answer among them, and **every option starting with `onset`**. That last rule is the
whole point of the exercise, so the build fails loudly rather than shipping a question
where the shared beginning isn't actually shared.

```js
{ onset: "סו", pic: "🐴", options: ["סוד","סוס","סוג","סוף"], answer: "סוס" }
```

`pic` is an emoji, which is why there are no image files to manage.
