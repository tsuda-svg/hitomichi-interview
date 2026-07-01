"""
パーサーとテンプレート単体テスト。Driveを使わずに動作確認する。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from publish_from_drive import parse_article
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

SAMPLE_ARTICLE = """---
slug: interview-02
title: 20代の離職を半減させた、対話型評価への転換。
volume: "No. 025"
date: 2026-06-01
themes:
  - エンゲージメント
  - 評価制度
industry: 製造業
size: 1000〜4999名

interviewee:
  name: 山田 健一
  name_en: Yamada Kenichi
  role: 人事戦略部長
  bio: 1975年生まれ。製造業の人事戦略を専門とし、5年で離職率を半減させた実績を持つ。

company:
  name: 千住メタルワークス株式会社
  tagline: 三代続く町工場の、現代化。
  logo_letter: S
  founded: 1962年
  employees: 1,200名（連結）
  industry: 製造業
  hq: 東京都
  description: |
    千住メタルワークスは、関東圏の中堅製造業として、精密金属加工で60年の歴史を持つ。三代目社長のもと、近年は人材育成と現場文化の現代化を経営の中心に据え、業界内で注目を集めている。
  website: https://example.com/

career:
  positions:
    - 人事マネージャー候補
    - 採用企画スペシャリスト
    - 人材開発担当
  persona: |
    現場と経営を行き来できる方。長期で組織と向き合える方を歓迎します。
  recruit_url: https://example.com/careers
  casual_url: https://meety.example.com/senju

quote: 査定から、対話へ。これは制度の話ではなく、組織の言語の話だった。

editor_note: |
  山田さんの言葉には、現場叩き上げの誇りと、人事の専門性への謙虚さが同居していた。
---

## リード

千住メタルワークスは、創業60年を超える金属加工メーカーである。社員1,200名、取引先600社。製造業の中では中堅規模だが、技術力では業界トップクラスの評価を受けている。

## Q. まず、人事戦略部長としての取り組みを教えてください。

私たちが直面していたのは、若手の離職率の高さでした。20代の離職率が業界平均の2倍。この5年で根本的な見直しを行いました。

## Q. 対話型評価への転換、最初は反発もありましたよね？

ありました。特に管理職から「査定はシンプルな方がいい」という声が強かった。でも、結果として残ったメンバーのエンゲージメントは飛躍的に上がりました。
"""

print("=== Step 1: パーサーテスト ===\n")
metadata, lead, qas = parse_article(SAMPLE_ARTICLE)

print(f"slug: {metadata['slug']}")
print(f"title: {metadata['title']}")
print(f"interviewee: {metadata['interviewee']['name']} ({metadata['interviewee']['role']})")
print(f"company: {metadata['company']['name']}")
print(f"themes: {metadata['themes']}")
print(f"lead: {lead[:80]}...")
print(f"qas: {len(qas)}個")
for i, qa in enumerate(qas, 1):
    print(f"  Q{i}: {qa['question']}")
    print(f"      ({len(qa['paragraphs'])}段落)")

print("\n=== Step 2: テンプレートレンダリングテスト ===\n")

ROOT = Path(__file__).parent.parent
TEMPLATES = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=False)
template = env.get_template("interview.html.j2")

images_used = {
    "hero": "assets/photos/articles/interview-02/hero.jpg",
    "profile": "assets/photos/articles/interview-02/profile.jpg",
}

related = [
    {"url": "interview-01.html", "image": "assets/photos/pickup-01.jpg",
     "themes": ["組織開発"], "industry": "製造業",
     "title": "経営と現場を往復する、人事の翻訳力。",
     "byline": "田中 良子 ｜ オリエンス・ホールディングス CHRO",
     "coming_soon": False},
]

description = f"{metadata['company']['name']} {metadata['interviewee']['role']} {metadata['interviewee']['name']}氏のインタビュー"

html = template.render(
    slug=metadata["slug"],
    title=metadata["title"],
    subtitle=metadata.get("subtitle", ""),
    description=description,
    volume=metadata.get("volume", ""),
    date=metadata.get("date", ""),
    themes=metadata.get("themes", []),
    industry=metadata.get("industry", ""),
    size=metadata.get("size", ""),
    interviewee=metadata["interviewee"],
    company=metadata["company"],
    career=metadata["career"],
    quote=metadata.get("quote", ""),
    editor_note=metadata.get("editor_note", ""),
    lead=lead,
    qas=qas,
    images=images_used,
    related=related,
)

out_path = ROOT / "_test_interview-02.html"
out_path.write_text(html, encoding="utf-8")
print(f"  ✓ レンダリング成功")
print(f"  ✓ ファイル出力: {out_path}")
print(f"  ✓ サイズ: {len(html)/1024:.1f} KB")
print(f"\nブラウザで開いて確認:")
print(f"  {out_path}")
