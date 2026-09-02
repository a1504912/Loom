# 多流程專案系統 — 建置規格(Atelier)

> 專案代號:`Atelier`(工作坊)。「先建案子 → 預設流程 → 分模組 → 掛 skill」的通用專案平台,不綁定領域。可作為 Dispatch(派工調度站)的延伸模組。

## 1. 一句話目標
讓使用者建立一個「案子」,系統依案子類型排好預設流程與模組,每個模組可掛可換的 skill 讓產出更準;開發階段一次生出 v1,之後系統長期監測品質、**主動建議、由使用者拍板**優化。

## 2. 核心概念與術語

| 對內(程式/DB) | 對外(新手 UI) | 說明 |
|---|---|---|
| project | 案子 / 專案 | 一個目標,例:記帳 app |
| module | 分工 / 團隊成員 | 流程中的一個角色:設計層、程式層、資安層、推廣層… |
| skill (manifest) | 能力 | 掛在模組上的能力包 |
| quality score | 健康度 | 每個模組的品質分數 0–100 |
| suggestion | 建議 | 系統提出、使用者決定的優化項 |

**設計鐵則:對外文案絕不出現 manifest / trigger / threshold 這類字。**

## 3. 架構:兩階段

- **開發階段 — 流水線**:模組線性往前跑,只往前不退回。任何「之後該重做」的發現產生一張 `suggestion`(source = `pipeline_ticket`)。跑完退場,產出 v1。
- **優化階段 — 長住 runtime**:orchestrator 監看健康度,掉到門檻下產生 `suggestion`(source = `score_trigger`)。調度只建議,不自動動手;使用者採用才執行。待命為常態。

品質訊號兩種速度:內部(快:測試通過率、覆蓋率、弱點掃描)、外部(慢:觸及率、轉換、真實回饋)。

## 4. skill 選用機制
skill 一張 manifest,靜態/動態共用同一張卡、只比對不同欄位:
- 開案時(靜態):比對 `applies_tags` ∩ 案子 tags,鋪底建議。
- 優化時(動態):比對 `trigger_expr`(如 `score < 75`),補強建議。

兩種都只產生 `suggestion`(pending),由使用者決定。配對器只做三件事:找出符合的 skill、白話講「為什麼 + 預期效果」、標出衝突(同 `conflict_group` 互斥)。

**風險分級**:`risk_level = high` 一律強制人工確認;`low` 且信任的未來可「自動掛」(MVP 先不做)。

配對器演進:1) 手動樣板(MVP);2) 標籤配對;3) 學習推薦。

## 5. 資料模型
見 `backend/app/models.py`(SQLModel / SQLite)。

## 6. 核心邏輯
見 `backend/app/services.py`。建立案子、更新健康度、採用建議、略過建議四段邏輯。

## 7. UI/UX:漸進揭露三層
1. 對話層(新手預設):一句話開案。
2. 看板層(日常):健康度總覽,安好模組一行,`needs_attention` 展開成「為什麼 + 採用 / 先略過」卡片。
3. 工作台層(進階):完整 module + skill + threshold 全開。

看板卡片必備:為什麼(連使用者情境)、預期效果、衝突標記。

## 8. 技術棧
後端 FastAPI + SQLModel + SQLite;前端 React + Vite + Tailwind;Agent 本地 Ollama;部署 Railway / Render。

## 9. MVP 建置順序
1. schema + 建表 + seed skill 目錄
2. 建立案子 API(依 type 樣板產 modules + 靜態配對產 suggestions)
3. 看板 UI(健康度列 + 建議卡)
4. 採用 / 略過 API(含 conflict_group 連動)
5. 健康度更新 API + 動態觸發產 suggestions
6.(之後)對話層、信任自動掛、學習推薦

本 MVP 已實作步驟 1–5。

## 10. 走查範例(驗收測試)
見 `backend/tests/test_walkthrough.py`,對應規格第 10 節逐步驗證。
