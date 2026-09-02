"""seed 一組 skill 目錄 — 規格第 9 節步驟 1、第 10 節走查用。

reason_template / predicted_effect 都是白話文案,連到使用者情境,
絕不出現 manifest / trigger / threshold 等字。
"""

from __future__ import annotations

from sqlmodel import Session, select

from .models import Skill

# 每筆 skill 的靜態欄位。predicted_effect 若含 {before}/{after} 佔位符,
# 會在動態觸發時依當下分數填入(見 services.py)。
SKILL_CATALOG: list[dict] = [
    {
        "name": "本地資料庫",
        "role_key": "code",
        "applies_tags": ["accounting", "mobile"],
        "trigger_expr": None,
        "content": "使用本地 SQLite/Room 儲存,離線可用,啟動時建表。",
        "affects_score": "code",
        "risk_level": "low",
        "conflict_group": None,
        "reason_template": "記帳資料要能離線記、隨時查,先在裝置上存好一份最穩。",
        "predicted_effect": "程式層更完整,少一類「沒網路就不能記帳」的客訴。",
    },
    {
        "name": "金流串接",
        "role_key": "code",
        "applies_tags": ["payment"],
        "trigger_expr": None,
        "content": "接第三方金流 SDK,處理付款、退款、對帳。",
        "affects_score": "code",
        "risk_level": "high",  # 動到錢,強制人工確認
        "conflict_group": None,
        "reason_template": "你的案子會收付款,金流要接對才不會漏帳、錯帳。",
        "predicted_effect": "程式層具備收款能力,付款流程可上線。",
    },
    {
        "name": "個資保護",
        "role_key": "security",
        "applies_tags": ["accounting", "payment"],
        "trigger_expr": None,
        "content": "最小化蒐集、去識別化、存取紀錄,對齊個資法基本要求。",
        "affects_score": "security",
        "risk_level": "low",
        "conflict_group": None,
        "reason_template": "記帳會存到使用者的消費與身分資料,先把個資守則立起來。",
        "predicted_effect": "資安層打底,降低個資外洩風險。",
    },
    {
        "name": "加密儲存",
        "role_key": "security",
        # 空的 applies_tags:開案時不鋪底,等健康度掉下來才動態補強
        "applies_tags": [],
        "trigger_expr": "score < 75",
        "content": "敏感欄位改用 AES 加密落地,金鑰交由安全儲存區保管。",
        "affects_score": "security",
        "risk_level": "high",  # 動到資安,強制人工確認
        "conflict_group": "storage_security",
        "reason_template": "目前錢包相關資料是明碼存的,一旦裝置遭竊資料就外流。",
        "predicted_effect": "資安 {before} → 預估 {after}",
    },
    {
        "name": "效能優先儲存",
        "role_key": "security",
        "applies_tags": [],
        "trigger_expr": "score < 75",
        "content": "不加密、以讀寫速度為先的儲存策略。",
        "affects_score": "security",
        "risk_level": "low",
        "conflict_group": "storage_security",  # 與「加密儲存」二選一
        "reason_template": "若這個案子的資料不敏感,可換速度優先,少一層加解密開銷。",
        "predicted_effect": "資安 {before} → 預估 {after}(以效能換取,敏感案子不建議)",
    },
    {
        "name": "觸及率追蹤",
        "role_key": "growth",
        "applies_tags": ["mobile"],
        "trigger_expr": "score < 70",
        "content": "埋設事件追蹤,量測安裝、開啟、留存。",
        "affects_score": "growth",
        "risk_level": "low",
        "conflict_group": None,
        "reason_template": "想知道有多少人真的在用、留下來,得先能量到這些數字。",
        "predicted_effect": "推廣層能看到真實使用數據,後續才有優化依據。",
    },
]


def seed_skills(session: Session) -> int:
    """把目錄寫入 DB(以 name 去重,可重複執行)。回傳新增筆數。"""
    added = 0
    for entry in SKILL_CATALOG:
        exists = session.exec(select(Skill).where(Skill.name == entry["name"])).first()
        if exists:
            continue
        skill = Skill(
            name=entry["name"],
            role_key=entry["role_key"],
            applies_tags=_json(entry["applies_tags"]),
            trigger_expr=entry["trigger_expr"],
            content=entry["content"],
            affects_score=entry["affects_score"],
            risk_level=entry["risk_level"],
            conflict_group=entry["conflict_group"],
            reason_template=entry["reason_template"],
            predicted_effect=entry["predicted_effect"],
            created_by="system",
        )
        session.add(skill)
        added += 1
    session.commit()
    return added


def _json(value) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)
