"""對外 API 結構。

看板卡片(SuggestionCard)必備三件事:為什麼、預期效果、衝突標記。
對外文案不出現 manifest / trigger / threshold 等字;數值欄位(健康度/門檻)
只在工作台層由前端決定是否顯示。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str
    type: str
    tags: list[str] = Field(default_factory=list)


class UpdateScoreRequest(BaseModel):
    value: int
    speed: str = "internal"  # internal | external


class SuggestionCard(BaseModel):
    id: int
    module_id: int
    module_name: str
    skill_id: int | None
    skill_name: str | None
    why: str                 # 為什麼(白話,連使用者情境)
    predicted_effect: str    # 預期效果
    conflict_group: str | None
    needs_confirmation: bool  # 高風險 → 強制人工確認
    source: str
    status: str


class ModuleView(BaseModel):
    id: int
    name: str
    role_key: str
    order_index: int
    status: str
    score: int
    threshold: int
    mounted_skills: list[str]
    open_suggestions: list[SuggestionCard]


class BoardView(BaseModel):
    project_id: int
    project_name: str
    project_type: str
    project_status: str
    tags: list[str]
    modules: list[ModuleView]
