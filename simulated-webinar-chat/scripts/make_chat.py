"""Make a WebinarJam-style chat CSV from a spec.
Part of the Simulated Webinar Chat skill.
Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.
Created by Emile Reuben Houessou. See LICENSE.md in the skill folder.

usage: python -I make_chat.py spec.json out.csv

spec.json:
{
  "seed": 11,                          # optional; change it to get a different shuffle
  "names_file": "names.json",          # the researched names (see SKILL.md step 2):
                                       #   {"country": "Ghana", "male": [100 names], "female": [100 names],
                                       #    "surnames": [common surnames]}
  "female_share": 0.5,                 # optional; share of attendees who are women (0-1), default 0.5
  "attendees": 60,                     # optional; how many different people chat, default 60
  "names": ["femi", ...],              # optional; use this exact list instead of names_file
  "edl": "path/to/edl.json",          # optional; list of segments of the FINAL video:
                                       #   {"type":"keep","start":s,"end":e}  (source seconds kept, in order)
                                       #   {"type":"clip"|"beat", "dur":d}     (inserted material)
                                       # with an edl, window times are SOURCE seconds; times in cuts are skipped.
                                       # without an edl, window times are seconds of the final video.
  "events": [
    {"window": [first, last], "messages": ["Hi", "hiiii", "I'm in Accra"]},
    ...
  ]
}
Each message gets a random time inside its window (sorted, so order in the list = order in the chat).
Names are made messy the way real people type them: mostly lowercase, some Capitalised, a few full names,
the odd ALL CAPS, the odd trailing space."""
import sys, os, json, csv, random
sys.stdout.reconfigure(encoding="utf-8")

spec_path = sys.argv[1]
spec = json.load(open(spec_path, encoding="utf-8")); random.seed(spec.get("seed", 11))


def messy(first, surname):
    r = random.random()
    if r < 0.45: n = first.lower()
    elif r < 0.70: n = first.capitalize()
    elif r < 0.80: n = f"{first.lower()} {surname.lower()}" if surname else first.lower()
    elif r < 0.88: n = f"{first.capitalize()} {surname.capitalize()}" if surname else first.capitalize()
    elif r < 0.94: n = first.upper()
    else: n = first.lower()[: max(3, len(first) - 2)] if len(first) > 5 else first.lower()  # nickname-ish
    if random.random() < 0.06: n += " "
    return n


def build_names():
    if spec.get("names"):
        return spec["names"]
    if not spec.get("names_file"):
        sys.exit("No names: research the country's top names first and pass names_file (see SKILL.md).")
    nf = spec["names_file"]
    if not os.path.isabs(nf):
        nf = os.path.join(os.path.dirname(os.path.abspath(spec_path)), nf)
    data = json.load(open(nf, encoding="utf-8"))
    male, female, surnames = data.get("male", []), data.get("female", []), data.get("surnames", [])
    if not male or not female:
        sys.exit("names_file needs both a 'male' and a 'female' list.")
    want, share = int(spec.get("attendees", 60)), float(spec.get("female_share", 0.5))
    nf_count = round(want * share)
    firsts = random.sample(female, min(nf_count, len(female))) + random.sample(male, min(want - nf_count, len(male)))
    out, seen = [], set()
    for f in firsts:
        n = messy(f, random.choice(surnames) if surnames else "")
        if n.strip().lower() not in seen:
            seen.add(n.strip().lower()); out.append(n)
    random.shuffle(out)
    return out


names = build_names()
edl = json.load(open(spec["edl"], encoding="utf-8")) if spec.get("edl") else None


def to_out(t):
    if edl is None: return t
    pos = 0
    for s in edl:
        if s["type"] == "keep":
            if s["start"] <= t < s["end"]: return pos + t - s["start"]
            pos += s["end"] - s["start"]
        else: pos += s["dur"]
    return None


rows = []
for ev in spec["events"]:
    a, b = ev["window"]; msgs = ev["messages"]; ts = []; tries = 0
    while len(ts) < len(msgs) and tries < 10000:
        tries += 1; o = to_out(random.uniform(a, b))
        if o is not None: ts.append(o)
    if len(ts) < len(msgs): print("WARNING: window", ev["window"], "falls in a cut; skipped"); continue
    for o, m in zip(sorted(ts), msgs):
        n = int(o); rows.append((o, [n // 3600, n % 3600 // 60, n % 60, random.choice(names), "Attendee", m, "Text"]))
rows.sort(key=lambda r: r[0])
with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Hour", "Minute", "Second", "Name", "Role", "Message", "Mode"]); w.writerows(r for _, r in rows)
print(len(rows), "messages from", len(names), "attendees ->", sys.argv[2])
