"""
HITOMICHI ロゴ画像の最適化

入力:
  - 画像2（横並び）: Japanese_calligraphy_..._1779338920315.png
  - 画像3（縦書き）: Vertical_Japanese_calligraphy_..._1779338924220.png

出力 (assets/):
  - logo-horizontal.png       : 黒、ヘッダー用
  - logo-horizontal-white.png : 白、フッター用（暗背景）
  - logo-horizontal@2x.png    : 黒・Retina対応
  - logo-mark.png             : 黒、シンボル正方形
  - favicon-512.png / 192.png / 32.png / 16.png
  - apple-touch-icon.png      : iOS用 180x180
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from PIL import Image
import numpy as np
import os

LOGO_DIR = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview/logo"
HORIZONTAL = os.path.join(LOGO_DIR, "Japanese_calligraphy_logo_design_on_pure_white_bac-1779338920315.png")
VERTICAL = os.path.join(LOGO_DIR, "Vertical_Japanese_calligraphy_logo_design_on_pure_-1779338924220.png")
ASSETS_DIR = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview/assets"


def transparent_ink(img, color=(0, 0, 0)):
    """
    白背景の墨絵を「指定色＋アルファチャネル」に変換。
    輝度の逆を alpha とし、文字色は color に置換。
    （書道のかすれ・滲みのグラデーションが自然に半透明化される）
    """
    img = img.convert("RGBA")
    arr = np.array(img)
    gray = arr[:, :, :3].mean(axis=2)
    alpha = np.clip(255 - gray, 0, 255).astype(np.uint8)
    out = np.zeros_like(arr)
    out[:, :, 0] = color[0]
    out[:, :, 1] = color[1]
    out[:, :, 2] = color[2]
    out[:, :, 3] = alpha
    return Image.fromarray(out, "RGBA")


def auto_crop(img, threshold=8):
    """透明度しきい値で content bbox を自動クロップ"""
    arr = np.array(img)
    alpha = arr[:, :, 3]
    rows = np.any(alpha > threshold, axis=1)
    cols = np.any(alpha > threshold, axis=0)
    if not rows.any() or not cols.any():
        return img
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return img.crop((cmin, rmin, cmax + 1, rmax + 1))


def pad_to_square(img, pad_ratio=0.10):
    """正方形に整え、周囲に余白を追加"""
    w, h = img.size
    side = max(w, h)
    pad = int(side * pad_ratio)
    new_side = side + 2 * pad
    canvas = Image.new("RGBA", (new_side, new_side), (0, 0, 0, 0))
    canvas.paste(img, ((new_side - w) // 2, (new_side - h) // 2), img)
    return canvas


def save_resized(img, path, target_h=None, target_size=None):
    """高さ指定 or 正方形サイズ指定でリサイズ保存"""
    if target_size:
        out = img.resize((target_size, target_size), Image.LANCZOS)
    else:
        w, h = img.size
        target_w = int(w * target_h / h)
        out = img.resize((target_w, target_h), Image.LANCZOS)
    out.save(path, "PNG", optimize=True)
    return out.size


os.makedirs(ASSETS_DIR, exist_ok=True)

# ============================================================
# 横並び版（ヘッダー用）
# ============================================================
print("[1/2] 横並び版を処理中…")
img2 = Image.open(HORIZONTAL)
img2_black = auto_crop(transparent_ink(img2, color=(0, 0, 0)))
img2_white = auto_crop(transparent_ink(img2, color=(255, 255, 255)))

s1 = save_resized(img2_black, os.path.join(ASSETS_DIR, "logo-horizontal.png"), target_h=160)
print(f"  ✓ logo-horizontal.png        {s1[0]}x{s1[1]}")

s2 = save_resized(img2_black, os.path.join(ASSETS_DIR, "logo-horizontal@2x.png"), target_h=320)
print(f"  ✓ logo-horizontal@2x.png     {s2[0]}x{s2[1]}")

s3 = save_resized(img2_white, os.path.join(ASSETS_DIR, "logo-horizontal-white.png"), target_h=160)
print(f"  ✓ logo-horizontal-white.png  {s3[0]}x{s3[1]}")

s4 = save_resized(img2_white, os.path.join(ASSETS_DIR, "logo-horizontal-white@2x.png"), target_h=320)
print(f"  ✓ logo-horizontal-white@2x   {s4[0]}x{s4[1]}")


# ============================================================
# 縦書き版（シンボル・favicon用）
# ============================================================
print("\n[2/2] 縦書き版を処理中…")
img3 = Image.open(VERTICAL)
img3_black = auto_crop(transparent_ink(img3, color=(0, 0, 0)))
img3_square = pad_to_square(img3_black, pad_ratio=0.08)

# シンボルマーク（大、SNS等用）— HITOMICHIテキストを含む完全版
save_resized(img3_square, os.path.join(ASSETS_DIR, "logo-mark.png"), target_size=512)
print(f"  ✓ logo-mark.png              512x512")

# ------------------------------------------------------------
# Favicon専用ソース: HITOMICHIテキストを除外し「人道」のみ密集
# 16-32pxではHITOMICHIテキストは見えないので削って密度を最大化
# ------------------------------------------------------------
img3_full = Image.open(VERTICAL)
w_full, h_full = img3_full.size
# 右側のHITOMICHI縦書きテキストを除外（左60%でカット）
img3_kanji_raw = img3_full.crop((0, 0, int(w_full * 0.60), h_full))
# auto_crop の閾値を高めにして、薄いアーティファクトの余白も削る
img3_kanji_t = transparent_ink(img3_kanji_raw, color=(0, 0, 0))
img3_kanji = auto_crop(img3_kanji_t, threshold=40)
favicon_src = pad_to_square(img3_kanji, pad_ratio=0.03)  # ごく小さな余白

# Favicon各サイズ（人道のみ、密度高め）
for size, filename in [
    (512, "favicon-512.png"),
    (192, "favicon-192.png"),
    (180, "apple-touch-icon.png"),
    (32,  "favicon-32.png"),
    (16,  "favicon-16.png"),
]:
    save_resized(favicon_src, os.path.join(ASSETS_DIR, filename), target_size=size)
    print(f"  ✓ {filename:24s} {size}x{size}")


# ============================================================
# 既存の暫定 favicon.svg を削除（PNGに置き換え）
# ============================================================
old_svg = os.path.join(ASSETS_DIR, "favicon.svg")
if os.path.exists(old_svg):
    os.remove(old_svg)
    print(f"\n旧 favicon.svg を削除しました（PNG favicon に切り替え）")


print("\n完了。")
