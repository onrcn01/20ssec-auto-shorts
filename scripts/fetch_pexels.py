# scripts/fetch_pexels.py
import os, random, requests, pathlib, argparse
from typing import List

API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
SEARCH_TERMS = ["drift","car drift","drift car","burnout car","touge","jdm drift","track drift"]

def pick_best_file(video_files: List[dict]) -> str:
    vertical = [vf for vf in video_files if (vf.get("height",0) >= vf.get("width",0))]
    cand = vertical or video_files
    if not cand:
        raise RuntimeError("No video_files candidates.")
    cand.sort(key=lambda v: abs((v.get("height",0) - 1920)))
    return cand[0]["link"]

def fetch(n=10, out_dir="raw_clips", min_dur=5, max_dur=25):
    if not API_KEY:
        raise SystemExit("PEXELS_API_KEY yok. GitHub Secrets veya env olarak ekleyin.")
    headers = {"Authorization": API_KEY}
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

    pool = []
    for term in SEARCH_TERMS:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": term, "per_page": 30, "orientation": "portrait", "page": 1},
            timeout=20
        )
        r.raise_for_status()
        for v in r.json().get("videos", []):
            dur = int(v.get("duration", 0))
            if min_dur <= dur <= max_dur:
                pool.append(v)

    if not pool:
        print("Uygun video bulunamadı.")
        return 0

    random.shuffle(pool)
    selected = pool[:n]
    for v in selected:
        url = pick_best_file(v.get("video_files", []))
        vid_id = v.get("id")
        path = pathlib.Path(out_dir) / f"pexels_{vid_id}.mp4"
        if path.exists():
            continue
        with requests.get(url, stream=True, timeout=60) as s:
            s.raise_for_status()
            with open(path, "wb") as f:
                for chunk in s.iter_content(1<<20):
                    if chunk: f.write(chunk)
    print(f"{len(selected)} video indirildi.")
    return len(selected)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default="raw_clips")
    args = ap.parse_args()
    fetch(n=args.n, out_dir=args.out)
