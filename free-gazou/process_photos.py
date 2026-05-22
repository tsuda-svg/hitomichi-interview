"""
HITOMICHI 人道 サイトのインタビュー記事用画像を最適化する。

入力: free-gazou/ 配下のオリジナル画像（ぱくたそ / Pexels）
出力: assets/photos/ 配下に Web 用 JPEG（max width 1400px, quality 85, progressive）

マッピング:
  pickup-01.jpg   = 田中良子 (Pick up 01 / Interview 1 共用)
  pickup-02.jpg   = 山田健一
  dialogue-01.jpg = 木村×藤本 対談
  dialogue-02.jpg = 佐藤美和×三浦直人 対談
  interview-02.jpg = 林田真由美
  interview-03.jpg = 鈴木葵
  interview-04.jpg = 高橋翔
  interview-05.jpg = 中村律子
  interview-06.jpg = 林拓也
  column-01.jpg   = ジョブ型 コラム
  column-02.jpg   = エンゲージメントサーベイ
  column-03.jpg   = 次世代リーダー育成
  column-04.jpg   = 人的資本開示
  service-conference.jpg = HITOMICHI Conference
  service-awards.jpg     = HITOMICHI Awards
  service-salon.jpg      = HR Practitioners' Salon
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image

SOURCE_DIR = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview/free-gazou"
DEST_DIR   = "c:/Users/aidma-1094/OneDrive/pmi-ai/pmi-solutions/kaimaku/hitomichi-interview/assets/photos"

MAPPING = [
    # (source, dest, role)
    ("pexels-felicity-tai-7964535.jpg",                "pickup-01.jpg",           "Pick up 01 / Interview 1 - 田中良子"),
    ("nozakisan_IMG_0090_TP_V.jpg",                    "pickup-02.jpg",           "Pick up 02 - 山田健一"),
    ("pexels-mikhail-nilov-7988693.jpg",               "dialogue-01.jpg",         "対談1 - 木村拓海×藤本涼"),
    ("pexels-rdne-7845457.jpg",                        "dialogue-02.jpg",         "対談2 - 佐藤美和×三浦直人"),
    ("pexels-ketut-subiyanto-4623529.jpg",             "interview-02.jpg",        "Interview 2 - 林田真由美"),
    ("pexels-rdne-7845392.jpg",                        "interview-03.jpg",        "Interview 3 - 鈴木葵"),
    ("azumaIMG_3017_TP_V.jpg",                         "interview-04.jpg",        "Interview 4 - 高橋翔"),
    ("SAKIHFKE7638_TP_V.jpg",                          "interview-05.jpg",        "Interview 5 - 中村律子"),
    ("PKU4141318PAR58209_TP_V.jpg",                    "interview-06.jpg",        "Interview 6 - 林拓也"),
    ("pexels-pixabay-260973.jpg",                      "column-01.jpg",           "コラム1 - ジョブ型"),
    ("syu-PAUI4925-b_TP_V.jpg",                        "column-02.jpg",           "コラム2 - サーベイ"),
    ("tkIMG_8743_TP_V.jpg",                            "column-03.jpg",           "コラム3 - 後継者育成"),
    ("reai_2567D018_TP_V.jpg",                         "column-04.jpg",           "コラム4 - 人的資本"),
    ("pexels-asia-culture-center-3116378-4940642.jpg", "service-conference.jpg",  "Conference"),
    ("pexels-werner-pfennig-6949886.jpg",              "service-awards.jpg",      "Awards"),
    ("pexels-doan-thanh-binh-2147604563-36834057.jpg", "service-salon.jpg",       "Salon"),
]

def process(src, dst, max_width=1400, quality=85):
    img = Image.open(src).convert("RGB")
    w, h = img.size
    if w > max_width:
        new_h = int(h * max_width / w)
        img = img.resize((max_width, new_h), Image.LANCZOS)
    img.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    return img.size, os.path.getsize(dst)


os.makedirs(DEST_DIR, exist_ok=True)
print(f"画像処理開始（{len(MAPPING)}枚）...\n")

total_orig = 0
total_new  = 0
for src_name, dst_name, role in MAPPING:
    src = os.path.join(SOURCE_DIR, src_name)
    dst = os.path.join(DEST_DIR, dst_name)
    orig_size = os.path.getsize(src)
    (w, h), new_size = process(src, dst)
    total_orig += orig_size
    total_new  += new_size
    saved_pct = (1 - new_size / orig_size) * 100
    print(f"  ✓ {dst_name:24s} {w:4d}x{h:4d}  {new_size/1024:5.0f} KB  (元: {orig_size/1024:5.0f} KB, -{saved_pct:.0f}%)  {role}")

print(f"\n完了。合計サイズ: {total_orig/1024/1024:.1f} MB → {total_new/1024/1024:.1f} MB  (-{(1-total_new/total_orig)*100:.0f}%)")
