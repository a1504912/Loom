"""SQLModel 資料模型 — 對應規格第 5 節。

命名鐵則:對內(程式/DB)可用 manifest / trigger / threshold;
對外的 API 回應與 UI 文案絕不出現這些字(見 schemas.py 的對外映射)。
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.utcnow()


class Project(SQLModel, table=True):
    """案子。"""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    type: str                       # 案子類型,例:accounting_app
    tags: str = "[]"                # JSON list,靜態配對用
    status: str = "building"        # building | optimizing
    created_at: datetime = Field(default_factory=_now)


class Module(SQLModel, table=True):
    """模組 / 層 — 流程中的一個角色。"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    name: str                       # 設計層 / 程式層 / 資安層 / 推廣層
    role_key: str                   # design | code | security | growth …
    order_index: int                # 流水線順序
    status: str = "not_started"     # not_started | active | resting | needs_attention
    score: int = 0                  # 健康度 0–100
    threshold: int = 80             # 低於此值觸發建議


class Skill(SQLModel, table=True):
    """能力(全域目錄,一張 manifest)。"""

    id: int | None = Field(default=None, primary_key=True)
    name: str                       # 對外顯示名,例:加密儲存
    role_key: str                   # 掛哪層
    applies_tags: str = "[]"        # JSON list,靜態配對
    trigger_expr: str | None = None # 動態觸發,例:"score < 75"
    content: str = ""               # 注入的指令 / 工具 / 檢查清單
    affects_score: str = ""         # 影響哪個 role_key 的分數
    risk_level: str = "low"         # low | high
    conflict_group: str | None = None
    reason_template: str = ""       # 白話「為什麼」,連使用者情境
    predicted_effect: str = ""      # 白話「預期效果」樣板
    created_by: str = "system"      # system | user


class ProjectSkill(SQLModel, table=True):
    """掛在某案子某模組上的 skill 實例。"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    module_id: int = Field(foreign_key="module.id", index=True)
    skill_id: int = Field(foreign_key="skill.id")
    state: str = "active"           # active | skipped
    mounted_at: datetime = Field(default_factory=_now)


class Suggestion(SQLModel, table=True):
    """建議(= 優化票,統一)。"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    module_id: int = Field(foreign_key="module.id", index=True)
    skill_id: int | None = Field(default=None, foreign_key="skill.id")
    source: str                     # static_match | score_trigger | pipeline_ticket
    reason: str                     # 白話原因,連使用者情境
    predicted_effect: str = ""      # 例:資安 58 → 預估 85
    conflict_group: str | None = None
    status: str = "pending"         # pending | adopted | skipped
    created_at: datetime = Field(default_factory=_now)


class ScoreEvent(SQLModel, table=True):
    """健康度軌跡(依質優化的依據)。"""

    id: int | None = Field(default=None, primary_key=True)
    module_id: int = Field(foreign_key="module.id", index=True)
    value: int
    signal_speed: str               # internal | external
    recorded_at: datetime = Field(default_factory=_now)
