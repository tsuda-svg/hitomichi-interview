"""
interview-03.jpg（鈴木葵）のピンク背景を完全モノクロ化。
編集メディアのトーンに揃える。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image, ImageEnhance

ROOT = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview"
src = os.path.join(ROOT, "free-gazou", "pexels-rdne-7845392.jpg")
dst = os.path.join(ROOT, "assets", "photos", "interview-03.jpg")

img = Image.open(src).convert("RGB")

# リサイズ（max 1400px width）
w, h = img.size
if w > 1400:
    img = img.resize((1400, int(h * 1400 / w)), Image.LANCZOS)

# 完全モノクロ化（saturation 0%）
img = ImageEnhance.Color(img).enhance(0.0)

# わずかにコントラスト＋明るさ調整（編集メディア風）
img = ImageEnhance.Contrast(img).enhance(1.08)
img = ImageEnhance.Brightness(img).enhance(0.98)

img.save(dst, "JPEG", quality=85, optimize=True, progressive=True)
print(f"完了: {os.path.basename(dst)}  {img.size[0]}x{img.size[1]}  ({os.path.getsize(dst)/1024:.0f} KB)")
