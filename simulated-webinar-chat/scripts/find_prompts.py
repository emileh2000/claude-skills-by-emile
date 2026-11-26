"""Part of the Simulated Webinar Chat skill.
Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.
Created by Emile Reuben Houessou. See LICENSE.md in the skill folder.

List chat prompts ("type X in the chat", "say hi", "comment ...") and reactions ("I can see you guys typing ...").
usage: python -I find_prompts.py <words.jsonl>
Prints time (h:mm:ss.s, seconds) and ~14 words of context. Review each by reading the transcript; this is a finder only."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
words = []
for l in open(sys.argv[1], encoding="utf-8"):
    words += [(s, re.sub(r"[^\w']", "", w.lower())) for s, e, w in json.loads(l)["w"]]
def fmt(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:04.1f} ({t:.1f}s)"
ASK = {"type", "say", "comment", "drop", "write"}
last = {"ask": -99, "ack": -99}
for i, (t, w) in enumerate(words):
    nxt = " ".join(x for _, x in words[i:i+12])
    ctx = " ".join(x for _, x in words[max(0, i-2):i+14])
    kind = None
    if w in ASK and re.search(r"\b(chat|comment|yes|hi|paid|show me|it)\b", nxt): kind = "ask"
    if w == "see" and re.search(r"^see (you guys|some of you|so many|people|a lot)", nxt): kind = "ack"
    if w in ("seeing",) or (w == "typing" and "you guys" in " ".join(x for _, x in words[max(0,i-3):i])): kind = kind or "ack"
    if kind and t - last[kind] > 6:
        print(f"{kind.upper():4s} {fmt(t)}  ...{ctx}..."); last[kind] = t
