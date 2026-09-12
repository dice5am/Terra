#!/usr/bin/env python3
"""Headless Chrome proof frames for S0/S1/S3/S5 × ios/android + S5 closeup."""
from __future__ import annotations
import subprocess, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "proof"
PROOF.mkdir(exist_ok=True)
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

CHROME = "google-chrome"
SIZE = "390,844"  # logical phone

def capture(url: str, out: Path, wait_ms=2500, clip=None):
    out.parent.mkdir(parents=True, exist_ok=True)
    # Use CDP via chrome headless screenshot
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=2",
        f"--window-size={SIZE}",
        f"--screenshot={out}",
        url,
    ]
    # Chrome --screenshot doesn't support wait; use virtual time budget via timeout + run twice
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if not out.exists():
        print("FAIL", out, r.stderr[-500:])
        return False
    print("OK", out, out.stat().st_size)
    return True

def main():
    # assume server already running
    frames = []
    for plat in ("ios", "android"):
        for mode in ("S0", "S1", "S3", "S5"):
            url = f"{BASE}/?platform={plat}&mode={mode}"
            out = PROOF / f"{mode.lower()}-{plat}.png"
            frames.append((url, out))
    # S5 closeup — same S5 ios, we'll crop after
    ok = 0
    for url, out in frames:
        # warm + capture: chrome loads then screenshots; add query cachebust
        if capture(url + f"&t={int(time.time()*1000)}", out):
            ok += 1
        time.sleep(0.3)

    # Closeup from S5 ios using PIL crop of central globe
    try:
        from PIL import Image
        src = PROOF / "s5-ios.png"
        if src.exists():
            im = Image.open(src)
            w, h = im.size
            # center crop ~ India/Pacific region for volume spill feel
            cw, ch = int(w * 0.55), int(h * 0.40)
            left = (w - cw) // 2 + int(w * 0.05)
            top = (h - ch) // 2 - int(h * 0.02)
            crop = im.crop((left, top, left + cw, top + ch))
            crop.save(PROOF / "s5-closeup.png")
            print("OK", PROOF / "s5-closeup.png")
            ok += 1
    except Exception as e:
        print("closeup skip", e)

    # Also try puppeteer-like wait with chrome remote — if first captures are blank white,
    # use a longer virtual-time approach via html dump.
    print(f"captured {ok} frames into {PROOF}")

if __name__ == "__main__":
    main()
