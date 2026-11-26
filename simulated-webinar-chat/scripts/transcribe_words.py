"""Part of the Simulated Webinar Chat skill.
Copyright (c) 2026 Emile Reuben Houessou. All rights reserved.
Created by Emile Reuben Houessou. See LICENSE.md in the skill folder.

Word-timestamp transcript of a video. usage: python -I transcribe_words.py <video> <out_dir> [model=small] [language=en]
Writes <out_dir>/words.jsonl (one segment per line: s, e, t, w=[[start,end,word],...]) and <out_dir>/transcript.txt."""
import sys, subprocess, os, time, wave, json, shutil
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from faster_whisper import WhisperModel
src, out_dir = sys.argv[1], sys.argv[2]; model_name = sys.argv[3] if len(sys.argv) > 3 else "small"
language = sys.argv[4] if len(sys.argv) > 4 else "en"
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
os.makedirs(out_dir, exist_ok=True)
wav = os.path.join(out_dir, "audio16k.wav")
if not os.path.exists(wav):
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
with wave.open(wav, "rb") as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=8)
ts = lambda s: f"{int(s)//3600:d}:{(int(s)%3600)//60:02d}:{s%60:05.2f}"
t0 = time.time()
segs, _ = model.transcribe(audio, language=language, vad_filter=True, beam_size=1, word_timestamps=True, condition_on_previous_text=False)
with open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8") as f, open(os.path.join(out_dir, "words.jsonl"), "w", encoding="utf-8") as g:
    for s in segs:
        f.write(f"[{ts(s.start)}] {s.text.strip()}\n"); f.flush()
        g.write(json.dumps({"s": s.start, "e": s.end, "t": s.text, "w": [[x.start, x.end, x.word] for x in (s.words or [])]}) + "\n"); g.flush()
print("done in", int(time.time() - t0), "s")
