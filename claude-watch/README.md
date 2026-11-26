# Claude Watch

**Created by Emile Reuben Houessou. Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.**

A Claude Code skill that lets Claude really *watch* a video: transcript with timestamps, sound cues, and a frame
grabbed at the moment each line is said, so pictures and words line up.

## Install

1. Copy the `claude-watch` folder into your Claude skills folder:
   - Windows: `C:\Users\<you>\.claude\skills\claude-watch`
   - Mac/Linux: `~/.claude/skills/claude-watch`
2. Install the tools it needs (one time):

   **Windows (PowerShell):**
   ```
   winget install yt-dlp.yt-dlp
   winget install Gyan.FFmpeg
   pip install faster-whisper numpy pillow
   ```
   **Mac:**
   ```
   brew install yt-dlp ffmpeg
   pip3 install faster-whisper numpy pillow
   ```
   You also need Python 3.9+ (python.org). Close and reopen the terminal after installing.
3. Restart Claude Code. Then just ask: *"watch this video and tell me why the hook works: <link>"*.

The first run downloads the Whisper speech model (about 500 MB), once.

See `LICENSE.md` for what you may and may not do with this skill.
