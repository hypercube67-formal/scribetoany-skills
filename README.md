# ScribeToAny Skills

Agent Skills for subtitles and transcripts, from the team behind
[ScribeToAny](https://scribetoany.com/?utm_source=github&utm_medium=readme&utm_campaign=scribetoany-skills).
They work in Claude Code, Claude.ai, Codex, Cursor, Gemini CLI, OpenCode and
any other agent that reads `SKILL.md` folders.

| Skill | What it does |
|---|---|
| [subtitle-qc](plugins/subtitle-qc/skills/subtitle-qc/SKILL.md) | Checks and fixes subtitle reading speed (CPS), line length, duration and gaps in SRT/VTT files. Timing first, words last. |

## subtitle-qc

A subtitle can be accurate and still fail: if it leaves the screen before the
viewer finishes reading, it was missed. Auto-captions and raw Whisper output
fail this constantly, because each cue is timed to the words, not to the
reading.

Ask your agent:

> Check `episode-12.srt` for reading speed and fix what you can.

> 帮我检查一下这个字幕是不是太快了，能修就修。

It runs a fixed order:

1. **Check** reading speed against Netflix-style limits: 17 CPS and 42
   characters a line for Latin scripts, 9 CPS and 16 characters for Chinese,
   Japanese and Korean (picked from the text automatically), 2 lines,
   0.83–7 s, 80 ms between cues. Overlaps and reversed times are reported.
2. **Fix the timing** without touching a word: extend cues into the silence
   after them, merge short neighbours (never across a speaker change), open
   gaps, re-break long lines. Always into a new file.
3. **Condense what's left**, only if you approve: the agent proposes shorter
   wording for the few cues still over the limit, never changing names,
   numbers or meaning, and never for verbatim or legal transcripts.

Example on cues timed exactly to the words:

```
                                  Before   After
  Cues                                 9       6
  Median CPS                        25.0    17.0
  Over 17 CPS                          8       3
  Shorter than 0.83 s                  5       1
  Lines over 42 chars                  3       0
  Chars to cut to pass                67      19
```

On a 447-word English voiceover, the same order took cues over 17 CPS from 68%
to 24% before a single word was cut. The method and sources are in
[Subtitle reading speed (CPS)](https://scribetoany.com/blog/subtitle-reading-speed-cps?utm_source=github&utm_medium=readme&utm_campaign=subtitle-qc).

## Install

**Claude Code (plugin marketplace)**

```
/plugin marketplace add hypercube67-formal/scribetoany-skills
/plugin install subtitle-qc@scribetoany-skills
```

**Claude Code, Codex, Cursor, Gemini CLI, OpenCode (copy the folder)**

```bash
git clone https://github.com/hypercube67-formal/scribetoany-skills.git
# Claude Code
cp -r scribetoany-skills/plugins/subtitle-qc/skills/subtitle-qc ~/.claude/skills/
# Agents that read ~/.agents/skills
cp -r scribetoany-skills/plugins/subtitle-qc/skills/subtitle-qc ~/.agents/skills/
```

**Claude.ai**: zip the `subtitle-qc` folder and upload it under
Settings → Capabilities → Skills.

**Without an agent**: the script is standard-library Python 3.8+.

```bash
python3 scripts/subtitle_qc.py check episode.srt
python3 scripts/subtitle_qc.py fix episode.srt -o episode.qc.srt --todo todo.json
python3 scripts/subtitle_qc.py check episode.srt --preset netflix-adult --json
```

## No subtitle file yet?

These skills work on files you already have. To get an SRT or VTT from audio
or video, any transcription tool works. ScribeToAny does it in about 98
languages, with a free 100 minutes every month, and translates subtitles into
134+ languages with the timings kept.

## Development

```bash
python3 -m unittest discover tests
claude plugin validate .
```

`tests/fixtures/` holds SRT quirks seen in the wild: BOM, CRLF, missing blank
lines or numbers, 2-digit milliseconds, `->` arrows, position coordinates,
HTML and ASS tags, Windows-1252 text, overlaps and reversed times.

## License

MIT
