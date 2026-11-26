---
name: simulated-webinar-chat
description: Makes a simulated (placeholder) live-chat CSV for a recorded webinar, in the WebinarJam chat-export format (Hour, Minute, Second, Name, Role, Message, Mode), timed to the recording - replies land a few seconds after the presenter says "type X in the chat" and just before the presenter reacts ("I can see you guys typing..."), with messy real-looking names researched for the audience's country (top 100 male and top 100 female names), messages written the way people from that country type, hellos, reactions and "paid" messages after the pay link. Used as test data for test runs of a webinar or evergreen-webinar setup, deleted before real attendees. Use whenever the user asks for simulated, fake, placeholder, test or dummy webinar chat/comments, or a chat CSV for a webinar, even if they don't name this skill.
license: Proprietary. Copyright (c) 2026 Emile Reuben Houessou. All rights reserved. See LICENSE.md.
metadata:
  author: Emile Reuben Houessou
  version: "1.0"
---

# Simulated webinar chat

*Created by Emile Reuben Houessou. Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.*

Builds a chat CSV that looks like a real WebinarJam chat export for a given webinar recording. It is **test data**:
the user loads it into their webinar setup to check that comments show up in the right places during a test run,
then deletes it before real attendees arrive. Make it look like a real export, "paid" messages included.

## What "realistic" means

1. **Typing delay.** Nobody replies the instant the presenter asks. Replies to a prompt start about **3-4 s after
   the presenter first says "type X"** and spread out over the following seconds.
2. **Before the reaction.** If the presenter reacts on the recording ("I can see you guys typing...", "I can see
   some of you saying paid already"), every reply for that prompt lands **at least ~1 s before** that line. If they
   never react, keep the burst within ~10 s of the ask.
3. **Messy names from the audience's country.** Real people type their names however they like: mostly lowercase,
   some Capitalised, a few full names, the odd ALL CAPS, the odd trailing space. Never all neatly capitalised.
   `make_chat.py` does this for you from the researched name lists. **Never reuse names from a real chat export**
   (those are real people).
4. **Messages that sound like that audience.** Short and varied in case and spelling: `Hi`, `hiiii`, `Hello sir`,
   `yes`, `YESSS`, `show mee`, `wow`, `paid`, `paid, I'm 2nd`, `payment sent`, `God bless you`, `hmm not bad
   actually`. Use the slang, spelling and city names people from the chosen country really use online (e.g.
   Nigeria: `Yes o`, `I'm in Lagos`; Ghana: `Chale this is good`, `from Kumasi`; UK: `hiya`, `from Leeds`).
   If unsure, look at real comment sections from that country to get the feel; never copy real people's comments.
5. **Format.** Columns `Hour,Minute,Second,Name,Role,Message,Mode`; Role `Attendee`; Mode `Text`; times are whole
   seconds from the start of the video; UTF-8.

## Workflow

### 1. Ask where the audience is from
Before anything else, ask the user (use the question tool if you have one): **"Which country should the attendees'
names come from?"** Offer a few likely options (e.g. Nigeria, Ghana, Kenya, South Africa, USA, UK) plus "other",
and whether to mix countries. Also ask roughly what share should be women (default 50/50) if it matters to them.

### 2. Research the top names for that country
Search the web for that country's **top 100 male first names** and, separately, its **top 100 female first names**
(official baby-name statistics, census or name-frequency sites; recent years first). Also collect ~30 common
surnames. If a source has fewer than 100, combine two sources and remove duplicates. For a country with several
large ethnic or language groups, make sure the lists cover them in roughly real proportions.

Save them next to the spec as `names.json`:
```json
{"country": "Ghana", "sources": ["<url>", "<url>"],
 "male": ["Kwame", "Kofi", "..."], "female": ["Ama", "Akosua", "..."], "surnames": ["Mensah", "Owusu", "..."]}
```
Tell the user in one line which sources you used. Reuse an existing `names.json` for the same country.

### 3. Get word timings for the exact video that will play
Timings must match the **final file** the user will upload (the edited version, not the raw recording, if there is one).
- If a word-timestamp transcript (`words.jsonl`) for that file already exists, reuse it.
- Otherwise run `scripts/transcribe_words.py <video> <out_dir> [small] [en]` (faster-whisper `small` on CPU, about
  20 min for 80 min of audio; the last argument is the spoken language). Run it in the background.
- If the video is an edit made from a raw recording with an edit list (`edl*.json`), you can transcribe the raw
  recording and pass the edit list to `make_chat.py`, which maps raw times to final times and drops anything that
  falls in a cut.

### 4. Find the prompts and the reactions
Run `scripts/find_prompts.py <words.jsonl>`. It lists every "type/say/comment ... in the chat" ask and every
"I can see / you guys typing / saying" reaction with times and context. Read the transcript around each one
yourself: the finder is a starting point, not the answer.

For each prompt decide a **window** `[first, last]` in seconds:
- `first` = time of the first "type X" + 3 to 4 s
- `last` = time of the reaction − 1 s (or `first` + ~8 s if there's no reaction)

Also add, without a prompt:
- a few early hellos in the first ~20 s (people joining) and more before the presenter says "I can see you saying hi";
- cities from the chosen country mixed into the hellos if the presenter asks where people are from (or 1-3 anyway);
- 2-3 "wow / that's impressive" right after each demo shown;
- around the offer: `i need this`, `nice`, `God bless you`, `hmm not bad actually`;
- **paid** messages only **after the pay link** first appears, with numbers that match what is said on the
  recording (if the presenter says "about four or five have joined", have about 5 paid before that line).

### 5. Generate the CSV
Write a spec JSON (format in `scripts/make_chat.py`'s docstring) that points at `names.json`, and run:

```
python -I scripts/make_chat.py spec.json out.csv
```

It builds a pool of attendees (default 60) from the researched names, makes their names messy, places each message
at a random time inside its window, sorts everything, maps through the edit list if given, and writes the CSV. Put
the CSV in the user's project folder, and tell the user which video version it is timed to.

### 6. Check before handing over
- Spot-check 3-4 prompts: the first reply is a few seconds after the ask, the last is before the reaction.
- No "paid" before the pay link.
- Names look messy and fit the chosen country; messages look varied.
- Tell the user the total message count, the country, and the video version the times match.
- Remind them to delete the simulated chat before real attendees see the webinar.

## Example (Nigerian audience, invented names)
```
Hour,Minute,Second,Name,Role,Message,Mode
0,0,9,ruth,Attendee,Hello,Text
0,0,18,Halima,Attendee,Good evening,Text
0,1,36,folake,Attendee,I'm in Lagos,Text
0,1,42,obinna eze,Attendee,hi from Abuja,Text
0,1,45,NGOZI,Attendee,hiiii,Text
0,23,11,kelechi,Attendee,Yes o,Text
1,9,52,Funmilayo ,Attendee,"payment sent, i am 5th",Text
```

## Notes
- Windows: run Python with `-I`. Audio is decoded with ffmpeg to a 16 kHz mono wav and read with the `wave` module.
- Needs Python 3.9+, ffmpeg and `pip install faster-whisper numpy` (see `README.md`).
- If the edit changes later, regenerate the chat from the same spec with the new edit list. Don't shift times by hand.
