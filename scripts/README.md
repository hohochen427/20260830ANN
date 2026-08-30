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

## 支援的供應商

在 `.env` 的 `IMAGE_PROVIDER` 填 `openai`、`google`、`stability` 或 `replicate`。
`IMAGE_MODEL` 留空會用各家預設值；`replicate` 一定要填完整的 `owner/model:version`。

## 改圖片內容

編輯 `scripts/image_prompts.json`。每一筆對應網站的一個段落：

- `id`：檔名，產生出來會是 `site/images/<id>.png`
- `page` / `section`：這張圖屬於哪一頁的哪一段，只是給人看的
- `alt`：無障礙替代文字，會寫進 HTML
- `prompt`：這一段的畫面描述
- `style`（頂層）：全站共用的視覺語彙，自動接在每個 prompt 後面

改完存檔，重跑腳本即可。
