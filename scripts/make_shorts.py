# scripts/make_shorts.py
import os, glob, random, subprocess, shlex, pathlib

RAW = "raw_clips"
OUT = "outputs"
MUSIC = "music"
LOGO = "logo/20ssec_logo.png"

MAX_VIDS = 5
HOOKS = [
  "Name a cleaner 360 🌀",
  "Wait for it… 👇",
  "POV: No grip, full control",
  "Rate this 1–10 👇",
  "He didn’t turn — he slid."
]

def ffprobe_duration(path):
    cmd = ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",path]
    out = subprocess.check_output(cmd, text=True).strip()
    try: return float(out)
    except: return None

def build_cmd(inp, outp, music=None, logo=LOGO, hook_text=None, dur_hint=None):
    D = dur_hint or ffprobe_duration(inp) or 12.0
    D = min(D, 20.0)
    start_final_logo = max(D - 2.0, 0)

    inputs = f'-i "{inp}"'
    idx_audio_map = "-an"
    music_part = ""
    if music and os.path.exists(music):
        music_part = f' -stream_loop -1 -i "{music}"'
        idx_audio_map = "-map 2:a -shortest"
    logo_part = f' -i "{logo}"' if os.path.exists(logo) else ""

    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    hook = (hook_text or random.choice(HOOKS)).replace('"','\"')

    # 9:16 kırp + hafif aydınlatma + logo + hook + progress bar
    fc = f"""
 [0:v]fps=30,scale=-2:1920:force_original_aspect_ratio=decrease,
      crop=1080:1920,
      eq=brightness=0.05:contrast=1.1:gamma=0.92[base];
"""
    if os.path.exists(logo):
        fc += f"""
 [1]scale=-1:ih*0.10,format=rgba,colorchannelmixer=aa=0.6[wm];
 [base][wm]overlay=W-w-40:H-h-40:format=auto[ol];
 [1]scale=-1:ih*0.18,format=rgba[wm2];
 [ol][wm2]overlay=(W-w)/2:(H-h)/2:enable='gte(t,{start_final_logo})'[ol2];
"""
        last = "[ol2]"
    else:
        last = "[base]"

    fc += f"""
 {last}drawtext=fontfile={font}:text='{hook}':x=(w-text_w)/2:y=20:
        fontsize=64:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=20:
        enable='lte(t,0.8)'[t1];
 [t1]drawbox=x=0:y=h-20:w=w*t/{D}:h=10:color=white@0.7:t=max[vid]
"""

    cmd = f"""ffmpeg -y {inputs}{logo_part}{music_part} -filter_complex "{fc}" -map "[vid]" {idx_audio_map}  -c:v libx264 -pix_fmt yuv420p -b:v 6M -preset medium -r 30  -c:a aac -ar 44100 -b:a 192k -movflags +faststart "{outp}""""
    return cmd

def main():
    pathlib.Path(OUT).mkdir(exist_ok=True)
    vids = sorted(glob.glob(os.path.join(RAW,"*.mp4")) + glob.glob(os.path.join(RAW,"*.mov")) + glob.glob(os.path.join(RAW,"*.mkv")))
    if not vids:
        print("[ERR] raw_clips boş.")
        return
    musics = sorted(glob.glob(os.path.join(MUSIC,"*.mp3")))
    pick = vids[:MAX_VIDS]
    random.shuffle(pick)
    for i, v in enumerate(pick, 1):
        m = random.choice(musics) if musics else None
        outp = os.path.join(OUT, f"20ssec_output_{i}.mp4")
        D = ffprobe_duration(v)
        cmd = build_cmd(v, outp, music=m, dur_hint=D)
        print("\n[CMD]", cmd)
        subprocess.run(shlex.split(cmd), check=True)
        print("[OK]", outp)

if __name__ == "__main__":
    main()
