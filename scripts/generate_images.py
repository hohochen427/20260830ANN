#!/usr/bin/env python3
"""依 scripts/image_prompts.json 產生 site/images/ 底下的圖片。

用法：
    cp .env.example .env      # 然後把金鑰填進 .env
    python3 scripts/generate_images.py            # 只補還沒有的圖
    python3 scripts/generate_images.py --force    # 全部重畫
    python3 scripts/generate_images.py --only hero-home,sl100-purifier
    python3 scripts/generate_images.py --dry-run  # 只印出會送出的提示詞，不呼叫 API

金鑰一律從環境變數讀，不寫在程式碼裡，也不進版控。
"""
import argparse, base64, json, os, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "images"
MANIFEST = ROOT / "scripts" / "image_prompts.json"


def load_env():
    """讀 .env（若存在），不覆蓋已存在的環境變數。"""
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def post_json(url, payload, headers, timeout=180):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"API 回應 {e.code}：{e.read().decode()[:500]}")
    except urllib.error.URLError as e:
        sys.exit(f"連線失敗：{e.reason}")


# ---------- 各供應商轉接 ----------
# 每個函式回傳 PNG/JPEG 的 bytes。

def gen_openai(prompt, key, model, size):
    model = model or "gpt-image-1"
    d = post_json("https://api.openai.com/v1/images/generations",
                  {"model": model, "prompt": prompt, "size": f"{size}x{size}", "n": 1},
                  {"Authorization": f"Bearer {key}"})
    return base64.b64decode(d["data"][0]["b64_json"])


def gen_google(prompt, key, model, size):
    model = model or "imagen-3.0-generate-002"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:predict?key={key}")
    d = post_json(url, {"instances": [{"prompt": prompt}],
                        "parameters": {"sampleCount": 1}}, {})
    return base64.b64decode(d["predictions"][0]["bytesBase64Encoded"])


def gen_stability(prompt, key, model, size):
    model = model or "sd3.5-large"
    d = post_json("https://api.stability.ai/v2beta/stable-image/generate/sd3",
                  {"prompt": prompt, "model": model, "output_format": "png"},
                  {"Authorization": f"Bearer {key}", "Accept": "application/json"})
    return base64.b64decode(d["image"])


def gen_replicate(prompt, key, model, size):
    if not model:
        sys.exit("replicate 需要在 IMAGE_MODEL 填完整的 owner/model:version")
    d = post_json("https://api.replicate.com/v1/predictions",
                  {"version": model.split(":")[-1], "input": {"prompt": prompt}},
                  {"Authorization": f"Bearer {key}", "Prefer": "wait"})
    out = d.get("output")
    url = out[0] if isinstance(out, list) else out
    if not url:
        sys.exit(f"replicate 未回傳圖片：{json.dumps(d)[:300]}")
    with urllib.request.urlopen(url, timeout=180) as r:
        return r.read()


PROVIDERS = {"openai": gen_openai, "google": gen_google,
             "stability": gen_stability, "replicate": gen_replicate}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="已存在的圖也重畫")
    ap.add_argument("--only", help="只畫這些 id，逗號分隔")
    ap.add_argument("--dry-run", action="store_true", help="只印提示詞，不呼叫 API")
    a = ap.parse_args()

    load_env()
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    style = m["style"]
    items = m["images"]
    if a.only:
        want = {s.strip() for s in a.only.split(",")}
        items = [i for i in items if i["id"] in want]
        missing = want - {i["id"] for i in items}
        if missing:
            sys.exit(f"找不到這些 id：{', '.join(sorted(missing))}")

    if not a.dry_run:
        provider = os.environ.get("IMAGE_PROVIDER", "").strip().lower()
        key = os.environ.get("IMAGE_API_KEY", "").strip()
        if not provider:
            sys.exit("IMAGE_PROVIDER 沒有設定。請複製 .env.example 為 .env 後填寫。")
        if provider not in PROVIDERS:
            sys.exit(f"不支援的 IMAGE_PROVIDER：{provider}。"
                     f"可用：{', '.join(PROVIDERS)}")
        if not key:
            sys.exit("IMAGE_API_KEY 沒有設定。請在 .env 填入你的金鑰。")
        model = os.environ.get("IMAGE_MODEL", "").strip()
        size = int(os.environ.get("IMAGE_SIZE", "1024"))
        fn = PROVIDERS[provider]

    OUT.mkdir(parents=True, exist_ok=True)
    made = skipped = 0
    for it in items:
        dest = OUT / f"{it['id']}.png"
        full = f"{it['prompt']}. {style}"
        if a.dry_run:
            print(f"\n--- {it['id']}  [{it['page']} / {it['section']}]")
            print(full)
            continue
        if dest.exists() and not a.force:
            print(f"跳過（已存在）  {dest.relative_to(ROOT)}")
            skipped += 1
            continue
        print(f"產生中  {it['id']} …", flush=True)
        dest.write_bytes(fn(full, key, model, size))
        print(f"  完成  {dest.relative_to(ROOT)}  "
              f"{dest.stat().st_size // 1024} KB")
        made += 1

    if not a.dry_run:
        print(f"\n新增 {made} 張，跳過 {skipped} 張。"
              f"重畫請加 --force。")


if __name__ == "__main__":
    main()
