# Simulated Webinar Chat

**Created by Emile Reuben Houessou. Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.**

A Claude Code skill that makes a realistic placeholder live-chat CSV (WebinarJam export format) timed to a webinar
recording, for test runs. It asks which country the attendees should come from, researches that country's top 100
male and top 100 female names, and writes messages the way that audience types.

## Install

1. Copy the `simulated-webinar-chat` folder into your Claude skills folder:
   - Windows: `C:\Users\<you>\.claude\skills\simulated-webinar-chat`
   - Mac/Linux: `~/.claude/skills/simulated-webinar-chat`
2. Install the tools it needs (one time):

   **Windows (PowerShell):**
   ```
   winget install Gyan.FFmpeg
   pip install faster-whisper numpy
   ```
   **Mac:**
   ```
   brew install ffmpeg
   pip3 install faster-whisper numpy
   ```
   You also need Python 3.9+ (python.org).
3. Restart Claude Code. Then ask: *"make a simulated chat for my webinar recording <path>"*.

It is test data only: delete it before real attendees see the webinar.

See `LICENSE.md` for what you may and may not do with this skill.
