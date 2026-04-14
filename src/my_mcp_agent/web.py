from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .agent import chat
from .config import APP_NAME
from .memory import (
    get_memory_by_id,
    maybe_upsert_memory,
    recent_memories,
    update_memory,
    delete_memory,
)
from .profile import get_profile, set_profile

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": get_profile(),
            "memories": recent_memories(20),
            "result": None,
            "message": "",
        },
    )


@app.post("/chat", response_class=HTMLResponse)
def chat_route(request: Request, message: str = Form(...)):
    result = chat(message)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profile": get_profile(),
            "memories": recent_memories(20),
            "result": result.model_dump(),
            "message": message,
        },
    )


@app.post("/profile")
def update_profile_route(key: str = Form(...), value: str = Form(...)):
    set_profile(key.strip(), value.strip())
    return RedirectResponse(url="/", status_code=303)


@app.get("/memories", response_class=HTMLResponse)
def memories_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="memories.html",
        context={
            "memories": recent_memories(200),
            "editing": None,
        },
    )


@app.get("/memories/{memory_id}", response_class=HTMLResponse)
def edit_memory_page(request: Request, memory_id: int):
    return templates.TemplateResponse(
        request=request,
        name="memories.html",
        context={
            "memories": recent_memories(200),
            "editing": get_memory_by_id(memory_id),
        },
    )


@app.post("/memories/add")
def add_memory_route(
    text: str = Form(...),
    memory_type: str = Form(...),
    tags: str = Form(""),
    confidence: float = Form(0.85),
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    maybe_upsert_memory(
        text=text.strip(),
        memory_type=memory_type.strip(),
        tags=tag_list,
        confidence=confidence,
    )
    return RedirectResponse(url="/memories", status_code=303)


@app.post("/memories/{memory_id}/update")
def update_memory_route(
    memory_id: int,
    text: str = Form(...),
    memory_type: str = Form(...),
    tags: str = Form(""),
    confidence: float = Form(0.85),
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    update_memory(
        memory_id=memory_id,
        text=text.strip(),
        memory_type=memory_type.strip(),
        tags=tag_list,
        confidence=confidence,
    )
    return RedirectResponse(url="/memories", status_code=303)


@app.post("/memories/{memory_id}/delete")
def delete_memory_route(memory_id: int):
    delete_memory(memory_id)
    return RedirectResponse(url="/memories", status_code=303)
