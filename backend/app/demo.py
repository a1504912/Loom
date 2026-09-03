"""seed 一組示範案子 — 對應設計交接包的原型資料。

只在資料庫還沒有任何案子時才灌入,讓本機一啟動看板就有東西可看。
需要 seed_skills 先跑過(能力目錄要先在)。
"""

from __future__ import annotations

import json
import re

from sqlmodel import Session, select

from .models import Module, Output, Project, ProjectSkill, SocialAccount, Suggestion
from .seed import seed_skills

# 每筆產出的條列摘要(審核對話框用)。
OUT_ITEMS: dict[str, list[str]] = {
    "行動端版面草稿 v3": [
        "首頁、記帳輸入、月報三個主要畫面已定版。",
        "輸入鍵盤區改為單手可及範圍。",
        "待確認:分類圖示是否沿用舊版。",
    ],
    "記帳輸入流程圖": [
        "從桌面捷徑到完成一筆記帳共 3 步。",
        "含拍照存單據的分支。",
        "待確認:重複性支出要不要獨立入口。",
    ],
    "個資盤點清單": [
        "盤出 11 項會落地的個資欄位。",
        "其中 4 項目前為明碼儲存。",
        "建議下一步:先處理錢包相關欄位。",
    ],
    "訂閱頁草稿": [
        "方案比較表 + 單一 CTA。",
        "首屏放咖啡風味描述,價格在第二屏。",
        "待確認:是否顯示年繳折扣。",
    ],
}
OUT_ITEMS_FALLBACK = ["已完成本輪任務,產出可下載。", "沒有需要你決定的項目。"]


# 五個示範案子,結構對齊原型 DATA。
DEMO_PROJECTS: list[dict] = [
    {
        "name": "記帳 app", "category": "記帳工具", "cat_key": "money",
        "type": "accounting_app", "stage": "dev",
        "tags": ["accounting", "payment", "mobile"], "trend": [78, 74, 71, 69, 70, 72],
        "modules": [
            {"name": "設計層", "role_key": "design", "status": "active", "score": 82,
             "threshold": 80, "skills": ["行動端版面"], "model": "gemini", "suggestions": [],
             "outputs": [
                 {"title": "行動端版面草稿 v3", "state": "done", "by": "Gemini", "when": "8/28"},
                 {"title": "記帳輸入流程圖", "state": "review", "by": "Gemini", "when": "8/30"},
             ]},
            {"name": "程式層", "role_key": "code", "status": "active", "score": 76,
             "threshold": 80, "skills": ["本地資料庫"], "model": "claude",
             "suggestions": [
                 {"skill": "金流串接",
                  "why": "你的案子會收付款,金流要接對才不會漏帳、錯帳。",
                  "effect": "程式層具備收款能力,付款流程可上線。", "conflict": None},
             ],
             "outputs": [{"title": "本地資料庫 schema", "state": "done", "by": "Claude", "when": "8/26"}]},
            {"name": "資安層", "role_key": "security", "status": "needs_attention", "score": 58,
             "threshold": 75, "skills": ["個資保護"], "model": "claude",
             "suggestions": [
                 {"skill": "加密儲存",
                  "why": "目前錢包相關資料是明碼存的,一旦裝置遭竊資料就外流。",
                  "effect": "資安 58 → 預估 82", "conflict": "storage_security"},
                 {"skill": "效能優先儲存",
                  "why": "若這個案子的資料不敏感,可換速度優先,少一層加解密開銷。",
                  "effect": "資安 58 → 預估 64(以效能換取,敏感案子不建議)", "conflict": "storage_security"},
             ],
             "outputs": [{"title": "個資盤點清單", "state": "review", "by": "Claude", "when": "8/29"}]},
            {"name": "推廣層", "role_key": "growth", "status": "not_started", "score": 66,
             "threshold": 70, "skills": [], "model": "gpt",
             "suggestions": [
                 {"skill": "觸及率追蹤",
                  "why": "想知道有多少人真的在用、留下來,得先能量到這些數字。",
                  "effect": "推廣層能看到真實使用數據,後續才有優化依據。", "conflict": None},
             ],
             "outputs": []},
        ],
    },
    {
        "name": "出貨排程小工具", "category": "內部工具", "cat_key": "internal",
        "type": "generic", "stage": "dev",
        "tags": ["internal", "ops"], "trend": [70, 76, 80, 83, 86, 88],
        "modules": [
            {"name": "設計層", "role_key": "design", "status": "resting", "score": 88,
             "threshold": 80, "skills": ["表單版面"], "model": "gemini", "suggestions": [],
             "outputs": [{"title": "排程表單版面", "state": "done", "by": "Gemini", "when": "8/20"}]},
            {"name": "程式層", "role_key": "code", "status": "active", "score": 90,
             "threshold": 80, "skills": ["排程引擎"], "model": "claude", "suggestions": [],
             "outputs": [
                 {"title": "排程引擎 v1", "state": "done", "by": "Claude", "when": "8/22"},
                 {"title": "邊界情境測試", "state": "done", "by": "Claude", "when": "8/25"},
             ]},
            {"name": "推廣層", "role_key": "growth", "status": "not_started", "score": 84,
             "threshold": 70, "skills": [], "model": "gpt", "suggestions": [], "outputs": []},
        ],
    },
    {
        "name": "咖啡訂閱網站", "category": "客戶委託", "cat_key": "client",
        "type": "generic", "stage": "dev",
        "tags": ["payment", "web"], "trend": [82, 79, 74, 70, 66, 64],
        "modules": [
            {"name": "設計層", "role_key": "design", "status": "active", "score": 71,
             "threshold": 80, "skills": [], "model": "gemini", "suggestions": [],
             "outputs": [{"title": "訂閱頁草稿", "state": "review", "by": "Gemini", "when": "8/27"}]},
            {"name": "程式層", "role_key": "code", "status": "needs_attention", "score": 62,
             "threshold": 80, "skills": [], "model": "claude",
             "suggestions": [
                 {"skill": "金流串接",
                  "why": "訂閱制每月要自動扣款,金流沒接好會直接掉單。",
                  "effect": "程式層具備定期扣款能力。", "conflict": None},
             ],
             "outputs": [{"title": "商品與方案資料表", "state": "done", "by": "Claude", "when": "8/24"}]},
            {"name": "推廣層", "role_key": "growth", "status": "not_started", "score": 60,
             "threshold": 70, "skills": [], "model": "gpt", "suggestions": [], "outputs": []},
        ],
    },
    {
        "name": "家庭帳本 v2", "category": "記帳工具", "cat_key": "money",
        "type": "accounting_app", "stage": "maintain",
        "tags": ["accounting", "mobile"], "trend": [86, 88, 90, 89, 91, 91],
        "modules": [
            {"name": "設計層", "role_key": "design", "status": "resting", "score": 92,
             "threshold": 80, "skills": ["行動端版面"], "model": "gemini", "suggestions": [],
             "outputs": [{"title": "深色模式版面", "state": "done", "by": "Gemini", "when": "7/12"}]},
            {"name": "程式層", "role_key": "code", "status": "resting", "score": 90,
             "threshold": 80, "skills": ["本地資料庫"], "model": "claude", "suggestions": [],
             "outputs": [{"title": "同步機制重構", "state": "done", "by": "Claude", "when": "7/30"}]},
            {"name": "資安層", "role_key": "security", "status": "resting", "score": 93,
             "threshold": 75, "skills": ["個資保護", "加密儲存"], "model": "claude", "suggestions": [],
             "outputs": [{"title": "加密儲存實作報告", "state": "done", "by": "Claude", "when": "8/02"}]},
            {"name": "推廣層", "role_key": "growth", "status": "resting", "score": 88,
             "threshold": 70, "skills": ["觸及率追蹤"], "model": "gpt", "suggestions": [],
             "outputs": [{"title": "上架素材組", "state": "done", "by": "GPT", "when": "8/10"}],
             "accounts": [
                 {"channel": "Instagram", "state": "ready", "handle": "@familybook"},
                 {"channel": "LINE 官方帳號", "state": "applying", "handle": "@familybook"},
             ]},
        ],
    },
    {
        "name": "內部報表面板", "category": "內部工具", "cat_key": "internal",
        "type": "generic", "stage": "maintain",
        "tags": ["internal", "data"], "trend": [84, 83, 81, 80, 79, 79],
        "modules": [
            {"name": "設計層", "role_key": "design", "status": "resting", "score": 84,
             "threshold": 80, "skills": [], "model": "gemini", "suggestions": [],
             "outputs": [{"title": "報表版面規格", "state": "done", "by": "Gemini", "when": "6/18"}]},
            {"name": "程式層", "role_key": "code", "status": "resting", "score": 81,
             "threshold": 80, "skills": ["快取層"], "model": "claude", "suggestions": [],
             "outputs": [{"title": "快取層說明文件", "state": "done", "by": "Claude", "when": "7/05"}]},
            {"name": "推廣層", "role_key": "growth", "status": "needs_attention", "score": 68,
             "threshold": 70, "skills": [], "model": "gpt",
             "suggestions": [
                 {"skill": "觸及率追蹤",
                  "why": "報表做出來了,但沒人知道誰在看、看了哪幾張。",
                  "effect": "推廣 68 → 預估 78", "conflict": None},
             ],
             "outputs": []},
        ],
    },
]


def _predicted_score(effect: str) -> int | None:
    m = re.search(r"預估\s*(\d+)", effect)
    return int(m.group(1)) if m else None


def seed_demo(session: Session) -> int:
    """灌入示範案子(僅在沒有任何案子時)。回傳建立的案子數。"""
    seed_skills(session)  # 確保能力目錄在
    if session.exec(select(Project)).first():
        return 0

    from .models import Skill

    skills_by_name = {s.name: s for s in session.exec(select(Skill)).all()}

    created = 0
    for order_p, pdata in enumerate(DEMO_PROJECTS):
        project = Project(
            name=pdata["name"],
            type=pdata["type"],
            tags=json.dumps(pdata["tags"], ensure_ascii=False),
            status="building" if pdata["stage"] == "dev" else "optimizing",
            category=pdata["category"],
            cat_key=pdata["cat_key"],
            stage=pdata["stage"],
            trend=json.dumps(pdata["trend"]),
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        for order_m, mdata in enumerate(pdata["modules"]):
            module = Module(
                project_id=project.id,
                name=mdata["name"],
                role_key=mdata["role_key"],
                order_index=order_m,
                status=mdata["status"],
                score=mdata["score"],
                threshold=mdata["threshold"],
                model_key=mdata.get("model", ""),
            )
            session.add(module)
            session.commit()
            session.refresh(module)

            for skill_name in mdata.get("skills", []):
                skill = skills_by_name.get(skill_name)
                if skill:
                    session.add(ProjectSkill(
                        project_id=project.id, module_id=module.id,
                        skill_id=skill.id, state="active",
                    ))

            for sug in mdata.get("suggestions", []):
                skill = skills_by_name.get(sug["skill"])
                session.add(Suggestion(
                    project_id=project.id,
                    module_id=module.id,
                    skill_id=skill.id if skill else None,
                    source="score_trigger" if _predicted_score(sug["effect"]) else "static_match",
                    reason=sug["why"],
                    predicted_effect=sug["effect"],
                    predicted_score=_predicted_score(sug["effect"]),
                    conflict_group=sug["conflict"],
                    status="pending",
                ))

            for order_o, out in enumerate(mdata.get("outputs", [])):
                session.add(Output(
                    module_id=module.id,
                    title=out["title"],
                    state=out["state"],
                    by=out["by"],
                    when_label=out["when"],
                    items=json.dumps(OUT_ITEMS.get(out["title"], OUT_ITEMS_FALLBACK), ensure_ascii=False),
                    order_index=order_o,
                ))

            for acc in mdata.get("accounts", []):
                session.add(SocialAccount(
                    module_id=module.id, channel=acc["channel"],
                    state=acc["state"], handle=acc["handle"],
                ))

            session.commit()
        created += 1

    return created
