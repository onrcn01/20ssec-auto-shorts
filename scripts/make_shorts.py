#!/usr/bin/env python3
import os, glob, random, subprocess, pathlib

RAW   = "raw_clips"
OUT   = "outputs"
MUSIC = "music"
LOGO  = "logo/20ssec_logo.png"

# Hedef süre (sn). İstersen Actions'da TARGET_SEC ile geçersiz kılabilirsin.
TARGET_SEC = float(os.getenv("TARGET_SEC", "20"))
# Kaç video üretilecek
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

def choose_music_offset(music_path: str, seg_len: float) -> float:
    dur = ffprobe_duration(music_path) or 0.0
    if dur <= seg_len + 1:
        return 0.0
    lo = max(0.0, dur * 0.15)                 # introyu atla
    hi = max(lo, dur * 0.65 - seg_len)        # ortalara kadar
    return round(random.uniform(lo, hi), 2)

def build_cmd(inp, outp, music=None, logo=LOGO, src_dur=None):
    # Kaynak süresi
    Dsrc = src_dur or ffprobe_duration(inp) or 6.0
    # Hedef süre
    T = TARGET_SEC

    # Girişler
    inputs = f'-i "{inp}"'

    # Logo (şeffaf PNG): güvenli image2 + loop
    use_logo = os.path.exists(logo)
    if use_logo:
        inputs += f' -framerate 30 -loop 1 -f image2 -pattern_type none -i "{logo}"'

    # Müzik: intro atla + fade + normalize
    idx_audio_map = "-an"
    afilters = ""
    if music and os.path.exists(music):
        mstart = choose_music_offset(music, T)
        mstart = float(os.getenv("MUSIC_START", mstart))
        inputs += f' -ss {mstart} -i "{music}"'
        idx_audio_map = "-map 2:a'
        af_in = 0.35
        af_out = max(T - 0.60, 0)
        afilters = f'-af "loudnorm=I=-17:TP=-1.5:LRA=11,afade=t=in:st=0:d={af_in},afade=t=out:st={af_out:.2f}:d=0.6"'

    # 720x1280, hafif aydınlatma
    base = (
        "[0:v]fps=30,scale=-2:1280:force_original_aspect_ratio=decrease,"
        "crop=720:1280,eq=brightness=0.05:contrast=1.1:gamma=0.92[base];"
    )

    # Logo overlay (tek, sağ-alt)
    if use_logo:
        base += (
            "[1]scale=-1:ih*0.10,format=rgba,colorchannelmixer=aa=0.60[wm];"
            "[base][wm]overlay=W-w-32:H-h-32:format=auto[ol];"
        )
        last = "[ol]"
    else:
        last = "[base]"

    # Kısa klipleri 20s'e TAMAMLAMA (son 2–4 sn tekrar)
    # Dsrc < T ise: last -> split -> tail trim -> concat -> [vid]
    if Dsrc < T - 0.25:
        tail = max(2.0, min(4.0, Dsrc * 0.4))
        tail_start = max(Dsrc - tail, 0)
        fc = (
            base +
            f"{last}split[vmain][vtail];"
            f"[vtail]trim=start={tail_start}:end={Dsrc},setpts=PTS-STARTPTS[vt];"
            f"[vmain][vt]concat=n=2:v=1:a=0,format=yuv420p[vid]"
        )
    else:
        # Uzunsa/yakınsa: sadece formatla bitir
        fc = base + f"{last}format=yuv420p[vid]"

    # Komut (T saniyede bitir; -shortest ile ses de kesilir)
    cmd = (
        f'ffmpeg -y -hide_banner -stats -loglevel info '
        f'{inputs} -t {T} -filter_complex "{fc}" '
        f'-map "[vid]" {idx_audio_map} {afilters} -shortest '
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
        cmd = build_cmd(v, outp, music=m, src_dur=D)
        print("[CMD]", cmd)
        subprocess.run(cmd, shell=True, check=True)
        print("[OK]", outp)

if __name__ == "__main__":
    main()
