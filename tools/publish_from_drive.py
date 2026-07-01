"""
publish_from_drive.py
=====================
Drive上の記事フォルダから記事を取り込んで、サイトに公開する。

使い方:
    python tools/publish_from_drive.py <記事フォルダ名>

例:
    python tools/publish_from_drive.py article-02-yamada

処理フロー:
  1. Drive「人道_記事キュー / 03_公開待ち」から指定フォルダを検索
  2. Google Docを取得→YAMLフロントマター＋Markdown本文をパース
  3. 画像をローカルにDL→最適化→assets/photos/articles/{slug}/に配置
  4. Jinja2テンプレからHTMLを生成→{slug}.html を出力
  5. index.html のカード一覧を更新
  6. Driveフォルダを _公開済み/年/月/ に移動
  7. 完了報告（公開URL）
"""
import sys, io, os, re, shutil, datetime, traceback
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ============================================================
# 設定
# ============================================================
ROOT = Path(__file__).parent.parent
CREDENTIALS = ROOT.parent.parent.parent / "credentials.json"  # pmi-ai/credentials.json

QUEUE_FOLDER_ID    = "1UZ2X_GJKTurlLWAETHMZS6AZgXiq8jOr"
WAITING_FOLDER_ID  = "1-AweCPbsNP4XgPteb66aiiWEiX-w0lX3"  # 03_公開待ち
PUBLISHED_FOLDER_ID = "1zNPdx-iWqK4GFeKO8INWpFvfgltBsd5_"  # _公開済み

ASSETS_DIR = ROOT / "assets" / "photos" / "articles"
TEMPLATES_DIR = Path(__file__).parent / "templates"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


# ============================================================
# Google API クライアント
# ============================================================
def get_clients():
    creds = Credentials.from_service_account_file(str(CREDENTIALS), scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds)
    docs  = build("docs",  "v1", credentials=creds)
    return drive, docs


# ============================================================
# Driveからフォルダ＆ファイル取得
# ============================================================
def find_folder_in_parent(drive, name, parent_id):
    res = drive.files().list(
        q=f"name='{name}' and '{parent_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)",
    ).execute()
    files = res.get("files", [])
    if not files:
        return None
    return files[0]


def list_files_in_folder(drive, folder_id):
    res = drive.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, modifiedTime)",
        orderBy="name",
    ).execute()
    return res.get("files", [])


def download_doc_as_text(docs, doc_id):
    """Google Doc をプレーンテキストとして取得"""
    doc = docs.documents().get(documentId=doc_id).execute()
    text = ""
    for elem in doc.get("body", {}).get("content", []):
        para = elem.get("paragraph")
        if not para:
            continue
        for r in para.get("elements", []):
            t = r.get("textRun", {}).get("content", "")
            text += t
    return text


def download_file(drive, file_id, dest_path):
    """Drive上のバイナリファイルをローカルにダウンロード"""
    request = drive.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def move_drive_file(drive, file_id, new_parent_id, current_parent_id):
    """Driveのフォルダを別フォルダに移動"""
    drive.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=current_parent_id,
        fields="id, parents",
    ).execute()


def ensure_subfolder(drive, parent_id, name):
    """親フォルダ配下に指定名のサブフォルダが無ければ作る"""
    existing = find_folder_in_parent(drive, name, parent_id)
    if existing:
        return existing["id"]
    res = drive.files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id",
    ).execute()
    return res["id"]


# ============================================================
# Markdown + YAML パーサー
# ============================================================
def parse_article(text):
    """
    YAMLフロントマター + Markdown本文 をパースする。
    Returns: (metadata: dict, body_sections: list of dict)
    """
    # YAML frontmatter 抽出
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("YAMLフロントマターが見つかりません。記事の先頭が '---' で始まっていることを確認してください。")

    yaml_str = m.group(1)
    body_str = m.group(2)

    metadata = yaml.safe_load(yaml_str)
    if not metadata:
        raise ValueError("YAMLフロントマターが空です。")

    # Markdown 本文を section に分割
    sections = []
    current_heading = None
    current_paragraphs = []

    for line in body_str.split("\n"):
        line = line.rstrip()
        if line.startswith("## "):
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "paragraphs": current_paragraphs,
                })
            current_heading = line[3:].strip()
            current_paragraphs = []
        elif line.strip():
            if current_heading is not None:
                current_paragraphs.append(line.strip())

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "paragraphs": current_paragraphs,
        })

    # 構造化
    lead = ""
    qas = []
    for sec in sections:
        head = sec["heading"]
        paras = sec["paragraphs"]
        if head == "リード":
            lead = " ".join(paras)
        elif head.startswith("Q.") or head.startswith("Q "):
            qas.append({
                "question": head,
                "paragraphs": paras,
            })

    return metadata, lead, qas


# ============================================================
# 画像処理
# ============================================================
def optimize_image(src_path, dst_path, max_width=1400, quality=85):
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    if w > max_width:
        new_h = int(h * max_width / w)
        img = img.resize((max_width, new_h), Image.LANCZOS)
    img.save(dst_path, "JPEG", quality=quality, optimize=True, progressive=True)
    return img.size, os.path.getsize(dst_path)


# ============================================================
# Related Articles 自動選定
# ============================================================
def pick_related_articles(slug, metadata, all_articles):
    """同業種/同テーマの他記事から3件選ぶ。データ少ない時はサンプル使用"""
    # MVP: ハードコードの related（既存サイトのカード相当）
    return [
        {
            "url": "interview-01.html",
            "image": "assets/photos/pickup-01.jpg",
            "themes": ["組織開発", "評価制度"],
            "industry": "製造業",
            "title": "経営と現場を往復する、人事の翻訳力。",
            "byline": "田中 良子 ｜ オリエンス・ホールディングス CHRO",
            "coming_soon": False,
        },
        {
            "url": "#",
            "image": "assets/photos/interview-04.jpg",
            "themes": ["HRBP"],
            "industry": "コンサル・士業",
            "title": "HRBPは\"翻訳者\"であり、\"設計者\"でもある。",
            "byline": "高橋 翔 ｜ Verbena Consulting HRBP",
            "coming_soon": True,
        },
        {
            "url": "#",
            "image": "assets/photos/interview-05.jpg",
            "themes": ["採用"],
            "industry": "金融・保険",
            "title": "新卒一括採用の、終わり方。",
            "byline": "中村 律子 ｜ 北辰トラスト銀行 採用責任者",
            "coming_soon": True,
        },
    ]


# ============================================================
# index.html のカード更新
# ============================================================
def update_index_card(slug, metadata, byline_role, byline_company):
    """
    index.html のインタビュー一覧で、当該slug のカードを更新する。
    タイトル・社名・名前・サムネ画像・タグを差し替え、coming-soonバッジを除去。

    現状の実装方針：
      - slug が interview-02〜06 ならその位置のカードを更新
      - それ以外は新規追加（将来実装、今は警告のみ）
    """
    index_path = ROOT / "index.html"
    if not index_path.exists():
        print(f"  ⚠ index.html が見つかりません（更新スキップ）")
        return

    # 簡易マッピング: slug → どのカード位置か
    # MVP: 名前と社名のテキスト置換のみ（既存カードの構造を活かす）
    content = index_path.read_text(encoding="utf-8")

    # まずは「該当slugにあわせて assets/photos/{slug}.jpg を assets/photos/articles/{slug}/card.jpg に変更」
    # ※将来実装。今はサムネは既存のまま、テキストだけ書き換える形にする。

    # 警告のみで実装は次フェーズ
    print(f"  ℹ index.htmlカード更新は次フェーズで実装します（slug={slug}）")
    print(f"    手動で更新する場合: 「{slug}」のカード位置のタイトル・社名・名前を変更してください")


# ============================================================
# メイン処理
# ============================================================
def publish(folder_name):
    drive, docs = get_clients()

    # === Step 1: 03_公開待ち フォルダから対象案件を検索 ===
    print(f"[1/6] フォルダを検索中: {folder_name}")
    folder = find_folder_in_parent(drive, folder_name, WAITING_FOLDER_ID)
    if not folder:
        raise FileNotFoundError(f"03_公開待ち フォルダ内に「{folder_name}」が見つかりません")
    folder_id = folder["id"]
    print(f"  ✓ 発見: {folder['name']} ({folder_id})")

    # === Step 2: 中身を取得 ===
    print(f"\n[2/6] フォルダ内容を取得中...")
    files = list_files_in_folder(drive, folder_id)
    if not files:
        raise FileNotFoundError(f"フォルダ「{folder_name}」が空です")

    doc_file = None
    image_files = []
    for f in files:
        mime = f["mimeType"]
        if mime == "application/vnd.google-apps.document":
            doc_file = f
        elif mime.startswith("image/"):
            image_files.append(f)

    if not doc_file:
        raise FileNotFoundError("原稿（Google Doc）が見つかりません。フォルダ内にGoogle Docを配置してください。")

    print(f"  ✓ 原稿Doc: {doc_file['name']}")
    print(f"  ✓ 画像: {len(image_files)}枚 - {', '.join(f['name'] for f in image_files)}")

    # === Step 3: Doc をテキスト取得＆パース ===
    print(f"\n[3/6] 原稿をパース中...")
    text = download_doc_as_text(docs, doc_file["id"])
    metadata, lead, qas = parse_article(text)
    slug = metadata["slug"]
    print(f"  ✓ slug: {slug}")
    print(f"  ✓ title: {metadata['title']}")
    print(f"  ✓ Q&A: {len(qas)}個")

    # === Step 4: 画像をローカルDL＆最適化 ===
    print(f"\n[4/6] 画像処理中...")
    article_assets_dir = ASSETS_DIR / slug
    article_assets_dir.mkdir(parents=True, exist_ok=True)

    images_used = {}
    temp_dir = ROOT / "tools" / "_tmp"
    temp_dir.mkdir(exist_ok=True)

    # ファイル名から用途を識別（規約名 OR fallback で順番に hero / profile に割当）
    classified = []
    unclassified = []
    for f in image_files:
        name_lower = f["name"].lower()
        if name_lower.startswith("hero"):
            classified.append(("hero", f))
        elif name_lower.startswith("profile"):
            classified.append(("profile", f))
        elif name_lower.startswith("body"):
            classified.append((name_lower.split(".")[0], f))
        elif name_lower.startswith("card"):
            classified.append(("card", f))
        elif name_lower.startswith("logo"):
            classified.append(("logo", f))
        else:
            unclassified.append(f)

    # 規約名で見つからなかった hero / profile を unclassified から補完
    have = {kind for kind, _ in classified}
    if "hero" not in have and unclassified:
        classified.append(("hero", unclassified.pop(0)))
        print(f"  ℹ hero.jpg が無いので {classified[-1][1]['name']} を hero に自動割当")
    if "profile" not in have and unclassified:
        classified.append(("profile", unclassified.pop(0)))
        print(f"  ℹ profile.jpg が無いので {classified[-1][1]['name']} を profile に自動割当")

    if unclassified:
        for f in unclassified:
            print(f"  ⚠ 用途不明な画像をスキップ: {f['name']}（hero/profile/body-XX/card/logo で始まる名前にしてください）")

    for kind, f in classified:
        # 一時保存→最適化→assets/photos/articles/{slug}/{kind}.jpg
        ext = os.path.splitext(f["name"])[1].lower()
        tmp_path = temp_dir / f"{slug}_{kind}{ext}"
        download_file(drive, f["id"], tmp_path)

        dst_path = article_assets_dir / f"{kind}.jpg"
        size, fs = optimize_image(tmp_path, dst_path)
        images_used[kind] = f"assets/photos/articles/{slug}/{kind}.jpg"
        print(f"  ✓ {kind}.jpg  {size[0]}x{size[1]}  ({fs/1024:.0f} KB)  ← {f['name']}")

        tmp_path.unlink()

    # 必須画像チェック
    if "hero" not in images_used:
        raise FileNotFoundError("ヒーロー画像が必要です。フォルダ内に画像を1枚以上アップロードしてください")
    if "profile" not in images_used:
        # heroで代替
        images_used["profile"] = images_used["hero"]
        print(f"  ℹ profile.jpg 相当が無いため hero を流用")

    # === Step 5: HTML 生成 ===
    print(f"\n[5/6] HTML生成中...")
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    template = env.get_template("interview.html.j2")

    # related articles を選定
    related = pick_related_articles(slug, metadata, [])

    # description（OGP用）
    description = f"{metadata['company']['name']} {metadata['interviewee']['role']} {metadata['interviewee']['name']}氏が、{metadata['themes'][0]}について語る。"

    rendered = template.render(
        slug=slug,
        title=metadata["title"],
        subtitle=metadata.get("subtitle", ""),
        description=description,
        volume=metadata.get("volume", ""),
        date=metadata.get("date", ""),
        themes=metadata.get("themes", []),
        industry=metadata.get("industry", ""),
        size=metadata.get("size", ""),
        read_minutes=metadata.get("read_minutes", 8),
        interviewer=metadata.get("interviewer", "編集部"),
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

    html_path = ROOT / f"{slug}.html"
    html_path.write_text(rendered, encoding="utf-8")
    print(f"  ✓ {slug}.html ({len(rendered)/1024:.0f} KB)")

    # === Step 6: index.html 更新（暫定） ===
    print(f"\n[6/6] index.html を更新中...")
    update_index_card(slug, metadata, metadata["interviewee"]["role"], metadata["company"]["name"])

    # === 後処理：Driveフォルダを _公開済み に移動 ===
    today = datetime.date.today()
    year_folder_id = ensure_subfolder(drive, PUBLISHED_FOLDER_ID, str(today.year))
    month_folder_id = ensure_subfolder(drive, year_folder_id, f"{today.month:02d}")
    move_drive_file(drive, folder_id, month_folder_id, WAITING_FOLDER_ID)
    print(f"  ✓ Driveフォルダを _公開済み/{today.year}/{today.month:02d}/ に移動")

    # === 完了報告 ===
    print(f"\n{'='*50}")
    print(f"✅ 公開準備完了")
    print(f"{'='*50}")
    print(f"  本番URL（pushすると反映）:")
    print(f"  https://hitomichi-interview.vercel.app/{slug}.html")
    print(f"")
    print(f"  次にやること:")
    print(f"  1. ローカルプレビューで確認: open {html_path}")
    print(f"  2. OKなら: git add . && git commit && git push")


# ============================================================
# CLI エントリポイント
# ============================================================
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2:
        print("使い方: python tools/publish_from_drive.py <記事フォルダ名>")
        print("例:    python tools/publish_from_drive.py article-02-yamada")
        sys.exit(1)

    folder_name = sys.argv[1]

    try:
        publish(folder_name)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        traceback.print_exc()
        sys.exit(1)
