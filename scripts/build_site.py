#!/usr/bin/env python3
"""依 site.config.json 與 content/ 產生 site/ 底下的 HTML。

    python3 scripts/build_site.py            # 產生到 site/
    python3 scripts/build_site.py --out build   # 產生到別的目錄，供比對
    python3 scripts/build_site.py --check    # 只比對，不寫檔；有差異回傳 1

設計原則：頁面結構、文案、圖片版位一律來自設定檔與 content/，
本程式只負責組裝，不內含任何網站文字。
"""
import argparse, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
CONFIG = ROOT / "site.config.json"
IMAGES = ROOT / "scripts" / "image_prompts.json"


# ---------- 來源解析 ----------

def parse_markdown(path):
    """把 .md 拆成 [(標題, [區塊])]，標題為 None 代表前言。
    區塊型別：('p', 文字) 或 ('ul', [項目])"""
    lines = (CONTENT / path).read_text(encoding="utf-8").split("\n")
    sections, title, buf = [], None, []

    def flush():
        if title is not None or buf:
            sections.append((title, to_blocks(buf)))

    for ln in lines:
        m = re.match(r"^(#{2,3})\s+(.*)$", ln)
        if m:
            flush()
            title, buf = m.group(2).strip(), []
        elif ln.strip() == "---":
            flush()
            title, buf = None, []
        elif not ln.startswith("# "):
            buf.append(ln)
    flush()
    return [(t, b) for t, b in sections if t is not None or b]


def to_blocks(lines):
    blocks, para, items = [], [], []

    def flush_para():
        if para:
            blocks.append(("p", " ".join(x.strip() for x in para).strip()))
            para.clear()

    def flush_items():
        if items:
            blocks.append(("ul", list(items)))
            items.clear()

    for ln in lines:
        s = ln.strip()
        if not s:
            flush_para(); flush_items()
        elif s.startswith("- "):
            flush_para(); items.append(s[2:].strip())
        else:
            flush_items(); para.append(s)
    flush_para(); flush_items()
    return blocks


def is_internal(text, cfg):
    return any(m in text for m in cfg["internalMarkers"])


def is_pending(text):
    return text.lstrip().startswith("**未定案。**") or text.lstrip().startswith("未定案")


# ---------- 行內轉換 ----------

def inline(text, cfg):
    """跳脫後，把信箱轉成 mailto、去掉 markdown 強調與反引號。"""
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
    mail = re.escape(cfg["site"]["email"])
    t = re.sub(mail, f'<a href="mailto:{cfg["site"]["email"]}">{cfg["site"]["email"]}</a>', t)
    return t


# ---------- 圖片 ----------

def load_images():
    d = json.loads(IMAGES.read_text(encoding="utf-8"))
    out = {}
    for i in d["images"]:
        out.setdefault(i["page"], {})[i["slot"]] = i
    return out


def figure(item, cfg, extra=""):
    if not item:
        return ""
    c = f" {extra}" if extra else ""
    src = f'{cfg["site"]["imageDir"]}/{item["id"]}.png'
    return (f'<figure class="figure{c}">'
            f'<img src="{src}" alt="{html.escape(item["alt"])}" loading="lazy" '
            f'onerror="this.closest(\'.figure\').hidden=true">'
            f'</figure>')


# ---------- 區塊渲染 ----------

def render_blocks(blocks, cfg, indent="  "):
    out = []
    for kind, val in blocks:
        if kind == "p":
            if not val or is_internal(val, cfg):
                continue
            if is_pending(val):
                out.append(f'{indent}<p class="pending">{cfg["text"]["pendingBlock"]}</p>')
            else:
                out.append(f"{indent}<p>{inline(val, cfg)}</p>")
        else:
            keep = [i for i in val if not is_internal(i, cfg)]
            if not keep:
                continue
            lis = "".join(f"\n{indent}  <li>{inline(i, cfg)}</li>" for i in keep)
            out.append(f"{indent}<ul>{lis}\n{indent}</ul>")
    return out


def render_section(source, name, cfg, imgs, page):
    for title, blocks in parse_markdown(source):
        if title != name:
            continue
        out = [f"  <h2>{html.escape(title)}</h2>"]
        fig = figure(imgs.get(page, {}).get(f"section:{title}"), cfg)
        if fig:
            out.append(f"  {fig}")
        out += render_blocks(blocks, cfg)
        return out
    sys.exit(f"設定檔要求的段落在 {source} 找不到：{name}")


def parse_fields(items):
    d = {}
    for i in items:
        if "：" in i:
            k, v = i.split("：", 1)
            d[k.strip()] = v.strip()
    return d


def clean_field(v, cfg):
    """未定案（…）→ 依決策改為對外用語。"""
    return cfg["text"]["pendingField"] if v.startswith("未定案") else v


def render_products(block, cfg, imgs, page):
    out = ['  <div class="product-grid">']
    for title, blocks in parse_markdown(block["source"]):
        if title is None or title in cfg["excludeSections"]:
            continue
        items = next((v for k, v in blocks if k == "ul"), None)
        if not items:
            continue
        f = parse_fields(items)
        out.append("")
        out.append('  <div class="product">')
        fig = figure(imgs.get(page, {}).get(f"product:{title}"), cfg)
        if fig:
            out.append(f"    {fig}")
        out.append(f"    <h3>{html.escape(title)}</h3>")
        price = f.get(block["priceField"])
        if price:
            out.append(f'    <p class="price">{html.escape(price)}</p>')
        lis = "".join(f"\n      <li>{html.escape(k)}：{html.escape(clean_field(f[k], cfg))}</li>"
                      for k in block["fields"] if k in f)
        out.append(f"    <ul>{lis}\n    </ul>")
        out.append("  </div>")
    out.append("  </div>")
    return out


def render_faq(block, cfg):
    out = []
    for title, blocks in parse_markdown(block["source"]):
        if title is None:
            continue
        body = render_blocks(blocks, cfg, indent="")
        if not body:
            continue
        inner = "".join(body)
        out.append('  <details class="faq-item">')
        out.append(f"    <summary>{html.escape(title)}</summary>")
        out.append(f'    <div class="faq-body">{inner}</div>')
        out.append("  </details>")
    return out


# ---------- 頁面組裝 ----------

def build_page(page, cfg, imgs):
    s, key = cfg["site"], page["key"]
    body = []
    pimgs = imgs.get(key, {})

    if page.get("layout") == "home":
        fig = figure(pimgs.get("hero"), cfg)
        if fig:
            body.append(f"  {fig}")
        body.append(f'  <h1>{html.escape(cfg["campaign"]["heading"])}</h1>')
    else:
        body.append(f'  <h1>{html.escape(page["h1"])}</h1>')
        fig = figure(pimgs.get("pagetop"), cfg)
        if fig:
            body.append(f"  {fig}")

    tag = page.get("taglineText")
    if tag and tag.startswith("@text."):
        tag = cfg["text"][tag.split(".", 1)[1]]
    elif page.get("taglineFrom"):
        src = page["taglineFrom"]
        blocks = parse_markdown(src["source"])[0][1] if parse_markdown(src["source"]) else []
        paras = [v for k, v in blocks if k == "p"]
        n = src["paragraph"]
        tag = paras[n] if len(paras) > n else None
    if tag:
        body.append(f'  <p class="tagline">{inline(tag, cfg)}</p>')
    body.append("")

    for b in page["blocks"]:
        t = b["type"]
        if t == "campaignFeature":
            c = cfg["campaign"]
            fields = None
            for title, blocks in parse_markdown("products.md"):
                if title == c["featureProduct"]:
                    fields = parse_fields(next(v for k, v in blocks if k == "ul"))
            if fields is None:
                sys.exit(f'campaign.featureProduct 在 products.md 找不到：{c["featureProduct"]}')
            body.append('  <div class="feature">')
            fig = figure(pimgs.get("feature"), cfg)
            if fig:
                body.append(f"    {fig}")
            body.append(f'    <h2>{html.escape(c["featureProduct"])}</h2>')
            lis = "".join(f"\n      <li>{html.escape(k)}：{html.escape(clean_field(fields[k], cfg))}</li>"
                          for k in c["featureFields"] if k in fields)
            body.append(f"    <ul>{lis}\n    </ul>")
            target = next(p for p in cfg["pages"] if p["key"] == c["ctaTarget"])
            body.append(f'    <p><a class="cta" href="{target["file"]}">'
                        f'{html.escape(c["ctaLabel"])}</a></p>')
            body.append("  </div>")
        elif t == "section":
            body += render_section(b["source"], b["section"], cfg, imgs, key)
        elif t == "allSections":
            for title, blocks in parse_markdown(b["source"]):
                # title 為 None 代表檔案前言，不輸出到頁面
                if title is None or title in cfg["excludeSections"]:
                    continue
                rendered = render_blocks(blocks, cfg)
                if not rendered:
                    continue
                body.append(f"  <h2>{html.escape(title)}</h2>")
                body += rendered
                body.append("")
        elif t == "productGrid":
            body += render_products(b, cfg, imgs, key)
        elif t == "faqList":
            body += render_faq(b, cfg)
        else:
            sys.exit(f"未知的區塊型別：{t}")
        body.append("")

    nav = "".join(
        f'\n      <a href="{next(p for p in cfg["pages"] if p["key"] == n["key"])["file"]}">'
        f'{html.escape(n["label"])}</a>' for n in cfg["nav"])
    home = next(p for p in cfg["pages"] if p["key"] == "index")["file"]
    title = page["title"] if key == "index" else f'{page["title"]}｜{s["titleSuffix"]}'
    mail = f'<a href="mailto:{s["email"]}">{s["email"]}</a>'

    return f"""<!DOCTYPE html>
<html lang="{s['lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{s['stylesheet']}">
</head>
<body>

<header>
  <div class="wrap">
    <a class="brand" href="{home}">{html.escape(s['brand'])}</a>
    <nav>{nav}
    </nav>
  </div>
</header>

<main class="wrap">
{chr(10).join(body).rstrip()}
</main>

<footer>
  <div class="wrap">
    {s['footerLabel'] if 'footerLabel' in s else cfg['text']['footerLabel']}：{mail}
  </div>
</footer>

</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    ap.add_argument("--check", action="store_true", help="只比對現有 site/，不寫檔")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    imgs = load_images()
    out = ROOT / a.out
    diffs = 0

    for page in cfg["pages"]:
        text = build_page(page, cfg, imgs)
        dest = out / page["file"]
        if a.check:
            cur = ROOT / "site" / page["file"]
            same = cur.exists() and cur.read_text(encoding="utf-8") == text
            print(f'{"一致" if same else "有差異"}  {page["file"]}')
            diffs += 0 if same else 1
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            try:
                shown = dest.relative_to(ROOT)
            except ValueError:
                shown = dest
            print(f"產生  {shown}")

    if a.check:
        print(f"\n{diffs} 頁有差異。")
        sys.exit(1 if diffs else 0)
    print(f"\n完成 {len(cfg['pages'])} 頁。")


if __name__ == "__main__":
    main()
