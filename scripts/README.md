# 段落配圖

網站的圖片不進版控，由本目錄的腳本依提示詞產生。

## 第一次使用

```bash
cp .env.example .env      # 然後編輯 .env，填入 IMAGE_PROVIDER 與 IMAGE_API_KEY
python3 scripts/generate_images.py
```

`.env` 已被 `.gitignore` 排除，金鑰不會被 commit。

## 常用指令

| 指令 | 作用 |
|------|------|
| `python3 scripts/generate_images.py` | 只補還沒有的圖 |
| `python3 scripts/generate_images.py --force` | 全部重畫 |
| `python3 scripts/generate_images.py --only hero-home` | 只畫指定的一張 |
| `python3 scripts/generate_images.py --dry-run` | 只印提示詞，不呼叫 API，不需金鑰 |

## 供應商

預設是 OpenAI，`.env` 裡只需要填 `IMAGE_API_KEY`（ChatGPT 的 API key，`sk-` 開頭）。

模型預設 `gpt-image-1`。若帳號尚未完成組織驗證，呼叫時會拿到 403，
此時把 `IMAGE_MODEL` 改成 `dall-e-3` 即可。兩者的回應格式不同，腳本已分別處理。

也支援 `google`、`stability`、`replicate`，改 `IMAGE_PROVIDER` 即可。
`replicate` 一定要在 `IMAGE_MODEL` 填完整的 `owner/model:version`。

## 尺寸

`image_prompts.json` 每張圖的 `ratio` 決定送出的尺寸：

| ratio | gpt-image-1 | dall-e-3 |
|-------|-------------|----------|
| `1:1` | 1024x1024 | 1024x1024 |
| `4:3` / `16:9` | 1536x1024 | 1792x1024 |

版面用 `object-fit: cover` 裁切，不需要精準吻合。

## 改圖片內容

編輯 `scripts/image_prompts.json`。每一筆對應網站的一個段落：

- `id`：檔名，產生出來會是 `site/images/<id>.png`
- `page` / `section`：這張圖屬於哪一頁的哪一段，只是給人看的
- `alt`：無障礙替代文字，會寫進 HTML
- `prompt`：這一段的畫面描述
- `style`（頂層）：全站共用的視覺語彙，自動接在每個 prompt 後面

改完存檔，重跑腳本即可。
