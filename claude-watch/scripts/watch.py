"""watch.py - "watch" a TikTok / IG Reel / YouTube video properly.
Part of the Claude Watch skill.
Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.
Created by Emile Reuben Houessou. See LICENSE.md in the skill folder.

Usage:  python -I watch.py <url-or-video-file> <name> <out_dir> [--model small] [--lang auto|en|fr|...]

Claude can't hear audio, so this turns the video into things it can read and see:
  1. Downloads the video + its info (stats, caption, hashtags, the sound/song used).
  2. Transcribes the speech locally with faster-whisper, with timestamps.
  3. Adds sound cues per line: loudness vs the video's average, speaking speed,
     pauses, and stretches with no speech (music / sound only).
  4. Grabs frames at the moment each line is said and labels each frame with
     the time + the words, then tiles them into storyboard_XX.jpg sheets.
     Read the sheets in order: picture and words are in sync.
Writes <out_dir>/<name>.timeline.md (stats + synced transcript) and prints it.
"""
import json, os, subprocess, sys, wave, glob, shutil

# Finds yt-dlp and ffmpeg on any computer: first on the PATH, then (Windows) in the
# WinGet install folder of whoever is running this.
WINGET = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
def find_tool(name, sub):
    found = shutil.which(name)
    if found:
        return found
    hits = glob.glob(os.path.join(WINGET, sub)) if os.environ.get("LOCALAPPDATA") else []
    return hits[0] if hits else name
YT = find_tool("yt-dlp", r"yt-dlp.yt-dlp_*\yt-dlp.exe")
FF = find_tool("ffmpeg", r"Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe")

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

def fmt(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    model_size, lang = "small", None
    if "--model" in a:
        i = a.index("--model"); model_size = a[i + 1]; del a[i:i + 2]
    if "--lang" in a:  # default auto: speakers often mix languages, so language is detected line by line
        i = a.index("--lang"); lang = None if a[i + 1] == "auto" else a[i + 1]; del a[i:i + 2]
    url, name, out = a[0], a[1], a[2]
    local = os.path.isfile(url)
    if local:
        url = os.path.abspath(url)
    os.makedirs(out, exist_ok=True); os.chdir(out)

    # 1. download video + info (a video file on this computer is used as-is)
    if local:
        shutil.copy(url, f"{name}{os.path.splitext(url)[1].lower() or '.mp4'}")
        r = subprocess.CompletedProcess([], 0, "", "")
    else:
        r = run([YT, "-q", "--no-warnings", "-f", "b[ext=mp4][acodec!=none]/bv*+ba/b", "--merge-output-format", "mp4", "--write-info-json",
                 "--write-subs", "--write-auto-subs", "--sub-langs", "en,en-orig,eng,en-US,en-GB",
                 "-o", f"{name}.%(ext)s", url])
    vids = [f for f in (f"{name}.mp4", f"{name}.webm", f"{name}.mkv", f"{name}.mov") if os.path.exists(f)]
    if not vids and not local:  # subtitles can fail (e.g. rate limit) and stop the download: retry without them
        r = run([YT, "-q", "--no-warnings", "-f", "b[ext=mp4][acodec!=none]/bv*+ba/b", "--merge-output-format", "mp4", "--write-info-json", "-o", f"{name}.%(ext)s", url])
        vids = [f for f in (f"{name}.mp4", f"{name}.webm", f"{name}.mkv") if os.path.exists(f)]
    if not vids:
        print("NO VIDEO", r.stderr[-500:]); sys.exit(1)
    vid = vids[0]
    info = {}
    if os.path.exists(f"{name}.info.json"):
        info = json.load(open(f"{name}.info.json", encoding="utf-8"))
    dur = float(info.get("duration") or 0)

    # 2. audio -> wav, transcribe
    run([FF, "-y", "-loglevel", "error", "-i", vid, "-ac", "1", "-ar", "16000", f"{name}.wav"])
    import numpy as np
    from faster_whisper import WhisperModel
    w = wave.open(f"{name}.wav"); sr = w.getframerate()
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    w.close()
    if not dur:
        dur = len(audio) / sr
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segs_iter, tinfo = model.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False,
                                        condition_on_previous_text=False)
    wsegs = [(s.start, s.end, s.text.strip(), s.avg_logprob) for s in segs_iter if s.text.strip()]

    # platform captions (TikTok/IG/YouTube's own speech-to-text) = BACKUP transcript.
    # Whisper is the main one. Where a Whisper line comes out garbled (often when a
    # speaker switches mid-sentence to another language or slang), the
    # captions for that time range are used instead. If the captions don't cover it
    # either, the line is marked UNCLEAR: read the words burned into the frames.
    import re
    def secs(h, m, x): return int(h or 0) * 3600 + int(m) * 60 + float(x)
    psegs, seen = [], set()
    vtts = glob.glob(f"{name}*.vtt")
    if vtts:
        t0 = t1 = None
        for ln in open(vtts[0], encoding="utf-8", errors="replace").read().splitlines():
            m = re.match(r"(?:(\d+):)?(\d+):(\d+\.\d+)\s*-->\s*(?:(\d+):)?(\d+):(\d+\.\d+)", ln)
            if m:
                t0, t1 = secs(*m.groups()[:3]), secs(*m.groups()[3:]); continue
            ln = re.sub(r"<[^>]+>", "", ln).strip()
            if t0 is not None and ln and ln not in seen:
                seen.add(ln); psegs.append((t0, t1, ln, None))
    def garbled(text, lp):
        letters = [c for c in text if c.isalpha()]
        if not letters: return True
        foreign = sum(1 for c in letters if ord(c) > 0x24F)  # not Latin script
        return foreign / len(letters) > 0.2 or (lp is not None and lp < -1.0)
    segs, swapped = [], 0
    for st, en, text, lp in wsegs:
        if not garbled(text, lp):
            segs.append((st, en, text, lp)); continue
        fill = [(max(a, st), min(b, en), f"[captions] {t}", None) for a, b, t, _ in psegs
                if a < en and b > st]
        if fill:
            segs += fill; swapped += 1
        else:
            segs.append((st, en, "[UNCLEAR: Whisper garbled this and no platform captions. "
                                 "Read the on-screen words in the frames]", None))
    if not wsegs:
        segs = list(psegs)
    primary = ("Whisper" + (f", with {swapped} garbled part(s) replaced by platform captions" if swapped else "")
               if wsegs else "platform captions (Whisper heard nothing)")

    # 3. sound cues
    def db(t0, t1):
        x = audio[int(t0 * sr):int(t1 * sr)]
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9) if len(x) else -99
    avg = db(0, dur)
    rows, prev_end = [], 0.0
    for st, en, text, lp in segs:
        if st - prev_end >= 1.5:
            rows.append(("gap", prev_end, st, f"[no speech: {db(prev_end, st):.0f} dB, music/sound only if loud]", ""))
        words = len(text.split()); rate = words / max(en - st, 0.1)
        loud = db(st, en) - avg
        cues = []
        if loud > 4: cues.append("LOUDER")
        if loud < -6: cues.append("quiet")
        if rate > 3.6: cues.append("fast")
        if rate < 1.6: cues.append("slow/drawn out")
        if st - prev_end >= 0.8 and prev_end > 0: cues.append(f"pause {st - prev_end:.1f}s before")
        if lp is not None and lp < -1.0: cues.append("unclear audio")
        rows.append(("say", st, en, text, ", ".join(cues)))
        prev_end = max(prev_end, en)
    if dur - prev_end >= 1.5:
        rows.append(("gap", prev_end, dur, f"[no speech: {db(prev_end, dur):.0f} dB]", ""))
    if not segs:
        rows.append(("gap", 0, dur, "[NO SPEECH DETECTED: music / sound / text-only video]", ""))

    # 4. synced frames
    from PIL import Image, ImageDraw, ImageFont
    times = []
    for kind, t0, t1, text, _ in rows:
        span = t1 - t0
        pts = [t0 + 0.15, (t0 + t1) / 2] if span > 1.2 else [(t0 + t1) / 2]
        if span > 5: pts.append(t1 - 0.3)
        if kind == "gap" and span > 4:
            pts = [t0 + k * span / 4 for k in range(1, 4)]
        for p in pts:
            times.append((min(max(p, 0), max(dur - 0.1, 0)), text if kind == "say" else text.split(":")[0] + "]"))
    times = sorted(dict((round(t, 1), x) for t, x in times).items())
    if len(times) > 48:  # keep sheets readable on long videos
        step = len(times) / 48; times = [times[int(i * step)] for i in range(48)]
    def load_font(names, size):
        for n in names:
            try:
                return ImageFont.truetype(n, size)
            except OSError:
                pass
        return ImageFont.load_default()
    font = load_font([r"C:\Windows\Fonts\arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
                      "/Library/Fonts/Arial.ttf", "DejaVuSans.ttf"], 17)
    fontb = load_font([r"C:\Windows\Fonts\arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                       "/Library/Fonts/Arial Bold.ttf", "DejaVuSans-Bold.ttf"], 18)
    W, IMH, CAP = 300, 533, 120
    grabs = []
    for i, (t, text) in enumerate(times):
        f = f"{name}.f{i:03d}.jpg"
        run([FF, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", vid, "-frames:v", "1", "-q:v", "3", f])
        if not os.path.exists(f): continue
        im = Image.open(f).convert("RGB"); im.thumbnail((W, IMH)); os.remove(f)
        grabs.append((t, text, im))
    if grabs:  # fit panels to the video's shape (vertical or landscape)
        IMH = max(im.height for _, _, im in grabs)
    panels = []
    for t, text, im in grabs:
        pan = Image.new("RGB", (W, IMH + CAP), "white")
        pan.paste(im, ((W - im.width) // 2, 0))
        d = ImageDraw.Draw(pan)
        d.text((6, IMH + 4), fmt(t), fill="red", font=fontb)
        line, y = "", IMH + 26
        for word in ('"' + text + '"').split():
            if d.textlength(line + " " + word, font=font) > W - 12:
                d.text((6, y), line, fill="black", font=font); y += 20; line = word
                if y > IMH + CAP - 20: line += " ..."; break
            else:
                line = (line + " " + word).strip()
        d.text((6, y), line, fill="black", font=font)
        panels.append(pan)
    per = 8
    sheets = []
    for k in range(0, len(panels), per):
        grp = panels[k:k + per]; cols = 4; rws = (len(grp) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (W + 6), rws * (IMH + CAP + 6)), "#888")
        for j, p in enumerate(grp):
            sheet.paste(p, ((j % cols) * (W + 6), (j // cols) * (IMH + CAP + 6)))
        fn = f"{name}.storyboard_{k // per + 1:02d}.jpg"; sheet.save(fn, quality=85); sheets.append(os.path.abspath(fn))

    # 5. timeline file
    snd = info.get("track") or ""
    if info.get("artists") or info.get("artist"):
        snd += " by " + ", ".join(info.get("artists") or [info.get("artist")])
    L = [f"# {name}", f"URL: {url}",
         f"Creator: @{info.get('uploader') or info.get('channel') or info.get('uploader_id')} | {info.get('view_count')} views | "
         f"{info.get('like_count')} likes | {info.get('comment_count')} comments | {info.get('repost_count')} shares | "
         f"posted {info.get('upload_date')} | {dur:.0f}s",
         f"Caption: {(info.get('description') or '').strip()[:400]}",
         f"Sound used: {snd or 'unknown'}  (original sound = their own voice; a known song/meme sound often means a skit)",
         f"Whisper's main language guess: {tinfo.language} ({tinfo.language_probability:.0%}). Speech can mix languages: "
         "keep the original words and add a translation for lines not in the main language",
         "", f"## Synced transcript, from {primary} (time | what is said | sound cues)"]
    for kind, t0, t1, text, cues in rows:
        L.append(f"- {fmt(t0)}-{fmt(t1)} | {text}" + (f" | {cues}" if cues else ""))
    L += ["", "## Storyboards (read in order; each frame is labelled with its time and the words said then)"]
    L += [f"- {s}" for s in sheets]
    if wsegs and psegs:
        L += ["", "## Backup: platform captions (use to fill gaps or check words Whisper missed; the words burned into the frames decide)"]
        L += [f"- {fmt(a)}-{fmt(b)} | {t}" for a, b, t, _ in psegs]
    L += ["", "Note: both transcripts can mishear mixed-language speech, and both can invent a line in silence or "
          "at the end (e.g. 'thanks for watching'). On-screen captions in the frames beat both."]
    open(f"{name}.timeline.md", "w", encoding="utf-8").write("\n".join(L))
    for f in (f"{name}.wav",):
        if os.path.exists(f): os.remove(f)
    print("\n".join(L))

if __name__ == "__main__":
    main()
