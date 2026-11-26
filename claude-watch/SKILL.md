---
name: claude-watch
description: Lets Claude properly "watch" a video - a TikTok, Instagram Reel, YouTube video/Short or a video file on this computer - by downloading it, transcribing the speech with timestamps, adding sound cues (loud, quiet, fast, pauses, music-only stretches) and grabbing a frame at the exact moment each line is said, labelled with the time and the words, tiled into storyboard sheets. Picture and words stay in sync, so Claude sees faces, gestures, on-screen text and tone, not just the transcript. Use whenever the user asks Claude to watch, analyse, summarise, break down, describe or study a video or a video link, check its hook, tone, editing or what is shown on screen, or says "look at this video", even if they don't name this skill.
license: Proprietary. Copyright (c) 2026 Emile Reuben Houessou. All rights reserved. See LICENSE.md.
metadata:
  author: Emile Reuben Houessou
  version: "1.0"
---

# Claude Watch

*Created by Emile Reuben Houessou. Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.*

Claude can't hear audio or play video, so this skill turns a video into things Claude can read and see, in sync:
a timestamped transcript with sound cues, plus storyboard sheets where every frame is labelled with the time and
the words being said at that moment. Never judge a video from its caption or transcript alone: watch it with this.

## How to watch a video

```
python -I <this skill's folder>/scripts/watch.py "<url or path to a video file>" <short-name> "<scratchpad>/vids"
```

Options: `--model small` (Whisper model size; `small` is the default and is good enough, bigger ones are much
slower), `--lang auto` (default; or force a language like `en`, `fr`).

Put the output in the session's scratchpad or a temp folder, not in the user's project. It writes:
- `<name>.timeline.md` (also printed): creator, views, likes, comments, shares, date, length, caption, the sound
  used, then the **synced transcript** (`time | what is said | sound cues`).
- `<name>.storyboard_01.jpg`, `_02.jpg`, ...: frames taken at the moment each line is said, each labelled with
  its time in red and the words below it.

Then **read every storyboard sheet in order** (open each image), alongside the transcript. That is the "watching".

## Reading the results

- **Transcript:** Whisper is the main transcript. Where a Whisper line comes out garbled (often when the speaker
  switches language or uses slang), the platform's own captions for that stretch are swapped in, marked
  `[captions]`. If neither has it, the line is marked UNCLEAR: read the words burned into the video in the frames.
  On-screen text in the frames beats both transcripts.
- **Sound cues:** `LOUDER`, `quiet`, `fast`, `slow/drawn out`, `pause before`, `unclear audio`, and
  `[no speech]` stretches (music or sound only if they are loud).
- **Sound used:** "original sound" means their own voice; a known song or meme sound often means a skit.
- Both transcripts can invent a line in silence or at the end (e.g. "thanks for watching"). Check against the frames.
- Mixed languages are normal. Keep the original words and add a short translation.

## Check the tone before you report on a video

Look at the frames and transcript together, the way a viewer would. Signs of sarcasm, a joke or a skit: a smirk,
grin, eye-roll or deadpan face while saying something extreme; absurd escalation; a punchline or twist at the end;
a comedy/meme sound; #comedy/#skit hashtags or 😂 in the caption; comments playing along with the joke. Signs it is
sincere: calm explaining, a personal story with details, advice with reasons. Give a verdict when it matters:
`SERIOUS`, `SARCASM`, `JOKE/SKIT` or `UNSURE` (mixed is possible: say so).

## When it fails

- `NO VIDEO`: the link is private, deleted, region-locked or needs a login. Update yt-dlp first
  (`yt-dlp -U`, or `pip install -U yt-dlp`), then try again. For a login-only video, ask the user to download it
  and pass the file path instead of the link.
- `yt-dlp` / `ffmpeg` not found, or `No module named faster_whisper`: see the setup in `README.md`.
- Long videos: the script keeps at most 48 frames so the sheets stay readable. To look closer at one part, cut
  that part out with ffmpeg and watch the clip.

## Clean up

Delete the downloaded video and frame sheets when you are done, unless the user wants to keep them.
