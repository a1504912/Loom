"""驗收測試 — 對應規格第 10 節走查範例。

案子:記帳 app,type=accounting_app,tags=["accounting","payment","mobile"]
全程只用「採用 / 略過 + 更新健康度」完成,不碰 manifest/threshold 等字眼。
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app import services
from app.models import Module, ProjectSkill, Suggestion
from app.seed import seed_skills


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        seed_skills(s)
        yield s


def _modules(session, project_id):
    return {
        m.role_key: m
        for m in session.exec(
            select(Module).where(Module.project_id == project_id)
        ).all()
    }


def _pending(session, module_id):
    return session.exec(
        select(Suggestion).where(
            Suggestion.module_id == module_id,
            Suggestion.status == "pending",
        )
    ).all()


def test_step1_four_modules(session):
    """步驟 1:建立 → 產生四模組。"""
    project = services.create_project(
        session, "記帳 app", "accounting_app", ["accounting", "payment", "mobile"]
    )
    modules = _modules(session, project.id)
    assert set(modules) == {"design", "code", "security", "growth"}
    names = [
        m.name
        for m in sorted(modules.values(), key=lambda m: m.order_index)
    ]
    assert names == ["設計層", "程式層", "資安層", "推廣層"]
    assert project.status == "building"


def test_step2_static_matching(session):
    """步驟 2:靜態配對 → 程式層與資安層各得白話建議。"""
    project = services.create_project(
        session, "記帳 app", "accounting_app", ["accounting", "payment", "mobile"]
    )
    modules = _modules(session, project.id)

    code_suggestions = {
        _skill_name(session, s): s for s in _pending(session, modules["code"].id)
    }
    security_suggestions = {
        _skill_name(session, s): s for s in _pending(session, modules["security"].id)
    }

    assert set(code_suggestions) == {"本地資料庫", "金流串接"}
    assert set(security_suggestions) == {"個資保護"}

    # 加密儲存不在開案靜態建議中(等健康度掉下來才動態補強)
    assert "加密儲存" not in security_suggestions

    # 卡片是白話的,不出現內部字眼
    for s in code_suggestions.values():
        assert s.reason
        for banned in ("manifest", "trigger", "threshold", "applies_tags"):
            assert banned not in s.reason


def test_step3_adopt_creates_project_skill(session):
    """步驟 3:採用建議 → 建立對應 ProjectSkill。"""
    project = services.create_project(
        session, "記帳 app", "accounting_app", ["accounting", "payment", "mobile"]
    )
    modules = _modules(session, project.id)
    sug = _pending(session, modules["code"].id)[0]

    services.adopt_suggestion(session, sug.id)

    mounted = session.exec(
        select(ProjectSkill).where(ProjectSkill.skill_id == sug.skill_id)
    ).all()
    assert len(mounted) == 1
    assert mounted[0].state == "active"
    session.refresh(sug)
    assert sug.status == "adopted"


def test_step5_dynamic_high_risk_suggestion(session):
    """步驟 4→5:資安層健康度 58 < 門檻 75 → 動態產生『加密儲存』高風險建議。"""
    project = services.create_project(
        session, "記帳 app", "accounting_app", ["accounting", "payment", "mobile"]
    )
    security = _modules(session, project.id)["security"]

    new = services.update_score(session, security.id, 58, speed="internal")
    names = {_skill_name(session, s) for s in new}

    assert "加密儲存" in names
    session.refresh(security)
    assert security.status == "needs_attention"

    # 高風險 → 強制人工;預期效果已填入實際分數
    from app.models import Skill

    enc = session.exec(select(Skill).where(Skill.name == "加密儲存")).first()
    assert enc.risk_level == "high"
    enc_sug = next(s for s in new if s.skill_id == enc.id)
    assert "58" in enc_sug.predicted_effect


def test_step6_adopt_skips_conflict_and_rests(session):
    """步驟 6:採用『加密儲存』→ 掛上、衝突建議自動 skipped、資安層恢復。"""
    project = services.create_project(
        session, "記帳 app", "accounting_app", ["accounting", "payment", "mobile"]
    )
    security = _modules(session, project.id)["security"]
    services.update_score(session, security.id, 58, speed="internal")

    from app.models import Skill

    enc = session.exec(select(Skill).where(Skill.name == "加密儲存")).first()
    perf = session.exec(select(Skill).where(Skill.name == "效能優先儲存")).first()

    enc_sug = session.exec(
        select(Suggestion).where(
            Suggestion.skill_id == enc.id, Suggestion.status == "pending"
        )
    ).first()
    perf_sug = session.exec(
        select(Suggestion).where(
            Suggestion.skill_id == perf.id, Suggestion.status == "pending"
        )
    ).first()
    # 兩者同 conflict_group,UI 呈現二選一
    assert enc_sug.conflict_group == perf_sug.conflict_group == "storage_security"

    services.adopt_suggestion(session, enc_sug.id)

    session.refresh(perf_sug)
    assert perf_sug.status == "skipped"  # 衝突建議自動略過

    mounted = session.exec(
        select(ProjectSkill).where(ProjectSkill.skill_id == enc.id)
    ).first()
    assert mounted is not None and mounted.state == "active"

    # 分數回升到門檻上 → 資安層回到 resting
    services.update_score(session, security.id, 85, speed="internal")
    session.refresh(security)
    assert security.status == "resting"


def test_skip_preserves_exit(session):
    """略過不刪除,保留出口。"""
    project = services.create_project(
        session, "記帳 app", "accounting_app", ["accounting", "payment", "mobile"]
    )
    modules = _modules(session, project.id)
    sug = _pending(session, modules["code"].id)[0]
    services.skip_suggestion(session, sug.id)
    session.refresh(sug)
    assert sug.status == "skipped"
    # 仍存在於資料庫
    assert session.get(Suggestion, sug.id) is not None


def test_trigger_expr_safe_eval():
    assert services.trigger_matches("score < 75", 58) is True
    assert services.trigger_matches("score < 75", 80) is False
    assert services.trigger_matches("score <= 75", 75) is True
    assert services.trigger_matches(None, 10) is False
    # 惡意輸入不會被執行,只會安全地不匹配
    assert services.trigger_matches("__import__('os').system('x')", 10) is False


def _skill_name(session, suggestion):
    from app.models import Skill

    skill = session.get(Skill, suggestion.skill_id)
    return skill.name if skill else None
