"""Buat video produk 9:16: background + produk (cutout) bergoyang + caption pop-in."""
import math, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

import os, random
cfg = json.load(open(sys.argv[1]))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_DIR = os.path.join(REPO, "background")

def pick_background(cfg):
    """Kalau config tak set "background", pilih rawak dari folder background/."""
    if cfg.get("background"):
        return cfg["background"]
    files = sorted(f for f in os.listdir(BG_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    if not files:
        sys.exit("Folder background/ kosong. Letak sekurang-kurangnya satu gambar.")
    choice = random.Random(cfg.get("seed")).choice(files)
    print("background:", choice)
    return os.path.join(BG_DIR, choice)

def cover(im, w, h):
    """Besarkan & crop tengah supaya penuh 9:16 tanpa herot."""
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))
W, H, FPS = 1080, 1920, 30
dur = cfg["duration"]; N = int(dur * FPS)
FONT = cfg.get("font") or next((f for f in [
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Black.ttf"] if os.path.exists(f)), None)

bg0 = cover(Image.open(pick_background(cfg)).convert("RGB"), W, H)
prod = Image.open(cfg["product"]).convert("RGBA")
prod = prod.crop(prod.getbbox())
pw = int(W * cfg.get("product_scale", 1.0)); ph = int(prod.height * pw / prod.width)
prod = prod.resize((pw, ph), Image.LANCZOS)
# padankan cahaya sikit dengan background
rgb, a = prod.convert("RGB"), prod.getchannel("A")
rgb = ImageEnhance.Brightness(rgb).enhance(cfg.get("brightness", 1.0))
rgb = ImageEnhance.Color(rgb).enhance(cfg.get("saturation", 1.0))
prod = Image.merge("RGBA", (*rgb.split(), a))

emojis = {k: Image.open(v).convert("RGBA") for k, v in cfg.get("emoji", {}).items()}

def caption_img(text):
    """Teks putih outline hitam; token :nama: = emoji."""
    size = cfg.get("font_size", 88); font = ImageFont.truetype(FONT, size)
    lines = text.split("\n"); line_imgs = []
    for ln in lines:
        parts = []
        for tok in ln.split(" "):
            parts.append(("e", tok) if tok in emojis else ("t", tok))
        widths = []
        for kind, v in parts:
            widths.append(int(size * 1.05) if kind == "e" else int(font.getlength(v)))
        sp = int(size * 0.28); lw = sum(widths) + sp * (len(parts) - 1) + 24
        im = Image.new("RGBA", (lw, int(size * 1.35)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 12
        for (kind, v), w in zip(parts, widths):
            if kind == "t":
                d.text((x, 4), v, font=font, fill="white", stroke_width=9, stroke_fill="black")
            else:
                e = emojis[v].resize((int(size * 1.0), int(size * 1.0)), Image.LANCZOS)
                im.alpha_composite(e, (x, int(size * 0.12)))
            x += w + sp
        line_imgs.append(im)
    tw = max(i.width for i in line_imgs); th = sum(i.height for i in line_imgs)
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); y = 0
    for i in line_imgs:
        out.alpha_composite(i, ((tw - i.width) // 2, y)); y += i.height
    return out

caps = [(c["start"], c["end"], caption_img(c["text"])) for c in cfg["captions"]]
px, py = cfg.get("product_xy", [0, 300])

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "128k", cfg["output"]], stdin=subprocess.PIPE)

for f in range(N):
    t = f / FPS
    z = 1.0 + 0.06 * t / dur  # zoom perlahan background
    bw, bh = int(W * z), int(H * z)
    frame = bg0.resize((bw, bh), Image.BILINEAR).crop(((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H)).convert("RGBA")
    ang = 2.2 * math.sin(2 * math.pi * t / 2.6)           # goyang
    dy = 14 * math.sin(2 * math.pi * t / 1.9)             # naik turun
    p = prod.rotate(ang, resample=Image.BICUBIC, expand=True, center=(int(pw * 0.05), int(ph * 0.9)))
    frame.alpha_composite(p, (px - (p.width - pw) // 2, int(py + dy - (p.height - ph) // 2)))
    for s, e, ci in caps:
        if s <= t < e:
            k = min(1.0, (t - s) / 0.18); sc = 0.6 + 0.4 * (1 - (1 - k) ** 3) + 0.06 * math.sin(math.pi * k)
            c = ci.resize((max(1, int(ci.width * sc)), max(1, int(ci.height * sc))), Image.LANCZOS)
            frame.alpha_composite(c, ((W - c.width) // 2, cfg.get("caption_y", 330) - c.height // 2))
    ff.stdin.write(frame.convert("RGB").tobytes())
ff.stdin.close(); ff.wait(); print("ok", cfg["output"])
