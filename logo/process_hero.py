"""
ヒーロー画像（墨絵）2案を Web 用に最適化して assets/ に保存する。

入力:
  - logo/Contemporary_Japanese_abstract_calligraphy_art_in_-1779342857122.png  (案A)
  - logo/Remove_background_from_Japanese_calligraphy_art_k-1779343013458.png   (案B)

出力:
  - assets/hero-a.jpg
  - assets/hero-b.jpg
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from PIL import Image
import os

LOGO_DIR = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview/logo"
ASSETS_DIR = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview/assets"

SRC_A = os.path.join(LOGO_DIR, "Contemporary_Japanese_abstract_calligraphy_art_in_-1779342857122.png")
SRC_B = os.path.join(LOGO_DIR, "Remove_background_from_Japanese_calligraphy_art_k-1779343013458.png")


def process(src_path, dst_path, edge_crop=0.04, max_width=2000, quality=88):
    """
    edge_crop: 上下左右をこの比率だけクロップ（壁の余白除去）
    max_width: この幅以下にリサイズ
    quality: JPEG品質（85〜92が無難）
    """
    img = Image.open(src_path).convert("RGB")
    w, h = img.size

    # エッジクロップ
    cx = int(w * edge_crop)
    cy = int(h * edge_crop)
    img = img.crop((cx, cy, w - cx, h - cy))

    # リサイズ（幅を max_width に合わせる）
    w2, h2 = img.size
    if w2 > max_width:
        new_h = int(h2 * max_width / w2)
        img = img.resize((max_width, new_h), Image.LANCZOS)

    img.save(dst_path, "JPEG", quality=quality, optimize=True)
    print(f"  ✓ {os.path.basename(dst_path)}  {img.size[0]}x{img.size[1]}  ({os.path.getsize(dst_path)/1024:.0f} KB)")


print("ヒーロー画像を最適化中…")
process(SRC_A, os.path.join(ASSETS_DIR, "hero-a.jpg"), edge_crop=0.05)  # 案A: 壁の余白多めなのでクロップやや強め
process(SRC_B, os.path.join(ASSETS_DIR, "hero-b.jpg"), edge_crop=0.02)  # 案B: 壁の余白少ないのでクロップ控えめ
print("完了。")
