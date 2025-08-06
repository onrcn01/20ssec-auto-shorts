#!/usr/bin/env python3
import os, glob, random, subprocess, pathlib

RAW   = "raw_clips"
OUT   = "outputs"
MUSIC = "music"
LOGO  = "logo/20ssec_logo.png"

# İlk tur için 3 video (sonra 5/8 yaparız)
MAX_VIDS = int(os.getenv("MAX_VIDS", "3"))

def ffprobe_duration(path: str):
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1", path],
            text=True
        ).strip()
        return float(out)
    except Exception:
        return None

def build_cmd(inp, outp, music=None, logo=LOGO, dur_hint=None):
    # Maks 12 saniye
    D = dur_hint or ffprobe_duration(inp) or 12.0
    D = min(D, 12.0)

    # Girişler
    inputs = f'-i "{inp}"'

    # LOGO (şeffaf PNG) – güvenli image2 + loop
    use_logo = os.path.exists(logo)
    if use_logo:
        inputs += f' -framerate 30 -loop 1 -f image2 -pattern_type none -i "{logo}"'

    # MÜZİK (varsa)
    idx_audio_map = "-an"
    if music and os.path.exists(music):
        inputs += f' -stream_loop -1 -i "{music}"'
        idx_audio_map = "-map 2:a -shortest"

    # 720x1280, hafif aydınlatma
    fc = (
        "[0:v]fps=30,scale=-2:1280:force_original_aspect_ratio=decrease,"
        "crop=720:1280,eq=brightness=0.05:contrast=1.1:gamma=0.92[base];"
    )
    if use_logo:
        fc += (
            "[1]scale=-1:ih*0.10,format=rgba,colorchannelmixer=aa=0.60[wm];"
            "[base][wm]overlay=W-w-32:H-h-32:format=auto[vid]"
        )
    else:
        fc += " [base]format=yuv420p[vid]"

    # Hızlı encode + canlı ilerleme
    cmd = (
        f'ffmpeg -y -hide_banner -stats -loglevel info '
        f'{inputs} -t {D} -filter_complex "{fc}" '
        f'-map "[vid]" {idx_audio_map} -shortest '
        f'-c:v libx264 -pix_fmt yuv420p -crf 26 -preset veryfast -r 30 '
        f'-c:a aac -ar 44100 -b:a 128k -movflags +faststart "{outp}"'
    )
    return cmd

def main():
    pathlib.Path(OUT).mkdir(exist_ok=True)
    vids = sorted(
        glob.glob(os.path.join(RAW, "*.mp4")) +
        glob.glob(os.path.join(RAW, "*.mov")) +
        glob.glob(os.path.join(RAW, "*.mkv"))
    )
    if not vids:
        print("[ERR] raw_clips empty"); return

    random.shuffle(vids)
    pick = vids[:MAX_VIDS]
    musics = sorted(glob.glob(os.path.join(MUSIC, "*.mp3")))

    for i, v in enumerate(pick, 1):
        m = random.choice(musics) if musics else None
        outp = os.path.join(OUT, f"20ssec_output_{i}.mp4")
        D = ffprobe_duration(v)
        cmd = build_cmd(v, outp, music=m, dur_hint=D)
        print("[CMD]", cmd)
        # Canlı ilerleme için capture_output=False
        subprocess.run(cmd, shell=True, check=True)
        print("[OK]", outp)

if __name__ == "__main__":
    main()
