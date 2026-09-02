"""案子類型樣板 — 配對器演進第 1 階段:手動樣板(MVP)。

案子類型 = 一組預設模組(含 role_key / order_index / threshold)。
之後可換成標籤配對、學習推薦(見規格第 4 節)。
"""

from __future__ import annotations

from typing import TypedDict


class ModuleSpec(TypedDict):
    name: str
    role_key: str
    order_index: int
    threshold: int


# type -> 預設模組清單(流水線順序)
MODULE_TEMPLATES: dict[str, list[ModuleSpec]] = {
    "accounting_app": [
        {"name": "設計層", "role_key": "design", "order_index": 0, "threshold": 80},
        {"name": "程式層", "role_key": "code", "order_index": 1, "threshold": 80},
        {"name": "資安層", "role_key": "security", "order_index": 2, "threshold": 75},
        {"name": "推廣層", "role_key": "growth", "order_index": 3, "threshold": 70},
    ],
    # 通用退回樣板:任何未知類型都有一條可跑的流水線
    "generic": [
        {"name": "設計層", "role_key": "design", "order_index": 0, "threshold": 80},
        {"name": "程式層", "role_key": "code", "order_index": 1, "threshold": 80},
        {"name": "推廣層", "role_key": "growth", "order_index": 2, "threshold": 70},
    ],
}


def modules_for_type(project_type: str) -> list[ModuleSpec]:
    """取得案子類型的預設模組;未知類型退回 generic。"""
    return MODULE_TEMPLATES.get(project_type, MODULE_TEMPLATES["generic"])
