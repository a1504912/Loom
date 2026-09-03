"""對外 API 結構。

看板卡片(SuggestionCard)必備三件事:為什麼、預期效果、衝突標記。
對外文案不出現 manifest / trigger / threshold 等字;數值欄位(健康度/門檻)
只在工作台層由前端決定是否顯示。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# 請求                                                                          #
# --------------------------------------------------------------------------- #

class CreateProjectRequest(BaseModel):
    name: str
    type: str
    tags: list[str] = Field(default_factory=list)
    category: str = ""
    cat_key: str = "other"


class UpdateScoreRequest(BaseModel):
    value: int
    speed: str = "internal"  # internal | external


class SetModelRequest(BaseModel):
    model_key: str  # claude | gpt | gemini


class SetTaskRequest(BaseModel):
    task: str = ""
    task_note: str | None = None


class ReviewOutputRequest(BaseModel):
    decision: str  # approve | reject


class ToggleChannelRequest(BaseModel):
    channel: str


# --------------------------------------------------------------------------- #
# 回應                                                                          #
# --------------------------------------------------------------------------- #

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


class OutputView(BaseModel):
    id: int
    title: str
    state: str               # done | review | running | rejected
    by: str
    when: str
    items: list[str]


class AccountView(BaseModel):
    id: int
    channel: str
    state: str               # none | applying | ready
    handle: str


class ModuleView(BaseModel):
    id: int
    name: str
    role_key: str
    order_index: int
    status: str
    score: int
    threshold: int
    model_key: str
    task: str
    task_note: str
    mounted_skills: list[str]
    open_suggestions: list[SuggestionCard]
    outputs: list[OutputView]
    accounts: list[AccountView]


class BoardView(BaseModel):
    project_id: int
    project_name: str
    project_type: str
    project_status: str
    category: str
    cat_key: str
    stage: str
    tags: list[str]
    trend: list[int]
    health: int
    modules: list[ModuleView]


class CategoryView(BaseModel):
    key: str
    name: str
    count: int


class ProjectSummary(BaseModel):
    id: int
    name: str
    category: str
    cat_key: str
    type: str
    stage: str
    tags: list[str]
    health: int
    alerts: int


class HudView(BaseModel):
    project_count: int
    avg_health: int
    pending: int


class OverviewView(BaseModel):
    categories: list[CategoryView]
    projects: list[ProjectSummary]
    hud: HudView
