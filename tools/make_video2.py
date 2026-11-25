"""Video produk 9:16 gaya affiliate TikTok.

Ciri: voiceover, tajuk atas (kekal), subtitle bawah ikut ayat, tangan+produk bergoyang,
zoom background, tukar background dengan efek glitch, glitch di awal & hujung.

Guna:  python3 tools/make_video2.py config.json
"""
import json, math, os, random, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

cfg = json.load(open(sys.argv[1]))
W, H, FPS = 1080, 1920, 30
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_DIR = os.path.join(REPO, "background")
rng = random.Random(cfg.get("seed"))
FONT = cfg.get("font") or next(f for f in [
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Black.ttf"] if os.path.exists(f))


def audio_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout
    return float(out.strip())


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def pick_backgrounds(n):
    if cfg.get("backgrounds"):
        files = cfg["backgrounds"]
    else:
        files = sorted(os.path.join(BG_DIR, f) for f in os.listdir(BG_DIR)
                       if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        rng.shuffle(files)
    return [files[i % len(files)] for i in range(n)]


# ---------- teks ----------
emojis = {k: Image.open(v).convert("RGBA") for k, v in cfg.get("emoji", {}).items()}


def text_block(text, size, max_w, stroke, box=None):
    """Teks putih (wrap automatik), token :nama: jadi emoji. box=(r,g,b,a) untuk latar."""
    font = ImageFont.truetype(FONT, size)
    sp = int(size * 0.28)
    def tok_w(t):
        return int(size * 1.05) if t in emojis else int(font.getlength(t))
    lines, cur, cw = [], [], 0
    for tok in text.split():
        w = tok_w(tok)
        if cur and cw + sp + w > max_w:
            lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + w; cur.append(tok)
    if cur: lines.append(cur)
    lh = int(size * 1.28); pad = int(size * 0.35) if box else stroke + 6
    lw = [sum(tok_w(t) for t in ln) + sp * (len(ln) - 1) for ln in lines]
    bw, bh = max(lw) + pad * 2, lh * len(lines) + pad * 2 - int(size * 0.18)
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if box:
        d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=int(size * 0.35), fill=box)
    for i, ln in enumerate(lines):
        x = pad + (bw - pad * 2 - lw[i]) // 2; y = pad + i * lh
        for t in ln:
            if t in emojis:
                e = emojis[t].resize((size, size), Image.LANCZOS)
                im.alpha_composite(e, (x, y + int(size * 0.08)))
            else:
                d.text((x, y), t, font=font, fill="white", stroke_width=stroke, stroke_fill="black")
            x += tok_w(t) + sp
    return im


def subtitles(text, dur):
    """Pecah ikut ayat/koma, masa ikut panjang aksara."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?,])\s+", text) if p.strip()]
    total = sum(len(p) for p in parts); t = cfg.get("voice_start", 0.35); out = []
    usable = dur - t - 0.1
    for p in parts:
        d = usable * len(p) / total
        out.append((t, t + d, text_block(p.rstrip(",."), cfg.get("sub_size", 58), 900, 0, box=(0, 0, 0, 150))))
        t += d
    return out


# ---------- glitch ----------
STRIPES = np.array([(255, 60, 60), (255, 220, 0), (60, 255, 120), (0, 200, 255), (170, 60, 255), (255, 0, 200)], np.uint8)


def glitch(arr, k, seed):
    """k = 0..1 kekuatan glitch."""
    if k <= 0: return arr
    r = np.random.default_rng(seed)
    out = arr.copy()
    # anjak jalur mendatar
    for _ in range(int(6 + 30 * k)):
        y = r.integers(0, H - 40); h = r.integers(8, 90); dx = int(r.integers(-160, 160) * k)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    # pisah warna RGB
    s = int(24 * k)
    out[..., 0] = np.roll(out[..., 0], s, axis=1); out[..., 2] = np.roll(out[..., 2], -s, axis=1)
    # jalur warna pelangi
    if k > 0.35:
        cols = STRIPES[(np.arange(W) // r.integers(40, 120) + r.integers(0, 6)) % len(STRIPES)]
        jitter = r.integers(-30, 30, size=(H, 1))
        band = np.take_along_axis(np.broadcast_to(cols, (H, W, 3)),
                                  ((np.arange(W)[None, :] + jitter) % W)[..., None].repeat(3, 2), axis=1)
        a = min(1.0, (k - 0.35) * 1.6)
        out = (out * (1 - a) + band * a).astype(np.uint8)
    return out


# ---------- sediakan ----------
voice = cfg.get("voice")
dur = cfg.get("duration") or (audio_duration(voice) + cfg.get("voice_start", 0.35) + 0.6)
N = int(dur * FPS)
n_scenes = cfg.get("scenes", 2)
bgs = [cover(Image.open(p).convert("RGB"), W, H) for p in pick_backgrounds(n_scenes)]
cuts = [dur * i / n_scenes for i in range(1, n_scenes)]

prod = Image.open(cfg["product"]).convert("RGBA"); prod = prod.crop(prod.getbbox())
pw = int(W * cfg.get("product_scale", 0.9)); ph = int(prod.height * pw / prod.width)
prod = prod.resize((pw, ph), Image.LANCZOS)
anchor = cfg.get("anchor", "bottom-right")   # dari mana tangan masuk
ox, oy = cfg.get("offset", [0, 0])
if anchor == "bottom-right": px, py = W - pw + ox, H - ph + oy
elif anchor == "bottom-left": px, py = ox, H - ph + oy
else: px, py = (W - pw) // 2 + ox, H - ph + oy

headline = text_block(cfg["headline"], cfg.get("headline_size", 64), 980, 7)
subs = subtitles(cfg["script"], dur) if cfg.get("script") else []

cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
if voice:
    cmd += ["-itsoffset", str(cfg.get("voice_start", 0.35)), "-i", voice, "-map", "0:v", "-map", "1:a",
            "-af", "apad", "-t", f"{dur:.3f}"]
else:
    cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest"]
cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "160k", cfg["output"]]
ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)

for f in range(N):
    t = f / FPS
    si = sum(t >= c for c in cuts)
    s0 = ([0] + cuts)[si]; s1 = (cuts + [dur])[si]
    z = 1.0 + 0.07 * (t - s0) / (s1 - s0)
    bw, bh = int(W * z), int(H * z)
    frame = bgs[si].resize((bw, bh), Image.BILINEAR).crop(((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H)).convert("RGBA")
    ang = 2.0 * math.sin(2 * math.pi * t / 2.7); dy = 12 * math.sin(2 * math.pi * t / 1.9)
    p = prod.rotate(ang, resample=Image.BICUBIC, expand=True, center=(pw, ph))
    frame.alpha_composite(p, (px - (p.width - pw) // 2, int(py + dy - (p.height - ph) // 2)))
    frame.alpha_composite(headline, ((W - headline.width) // 2, cfg.get("headline_y", 170)))
    for a, b, im in subs:
        if a <= t < b:
            frame.alpha_composite(im, ((W - im.width) // 2, cfg.get("sub_y", 1180)))
    arr = np.asarray(frame.convert("RGB"))
    # kekuatan glitch: awal, setiap tukar scene, hujung
    k = 0.0
    for c in [0.0] + cuts + [dur]:
        d = abs(t - c)
        if d < 0.3: k = max(k, 1 - d / 0.3)
    arr = glitch(arr, k, f)
    ff.stdin.write(np.ascontiguousarray(arr).tobytes())
ff.stdin.close(); ff.wait()
print("ok", cfg["output"], f"{dur:.1f}s")
