"""FastAPI 入口 — 提供建立案子、總覽、看板、採用/略過、健康度、
執行模型/任務、產出審核、社群通路等 API。"""

from __future__ import annotations

import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from . import services
from .db import create_db_and_tables, engine, get_session
from .demo import seed_demo
from .models import (
    Module,
    Output,
    Project,
    ProjectSkill,
    Skill,
    SocialAccount,
    Suggestion,
)
from .schemas import (
    AccountView,
    BoardView,
    CategoryView,
    CreateProjectRequest,
    HudView,
    ModuleView,
    OutputView,
    OverviewView,
    ProjectSummary,
    ReviewOutputRequest,
    SetModelRequest,
    SetTaskRequest,
    SuggestionCard,
    ToggleChannelRequest,
    UpdateScoreRequest,
)

app = FastAPI(title="Atelier — 多流程專案系統")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        seed_demo(session)  # 內含 seed_skills;只在空庫時灌示範案子


# --------------------------------------------------------------------------- #
# 衍生值                                                                        #
# --------------------------------------------------------------------------- #

def _project_modules(session: Session, project_id: int) -> list[Module]:
    return session.exec(
        select(Module).where(Module.project_id == project_id).order_by(Module.order_index)
    ).all()


def _project_health(session: Session, project_id: int) -> int:
    modules = _project_modules(session, project_id)
    if not modules:
        return 0
    return round(sum(m.score for m in modules) / len(modules))


def _pending_count(session: Session, project_id: int) -> int:
    return len(
        session.exec(
            select(Suggestion).where(
                Suggestion.project_id == project_id,
                Suggestion.status == "pending",
            )
        ).all()
    )


# --------------------------------------------------------------------------- #
# 組看板視圖                                                                    #
# --------------------------------------------------------------------------- #

def _suggestion_card(session: Session, s: Suggestion, module_name: str) -> SuggestionCard:
    skill = session.get(Skill, s.skill_id) if s.skill_id else None
    needs_confirmation = bool(skill and skill.risk_level == "high")
    return SuggestionCard(
        id=s.id,
        module_id=s.module_id,
        module_name=module_name,
        skill_id=s.skill_id,
        skill_name=skill.name if skill else None,
        why=s.reason,
        predicted_effect=s.predicted_effect,
        conflict_group=s.conflict_group,
        needs_confirmation=needs_confirmation,
        source=s.source,
        status=s.status,
    )


def _build_board(session: Session, project: Project) -> BoardView:
    modules = _project_modules(session, project.id)

    module_views: list[ModuleView] = []
    for module in modules:
        mounted = session.exec(
            select(ProjectSkill).where(
                ProjectSkill.module_id == module.id,
                ProjectSkill.state == "active",
            )
        ).all()
        mounted_names: list[str] = []
        for ps in mounted:
            skill = session.get(Skill, ps.skill_id)
            if skill:
                mounted_names.append(skill.name)

        open_suggestions = session.exec(
            select(Suggestion).where(
                Suggestion.module_id == module.id,
                Suggestion.status == "pending",
            )
        ).all()
        cards = [_suggestion_card(session, s, module.name) for s in open_suggestions]

        outputs = session.exec(
            select(Output).where(Output.module_id == module.id).order_by(Output.order_index)
        ).all()
        output_views = [
            OutputView(
                id=o.id, title=o.title, state=o.state, by=o.by, when=o.when_label,
                items=json.loads(o.items or "[]"),
            )
            for o in outputs
        ]

        accounts = session.exec(
            select(SocialAccount).where(SocialAccount.module_id == module.id)
        ).all()
        account_views = [
            AccountView(id=a.id, channel=a.channel, state=a.state, handle=a.handle)
            for a in accounts
        ]

        module_views.append(
            ModuleView(
                id=module.id,
                name=module.name,
                role_key=module.role_key,
                order_index=module.order_index,
                status=module.status,
                score=module.score,
                threshold=module.threshold,
                model_key=module.model_key,
                task=module.task,
                task_note=module.task_note,
                mounted_skills=mounted_names,
                open_suggestions=cards,
                outputs=output_views,
                accounts=account_views,
            )
        )

    return BoardView(
        project_id=project.id,
        project_name=project.name,
        project_type=project.type,
        project_status=project.status,
        category=project.category,
        cat_key=project.cat_key,
        stage=project.stage,
        tags=json.loads(project.tags or "[]"),
        trend=json.loads(project.trend or "[]"),
        health=_project_health(session, project.id),
        modules=module_views,
    )


# --------------------------------------------------------------------------- #
# API                                                                          #
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/overview", response_model=OverviewView)
def overview(session: Session = Depends(get_session)):
    """左欄 + HUD 用:全部案子摘要、分類、系統讀數。"""
    projects = session.exec(select(Project).order_by(Project.id)).all()

    CAT_NAMES = {"money": "記帳工具", "internal": "內部工具", "client": "客戶委託", "other": "其他"}
    summaries: list[ProjectSummary] = []
    for p in projects:
        summaries.append(
            ProjectSummary(
                id=p.id, name=p.name, category=p.category, cat_key=p.cat_key,
                type=p.type, stage=p.stage, tags=json.loads(p.tags or "[]"),
                health=_project_health(session, p.id), alerts=_pending_count(session, p.id),
            )
        )

    # 分類:全部 + 實際出現過的分類鍵(照固定順序)
    present = {p.cat_key for p in projects}
    order = ["money", "internal", "client", "other"]
    categories = [CategoryView(key="all", name="全部案子", count=len(projects))]
    for key in order:
        if key in present:
            categories.append(
                CategoryView(
                    key=key,
                    name=CAT_NAMES.get(key, key),
                    count=sum(1 for p in projects if p.cat_key == key),
                )
            )

    total = len(summaries)
    avg = round(sum(s.health for s in summaries) / total) if total else 0
    pending = sum(s.alerts for s in summaries)
    return OverviewView(
        categories=categories,
        projects=summaries,
        hud=HudView(project_count=total, avg_health=avg, pending=pending),
    )


@app.post("/api/projects", response_model=BoardView)
def create_project(req: CreateProjectRequest, session: Session = Depends(get_session)):
    project = services.create_project(
        session, req.name, req.type, req.tags, req.category, req.cat_key
    )
    return _build_board(session, project)


@app.get("/api/projects/{project_id}/board", response_model=BoardView)
def get_board(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="找不到這個案子")
    return _build_board(session, project)


def _board_for_module(session: Session, module_id: int) -> BoardView:
    module = session.get(Module, module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="找不到這個模組")
    return _build_board(session, session.get(Project, module.project_id))


@app.post("/api/suggestions/{suggestion_id}/adopt", response_model=BoardView)
def adopt(suggestion_id: int, session: Session = Depends(get_session)):
    try:
        ps = services.adopt_suggestion(session, suggestion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _build_board(session, session.get(Project, ps.project_id))


@app.post("/api/suggestions/{suggestion_id}/skip", response_model=BoardView)
def skip(suggestion_id: int, session: Session = Depends(get_session)):
    try:
        s = services.skip_suggestion(session, suggestion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _build_board(session, session.get(Project, s.project_id))


@app.post("/api/modules/{module_id}/score", response_model=BoardView)
def update_score(
    module_id: int, req: UpdateScoreRequest, session: Session = Depends(get_session)
):
    try:
        services.update_score(session, module_id, req.value, req.speed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _board_for_module(session, module_id)


@app.post("/api/modules/{module_id}/model", response_model=BoardView)
def set_model(
    module_id: int, req: SetModelRequest, session: Session = Depends(get_session)
):
    try:
        services.set_module_model(session, module_id, req.model_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _board_for_module(session, module_id)


@app.post("/api/modules/{module_id}/task", response_model=BoardView)
def set_task(
    module_id: int, req: SetTaskRequest, session: Session = Depends(get_session)
):
    try:
        services.set_module_task(session, module_id, req.task, req.task_note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _board_for_module(session, module_id)


@app.post("/api/modules/{module_id}/channels", response_model=BoardView)
def toggle_channel(
    module_id: int, req: ToggleChannelRequest, session: Session = Depends(get_session)
):
    try:
        services.toggle_channel(session, module_id, req.channel)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _board_for_module(session, module_id)


@app.post("/api/accounts/{account_id}/apply", response_model=BoardView)
def apply_account(account_id: int, session: Session = Depends(get_session)):
    account = session.get(SocialAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="找不到這個帳號")
    module = session.get(Module, account.module_id)
    project = session.get(Project, module.project_id)
    try:
        services.apply_account(session, account_id, project.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _build_board(session, project)


@app.post("/api/outputs/{output_id}/review", response_model=BoardView)
def review_output(
    output_id: int, req: ReviewOutputRequest, session: Session = Depends(get_session)
):
    output = session.get(Output, output_id)
    if output is None:
        raise HTTPException(status_code=404, detail="找不到這筆產出")
    try:
        services.review_output(session, output_id, req.decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _board_for_module(session, output.module_id)


@app.get("/api/skills")
def list_skills(session: Session = Depends(get_session)) -> list[dict]:
    """工作台層用:完整能力目錄。"""
    skills = session.exec(select(Skill)).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "role_key": s.role_key,
            "risk_level": s.risk_level,
            "conflict_group": s.conflict_group,
            "content": s.content,
        }
        for s in skills
    ]
