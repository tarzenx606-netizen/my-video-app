"""
Video Automation Tool - Topic do -> HD video lo.
"""
import argparse, os, random
from config import *

from PIL import Image
from moviepy.editor import (VideoFileClip, AudioFileClip, concatenate_videoclips,
                            TextClip, CompositeVideoClip, VideoClip)
import numpy as np
import requests

SIZES = {
    "landscape": (1920, 1080),
    "vertical": (1080, 1920),
}
W, H = SIZES[SIZE]

# ---------------- STEP 1: SCRIPT ----------------
def make_script(topic):
    if OPENAI_KEY:
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                json={"model": "gpt-4o-mini",
                      "messages": [{"role": "user", "content":
                        f"Write a short engaging video script about '{topic}'. "
                        "6-8 short lines, each max 6 words, viral style. "
                        "Return ONLY the lines, one per line."}]},
                timeout=30)
            lines = [l.strip() for l in r.json()["choices"][0]["message"]["content"].splitlines() if l.strip()]
            if lines:
                return lines
        except Exception as e:
            print("[script] AI failed:", e)
    return [
        topic.upper(),
        "Yeh aapko zaroor pata hona chahiye!",
        "Fact #1: chote steps bade results dete hain",
        "Fact #2: consistency > motivation",
        "Fact #3: roz sirf 10 minute kaafi hain",
        "Aaj se start karo!",
        "Follow karo aur share bhi!",
    ]

# ---------------- STEP 2: VOICEOVER ----------------
def make_voiceover(lines, path="temp_voice.mp3"):
    import asyncio, edge_tts
    async def gen():
        communicate = edge_tts.Communicate(". ".join(lines), "en-US-GuyNeural")
        await communicate.save(path)
    asyncio.run(gen())
    return path

# ---------------- STEP 3: CLIPS ----------------
def fetch_pexels_clip(query, out_path):
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get("https://api.pexels.com/videos/search",
                         headers={"Authorization": PEXELS_KEY},
                         params={"query": query, "per_page": 5,
                                 "orientation": "portrait" if SIZE == "vertical" else "landscape"},
                         timeout=20)
        vids = r.json().get("videos", [])
        random.shuffle(vids)
        for v in vids:
            for f in v.get("video_files", []):
                if f.get("link") and (f.get("width") or 0) >= 700:
                    data = requests.get(f["link"], timeout=60).content
                    with open(out_path, "wb") as fh:
                        fh.write(data)
                    return out_path
    except Exception as e:
        print("[pexels]", e)
    return None

def gradient_clip(seconds, seed=None):
    rng = random.Random(seed)
    c1 = np.array(rng.sample(range(40, 220), 3))
    c2 = np.array(rng.sample(range(40, 220), 3))

    def make_frame(t):
        k = 0.5 + 0.5 * np.sin(t * 0.8)
        col = (c1 * (1 - k) + c2 * k).astype(np.uint8)
        img = np.zeros((H, W, 3), dtype=np.uint8)
        img[:, :] = col
        stripe = np.linspace(0, 60, W).astype(np.uint8)
        img[:, :, 0] = (img[:, :, 0].astype(int) + stripe[None, :]).clip(0, 255).astype(np.uint8)
        return img

    return VideoClip(make_frame, duration=seconds)

# ---------------- STEP 4: CAPTIONS ----------------
def caption_clip(text, duration):
    return (TextClip(text, fontsize=FONT_SIZE, color=CAPTION_COLOR,
                     stroke_color="black", stroke_width=3, method="caption",
                     size=(int(W * 0.85), None), font="DejaVu-Sans-Bold")
            .set_duration(duration)
            .set_position(("center", "center")))

# ---------------- MAIN ----------------
def build_video(topic, music_path=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("[1/5] Script bana rahe hain...")
    lines = make_script(topic)
    seg_dur = 4.0

    print("[2/5] Voiceover record ho rahi hai...")
    voice = make_voiceover(lines)
    audio = AudioFileClip(voice)

    print("[3/5] Clips load ho rahe hain...")
    segments = []
    for i, line in enumerate(lines):
        clip_file = f"temp_clip_{i}.mp4"
        if fetch_pexels_clip(topic.split()[0], clip_file):
            seg = (VideoFileClip(clip_file).resize(height=H)
                   .set_duration(seg_dur).set_audio(None))
            if seg.w > W:
                seg = seg.crop(x_center=seg.w / 2, width=W, height=H)
        else:
            seg = gradient_clip(seg_dur, seed=i)
        segments.append(CompositeVideoClip([seg, caption_clip(line, seg_dur)], size=(W, H)))
    base = concatenate_videoclips(segments, method="compose")

    print("[4/5] Audio add ho raha hai...")
    final = base.set_audio(audio)

    out = os.path.join(OUTPUT_DIR, f"video_{random.randint(1000,9999)}.mp4")
    print("[5/5] HD export ho raha hai...")
    final.write_videofile(out, fps=FPS, codec="libx264", audio_codec="aac",
                          preset="medium", threads=4)
    for f in os.listdir("."):
        if f.startswith("temp_clip_") or f == "temp_voice.mp3":
            try: os.remove(f)
            except OSError: pass
    print(f"\nDONE! Video ready: {out}")
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--music", default=os.path.join(ASSETS_DIR, "music.mp3"))
    args = p.parse_args()
    build_video(args.topic, args.music)
