# Game Trend Radar — YouTube 獨立後端

從主後端拆出的 YouTube 收集器，具備自己的 Python 依賴、測試、GitHub Actions 與 Secrets。只發布前端 `data/youtube_live.json`。

## 執行狀態

**收集目前維持手動，不含 cron、push 或 workflow_run 收集觸發器。** 設定 Secrets 不會自動開始收集；請到 Actions → Collect YouTube live data → Run workflow 執行。獨立的 Test standalone collector 只跑離線測試，不會查 API、不會發布資料。

## 之後需設定的 Secrets

位置：Settings → Secrets and variables → Actions → Repository secrets。

| Secret | 用途 |
|---|---|
| `YOUTUBE_API_KEY` | YouTube Data API v3 金鑰 |
| `FRONTEND_REPO_TOKEN` | 將本平台 JSON 寫入 `danielet087/game-trend-radar`；fine-grained token 僅選該前端 Repo，Contents: Read and write |

本專案不附帶或移轉任何 Secret 值。內建 `GITHUB_TOKEN` 不能取代跨 Repo 的 `FRONTEND_REPO_TOKEN`。缺少平台憑證時會明確跳過；缺少發布 Token 時只保存 2 天的 JSON artifact，前端不改動。

## 本機使用

需 Python 3.12。於專案根目錄執行：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.update_youtube --search-calls 2 --output output/youtube_live.json
```

先在執行環境設定 `YOUTUBE_API_KEY`。`.env.example` 只列名稱；程式不會自動讀取 `.env`。本機收集不需要發布 Token，只有執行 `bash scripts/publish_frontend.sh` 才需要。

## 與其他後端的關係

YouTube 會讀取前端已發布的 Twitch JSON，作為額外遊戲名稱字典；這是可缺省的公開資料，不會呼叫 Twitch API，也不需要 Twitch Secrets。Twitch JSON 缺失時仍能用 Steam 字典和 YouTube 搜尋執行。

發布前重新取得最新前端，只提交本平台一個 JSON；遇到其他後端同時發布時，重新套用到最新分支，最多重試 5 次，不使用 force push。API 或發布失敗時保留前端上一版資料。

## 資料限制

YouTube 資料是搜尋抽樣，遊戲名稱由直播標題比對；台灣／亞洲以頻道自行填寫的國家為代理，未知國家保留 unknown。既有搜尋邏輯通常使用 2 次 search.list，搜尋無結果時可能加 1 次備援；`--search-calls` 是既有搜尋詞容量參數，不是嚴格的 API 請求上限。

本次是程式拆分，沿用既有收集與統計邏輯，未把舊資料標記成新量測。

## 來源

原始程式：`danielet087/game-trend-radar-backend`，來源提交 `86ff4fa9d15aa8c8b9756a102b5ea810241a1de6`。只搬移目前所需的原始碼與對應測試，未搬移舊 Repo 的 Secrets、Actions 紀錄、Steam 主檔或實驗資料。

Secrets 設定參考：[GitHub 官方文件](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)。
