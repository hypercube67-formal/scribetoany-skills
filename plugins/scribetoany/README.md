# scribetoany

Lets a coding agent (Claude Code, Codex, Gemini CLI, Cursor…) transcribe
audio and video files on your computer with
[ScribeToAny](https://scribetoany.com/?utm_source=github&utm_medium=readme&utm_campaign=scribetoany-cli):
text with timestamps, SRT or VTT subtitles, speaker labels.

It drives the `scribetoany` command-line tool:

```bash
npm i -g scribetoany
scribetoany auth login            # opens the browser once
scribetoany transcribe meeting.m4a --format srt
```

Then ask your agent:

> Transcribe `~/Desktop/interview.m4a` with speaker labels and save it as SRT.

> 把桌面上的 lecture.mp4 转成文字稿。

The file is uploaded to your ScribeToAny account and counts toward your plan
(the free plan includes 100 minutes a month). We never train AI on your files.
