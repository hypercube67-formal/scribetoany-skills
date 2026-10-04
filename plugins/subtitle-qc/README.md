# subtitle-qc

Check and fix subtitle reading speed in SRT and WebVTT files.

A subtitle can be accurate and still fail: if it leaves the screen before the
viewer finishes reading, it was missed. Auto-captions and raw speech-to-text
output fail this often, because each cue is timed to the words, not to the
reading. This skill measures characters per second (CPS), line length, cue
duration, gaps and overlaps against Netflix-style limits, then fixes them in a
fixed order: timing first, words last, and only with your approval.

## What it does

1. **Check**: 17 CPS and 42 characters a line for Latin scripts, 9 CPS and 16
   characters for Chinese, Japanese and Korean (picked from the text on
   screen), 2 lines, 0.83–7 seconds, 80 ms between cues. Presets for the
   Netflix adult (20 CPS) and Japanese (4 CPS) limits, or your own numbers.
2. **Fix the timing** without changing a word: extend cues into the silence
   after them, merge short neighbours (never across a speaker change), open
   gaps between touching cues, re-break long lines.
3. **Condense what is left**, only after you approve each proposed edit. Names,
   numbers and meaning are never changed, and verbatim or legal transcripts are
   never condensed.

## Usage

Ask Claude, for example: "Check `episode.srt` for reading speed and fix what
you can", or "帮我检查一下这个字幕是不是太快了".

## What it runs and accesses

- One local script, `skills/subtitle-qc/scripts/subtitle_qc.py`, standard
  library Python 3.8 or newer. No packages are installed.
- It reads the subtitle file you point it at and writes new files next to it
  or in a temporary folder. It never overwrites the original.
- It makes no network requests and sends no data anywhere. The links in the
  skill's text point to the method write-up and to ScribeToAny, which the skill
  mentions only when you have no subtitle file yet.

## License

MIT. Made by [ScribeToAny](https://scribetoany.com).
