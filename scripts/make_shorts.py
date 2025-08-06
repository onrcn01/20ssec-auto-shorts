#!/usr/bin/env python3
import os, glob, random, subprocess, pathlib

RAW   = "raw_clips"
OUT   = "outputs"
MAX_VIDS = int(os.getenv("MAX_VIDS", "5"))

# Güvenli, sade filtre: 9:16 + hafif aydınlatma + yuv420p
VF = "fps=30,scale=-2:1920:force_original_aspect_ratio=decrease,crop=1080:1920,eq=brightness=0.05:contrast=1.1:gamma=0.92,format=yuv420p"

def run(cmd):
    print("[CMD]", cmd)
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    print(res.stdout); print(res.stderr)
    res.check_returncode()

def main():
    pathlib.Path(OUT).mkdir(exist_ok=True)
    vids = sorted(glob.glob(os.path.join(RAW, "*.mp4")) +
                  glob.glob(os.path.join(RAW, "*.mov")) +
                  glob.glob(os.path.join(RAW, "*.mkv")))
    if not vids:
        print("[ERR] raw_clips empty"); return

    random.shuffle(vids)
    for i, v in enumerate(vids[:MAX_VIDS], 1):
        outp = os.path.join(OUT, f"20ssec_output_{i}.mp4")
        cmd = (
            f'ffmpeg -y -hide_banner -i "{v}" '
            f'-vf "{VF}" -an '
            f'-c:v libx264 -pix_fmt yuv420p -b:v 6M -preset medium -r 30 '
            f'-movflags +faststart "{outp}"'
        )
        run(cmd)
        print("[OK]", outp)

if __name__ == "__main__":
    main()
