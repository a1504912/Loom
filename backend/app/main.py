"""FastAPI 入口 — 提供建立案子、看板、採用/略過、健康度更新 API。"""

from __future__ import annotations

import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from . import services
from .db import create_db_and_tables, engine, get_session
from .models import Module, Project, ProjectSkill, Skill, Suggestion
from .schemas import (
    BoardView,
    CreateProjectRequest,
    ModuleView,
    SuggestionCard,
    UpdateScoreRequest,
)
from .seed import seed_skills

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
        seed_skills(session)


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
    modules = session.exec(
        select(Module).where(Module.project_id == project.id).order_by(Module.order_index)
    ).all()

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

        module_views.append(
            ModuleView(
                id=module.id,
                name=module.name,
                role_key=module.role_key,
                order_index=module.order_index,
                status=module.status,
                score=module.score,
                threshold=module.threshold,
                mounted_skills=mounted_names,
                open_suggestions=cards,
            )
        )

    tags = json.loads(project.tags or "[]")
    return BoardView(
        project_id=project.id,
        project_name=project.name,
        project_type=project.type,
        project_status=project.status,
        tags=tags,
        modules=module_views,
    )


# --------------------------------------------------------------------------- #
# API                                                                          #
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/projects", response_model=BoardView)
def create_project(req: CreateProjectRequest, session: Session = Depends(get_session)):
    project = services.create_project(session, req.name, req.type, req.tags)
    return _build_board(session, project)


@app.get("/api/projects")
def list_projects(session: Session = Depends(get_session)) -> list[dict]:
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "status": p.status,
            "tags": json.loads(p.tags or "[]"),
        }
        for p in projects
    ]


@app.get("/api/projects/{project_id}/board", response_model=BoardView)
def get_board(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="找不到這個案子")
    return _build_board(session, project)


@app.post("/api/suggestions/{suggestion_id}/adopt", response_model=BoardView)
def adopt(suggestion_id: int, session: Session = Depends(get_session)):
    try:
        ps = services.adopt_suggestion(session, suggestion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    project = session.get(Project, ps.project_id)
    return _build_board(session, project)


@app.post("/api/suggestions/{suggestion_id}/skip", response_model=BoardView)
def skip(suggestion_id: int, session: Session = Depends(get_session)):
    try:
        s = services.skip_suggestion(session, suggestion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    project = session.get(Project, s.project_id)
    return _build_board(session, project)


@app.post("/api/modules/{module_id}/score", response_model=BoardView)
def update_score(
    module_id: int, req: UpdateScoreRequest, session: Session = Depends(get_session)
):
    try:
        services.update_score(session, module_id, req.value, req.speed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    module = session.get(Module, module_id)
    project = session.get(Project, module.project_id)
    return _build_board(session, project)


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
