"""核心邏輯 — 規格第 6 節。

配對器只做三件事,不做決策:
  1. 找出符合的 skill
  2. 用白話講清楚「為什麼」+「預期效果」
  3. 標出衝突(同 conflict_group 互斥)
所有輸出都是 Suggestion(pending),由使用者拍板。
"""

from __future__ import annotations

import json
import re

from sqlmodel import Session, select

from .models import (
    Module,
    Project,
    ProjectSkill,
    ScoreEvent,
    Skill,
    Suggestion,
)
from .templates import modules_for_type


# --------------------------------------------------------------------------- #
# 工具                                                                          #
# --------------------------------------------------------------------------- #

def _tags(raw: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


_TRIGGER_RE = re.compile(r"^\s*score\s*(<=|>=|<|>|==)\s*(\d+)\s*$")
_OPS = {
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
}


def trigger_matches(trigger_expr: str | None, score: int) -> bool:
    """安全評估 trigger_expr(只支援 `score <op> <int>`,不用 eval)。"""
    if not trigger_expr:
        return False
    m = _TRIGGER_RE.match(trigger_expr)
    if not m:
        return False
    op, num = m.group(1), int(m.group(2))
    return _OPS[op](score, num)


def _render_effect(skill: Skill, before: int | None = None) -> str:
    """把 predicted_effect 樣板裡的 {before}/{after} 填成當下分數。"""
    text = skill.predicted_effect or ""
    if before is None or "{before}" not in text:
        return text
    # 用預期效果推估目標:high 風險通常是補救型,拉到門檻之上一截
    after = min(100, max(before + 20, 85))
    return text.format(before=before, after=after)


def _has_open_or_active(
    session: Session, project_id: int, module_id: int, skill_id: int
) -> bool:
    """該 skill 在此模組是否已經有 pending 建議、或已 active/skipped 掛載。"""
    pending = session.exec(
        select(Suggestion).where(
            Suggestion.project_id == project_id,
            Suggestion.module_id == module_id,
            Suggestion.skill_id == skill_id,
            Suggestion.status == "pending",
        )
    ).first()
    if pending:
        return True
    mounted = session.exec(
        select(ProjectSkill).where(
            ProjectSkill.project_id == project_id,
            ProjectSkill.module_id == module_id,
            ProjectSkill.skill_id == skill_id,
        )
    ).first()
    return mounted is not None


# --------------------------------------------------------------------------- #
# 建立案子                                                                      #
# --------------------------------------------------------------------------- #

def create_project(
    session: Session, name: str, project_type: str, tags: list[str]
) -> Project:
    """依 type 樣板建立 modules,並對每個 module 做靜態配對產生 suggestions。"""
    project = Project(
        name=name,
        type=project_type,
        tags=json.dumps(tags, ensure_ascii=False),
        status="building",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    # 依樣板建立模組
    modules: list[Module] = []
    for spec in modules_for_type(project_type):
        module = Module(
            project_id=project.id,
            name=spec["name"],
            role_key=spec["role_key"],
            order_index=spec["order_index"],
            threshold=spec["threshold"],
        )
        session.add(module)
        modules.append(module)
    session.commit()
    for module in modules:
        session.refresh(module)

    # 靜態配對:role_key 相符 且 applies_tags ∩ project.tags ≠ ∅
    project_tags = set(tags)
    for module in modules:
        skills = session.exec(
            select(Skill).where(Skill.role_key == module.role_key)
        ).all()
        for skill in skills:
            applies = set(_tags(skill.applies_tags))
            if not applies or not (applies & project_tags):
                continue
            if _has_open_or_active(session, project.id, module.id, skill.id):
                continue
            session.add(
                Suggestion(
                    project_id=project.id,
                    module_id=module.id,
                    skill_id=skill.id,
                    source="static_match",
                    reason=skill.reason_template,
                    predicted_effect=_render_effect(skill),
                    conflict_group=skill.conflict_group,
                    status="pending",
                )
            )
    session.commit()
    return project


# --------------------------------------------------------------------------- #
# 更新健康度                                                                    #
# --------------------------------------------------------------------------- #

def update_score(
    session: Session, module_id: int, value: int, speed: str = "internal"
) -> list[Suggestion]:
    """寫入 ScoreEvent、更新 module.score,必要時動態觸發建議。

    回傳這次新產生的 suggestions。
    """
    module = session.get(Module, module_id)
    if module is None:
        raise ValueError(f"module {module_id} not found")

    value = max(0, min(100, value))
    session.add(ScoreEvent(module_id=module_id, value=value, signal_speed=speed))
    module.score = value

    new_suggestions: list[Suggestion] = []
    if value < module.threshold:
        module.status = "needs_attention"
        skills = session.exec(
            select(Skill).where(Skill.role_key == module.role_key)
        ).all()
        for skill in skills:
            if not trigger_matches(skill.trigger_expr, value):
                continue
            if _has_open_or_active(session, module.project_id, module.id, skill.id):
                continue
            suggestion = Suggestion(
                project_id=module.project_id,
                module_id=module.id,
                skill_id=skill.id,
                source="score_trigger",
                reason=skill.reason_template,
                predicted_effect=_render_effect(skill, before=value),
                conflict_group=skill.conflict_group,
                status="pending",
            )
            session.add(suggestion)
            new_suggestions.append(suggestion)
    else:
        module.status = "resting"

    session.add(module)
    session.commit()
    for suggestion in new_suggestions:
        session.refresh(suggestion)
    return new_suggestions


# --------------------------------------------------------------------------- #
# 採用 / 略過建議                                                               #
# --------------------------------------------------------------------------- #

def adopt_suggestion(session: Session, suggestion_id: int) -> ProjectSkill:
    """採用:掛上 ProjectSkill、同 conflict_group 其他 pending 建議自動 skipped。"""
    suggestion = session.get(Suggestion, suggestion_id)
    if suggestion is None:
        raise ValueError(f"suggestion {suggestion_id} not found")
    if suggestion.status != "pending":
        raise ValueError(f"suggestion {suggestion_id} 已處理過({suggestion.status})")
    if suggestion.skill_id is None:
        raise ValueError("此建議沒有對應的能力可掛載")

    project_skill = ProjectSkill(
        project_id=suggestion.project_id,
        module_id=suggestion.module_id,
        skill_id=suggestion.skill_id,
        state="active",
    )
    session.add(project_skill)

    # 同 conflict_group 的其他 pending suggestion → skipped(二選一)
    if suggestion.conflict_group:
        conflicts = session.exec(
            select(Suggestion).where(
                Suggestion.project_id == suggestion.project_id,
                Suggestion.module_id == suggestion.module_id,
                Suggestion.conflict_group == suggestion.conflict_group,
                Suggestion.status == "pending",
                Suggestion.id != suggestion.id,
            )
        ).all()
        for other in conflicts:
            other.status = "skipped"
            session.add(other)

    suggestion.status = "adopted"
    session.add(suggestion)
    session.commit()

    _recompute_module_status(session, suggestion.module_id)
    session.refresh(project_skill)
    return project_skill


def skip_suggestion(session: Session, suggestion_id: int) -> Suggestion:
    """略過:status=skipped(不刪除,保留出口:可回頭、可解釋風險)。"""
    suggestion = session.get(Suggestion, suggestion_id)
    if suggestion is None:
        raise ValueError(f"suggestion {suggestion_id} not found")
    if suggestion.status != "pending":
        raise ValueError(f"suggestion {suggestion_id} 已處理過({suggestion.status})")
    suggestion.status = "skipped"
    session.add(suggestion)
    session.commit()
    _recompute_module_status(session, suggestion.module_id)
    session.refresh(suggestion)
    return suggestion


def _recompute_module_status(session: Session, module_id: int) -> None:
    """沒有待處理建議、且分數達標的模組回到 resting。"""
    module = session.get(Module, module_id)
    if module is None:
        return
    open_count = len(
        session.exec(
            select(Suggestion).where(
                Suggestion.module_id == module_id,
                Suggestion.status == "pending",
            )
        ).all()
    )
    if open_count == 0 and module.score >= module.threshold:
        module.status = "resting"
    elif open_count == 0 and module.status == "needs_attention":
        # 建議都處理完了,但分數仍偏低:離開「需要注意」的待辦狀態
        module.status = "active"
    session.add(module)
    session.commit()
