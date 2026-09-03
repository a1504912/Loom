# Atelier — 多流程專案系統

「先建案子 → 預設流程 → 分模組 → 掛 skill」的通用專案平台。開發階段一次生出 v1,
之後系統長期監測品質、**主動建議、由使用者拍板**優化。完整規格見
[`docs/atelier-spec.md`](docs/atelier-spec.md)。

本 repo 實作了 MVP 建置順序的步驟 1–5:

1. SQLModel schema + 建表 + seed skill 目錄
2. 建立案子 API(依 type 樣板產 modules + 靜態配對產 suggestions)
3. 看板 UI(健康度列 + 建議卡)
4. 採用 / 略過 API(含 conflict_group 連動)
5. 健康度更新 API + 動態觸發產 suggestions

## 架構

- **後端**:FastAPI + SQLModel + SQLite(`backend/`)
- **前端**:React + Vite + Tailwind CSS(`frontend/`)

兩階段:開發階段的線性流水線(只往前)、優化階段的長住 runtime(監看健康度、只建議不動手)。

## 跑起來

### 後端

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
```

啟動時自動建表並 seed 一組 skill 目錄。API 文件在 `/docs`。

### 前端

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173,/api 代理到 :8000
```

## 測試(= 規格第 10 節走查驗收)

```bash
cd backend
. .venv/bin/activate
PYTHONPATH=. pytest -q
```

`tests/test_walkthrough.py` 逐步驗證記帳 app 走查:四模組 → 靜態配對 → 採用 →
資安層健康度 58 觸發高風險建議「加密儲存」→ 採用後衝突建議自動略過、資安層回到待命。

## 看板 UI(Industry design system)

前端看板依設計交接包重建,套用 Industry 鋼藍藍圖風格(`frontend/src/industry.css`
為設計 token 與元件層來源):

- **左欄**:深色場,分類篩選 + 「執行中 · 開發階段」/「維護中 · 優化階段」兩組案子。
- **主區**:標頭(麵包屑、案名、tags、進階開關、整體健康度儀表 + 近 6 週趨勢柱)、
  HUD 讀數條、**橫向流水線**(每個分工層一欄)。
- **每一欄**:步驟標、狀態、健康度進度條、已掛能力、執行模型(Claude/GPT/Gemini)、
  主要任務、完成結果(可審核)、建議卡;推廣層另有社群通路與帳號辦理。
- **對話框**:產出審核、高風險採用確認。

後端首次啟動會 seed 一組示範案子(記帳 app、家庭帳本 v2…),看板一開就有資料。

## 主要 API

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/api/overview` | 左欄 + HUD:全部案子摘要、分類、系統讀數 |
| POST | `/api/projects` | 建立案子(依 type 產模組 + 靜態配對建議) |
| GET | `/api/projects/{id}/board` | 看板視圖(模組 + 建議卡 + 產出 + 帳號) |
| POST | `/api/suggestions/{id}/adopt` | 採用建議(掛 skill、連動 skip 衝突、提升健康度) |
| POST | `/api/suggestions/{id}/skip` | 略過建議(保留出口) |
| POST | `/api/modules/{id}/score` | 回報健康度(必要時動態觸發建議) |
| POST | `/api/modules/{id}/model` | 設定該層執行模型 |
| POST | `/api/modules/{id}/task` | 設定該層主要任務與備註 |
| POST | `/api/modules/{id}/channels` | 開/關一個社群通路(推廣層) |
| POST | `/api/accounts/{id}/apply` | 開始辦理某通路帳號 |
| POST | `/api/outputs/{id}/review` | 核可 / 退回一筆產出 |

## 設計鐵則

對外文案絕不出現 `manifest` / `trigger` / `threshold` 這類字;看板卡片一律只講
「為什麼(連使用者情境)」「預期效果」「衝突(二選一)」。高風險(動到錢、資安)
一律強制人工確認。
