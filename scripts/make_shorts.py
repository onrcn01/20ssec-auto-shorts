#!/usr/bin/env python3
import os, glob, random, subprocess, pathlib

RAW   = "raw_clips"
OUT   = "outputs"
MUSIC = "music"
LOGO  = "logo/20ssec_logo.png"

# Günlük üretilecek kısa video sayısı (env ile override edebilirsin)
MAX_VIDS = int(os.getenv("MAX_VIDS", "5"))

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
    D = dur_hint or ffprobe_duration(inp) or 12.0
    D = min(D, 20.0)

    # Girişler
    inputs = f'-i "{inp}"'

    # Logo (tek küçük watermark, tüm süre): image2 + loop güvenli
    use_logo = os.path.exists(logo)
    if use_logo:
        inputs += f' -framerate 30 -loop 1 -f image2 -pattern_type none -i "{logo}"'

    # Müzik (varsa)
    idx_audio_map = "-an"
    if music and os.path.exists(music):
        inputs += f' -stream_loop -1 -i "{music}"'
        idx_audio_map = "-map 2:a -shortest"

    # Filtre grafiği
    fc = (
        "[0:v]fps=30,scale=-2:1920:force_original_aspect_ratio=decrease,"
        "crop=1080:1920,eq=brightness=0.05:contrast=1.1:gamma=0.92[base];"
    )

    last = "[base]"
    if use_logo:
        # sadece tek watermark: sağ-alt, %10 yükseklik
        fc += (
            "[1]scale=-1:ih*0.10,format=rgba,colorchannelmixer=aa=0.60[wm];"
            "[base][wm]overlay=W-w-40:H-h-40:format=auto[ol];"
        )
        last = "[ol]"

    # Progress bar (stabil): t=fill ve çıktıyı [vid] olarak etiketle
    fc += f"{last}drawbox=x=0:y=h-20:w=w*(t/{D}):h=10:color=white@0.7:t=fill[vid]"

    cmd = (
        f'ffmpeg -y -hide_banner {inputs} -filter_complex "{fc}" '
        f'-map "[vid]" {idx_audio_map} -shortest '
        f'-c:v libx264 -pix_fmt yuv420p -b:v 6M -preset medium -r 30 '
        f'-c:a aac -ar 44100 -b:a 192k -movflags +faststart "{outp}"'
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
        print("[ERR] raw_clips empty")
        return

    random.shuffle(vids)
    pick = vids[:MAX_VIDS]
    musics = sorted(glob.glob(os.path.join(MUSIC, "*.mp3")))

    for i, v in enumerate(pick, 1):
        m = random.choice(musics) if musics else None
        outp = os.path.join(OUT, f"20ssec_output_{i}.mp4")
        D = ffprobe_duration(v)
        cmd = build_cmd(v, outp, music=m, dur_hint=D)
        print("[CMD]", cmd)
        res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        print(res.stdout)
        print(res.stderr)
        res.check_returncode()
        print("[OK]", outp)

if __name__ == "__main__":
    main()
