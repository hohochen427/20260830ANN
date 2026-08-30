---
source: source/brand-notes.md
---

# Design Brief — 星光家電客服知識中心

## 對象與語氣

面向一般消費者，語氣像鄰居，不要像業務；可以親切，不要裝熟；不要驚嘆號連發。

**不可使用**：保證、一定、最便宜、市場第一（法務要求，見 content/policy.md）
**可以使用**：實測、適用坪數、建議更換週期

## 品牌色

| Token | 值 | 用途 |
|---|---|---|
| `--color-primary` | `#E8752A`（暖橘） | 主色、按鈕、連結、強調 |
| `--color-bg` | `#FAF7F2`（米白，非純白） | 頁面底色 |
| `--color-ink` | `#2A2320` | 主要文字 |
| `--color-muted` | `#6B6259` | 次要文字 |
| `--color-border` | `#E6DED4` | 分隔線、卡片邊框 |
| `--color-surface` | `#FFFFFF` | 卡片底色 |

## 字體

中文使用思源黑體（Noto Sans TC）一類的黑體，**不使用襯線字**。

```
font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", -apple-system, sans-serif;
```

## 裝置優先序

行動裝置優先（多數客服查詢來自手機），版面採單欄可堆疊設計，最大內容寬度 960px 置中。

## 網站上必須要有

- 客服信箱（`service@starlight-demo.example`）
- 適用坪數（產品相關頁面）
- 保固說明

## 網站上不可以有

- 星等評分（沒有真實評分資料）
- 來路不明的媒體報導引用
