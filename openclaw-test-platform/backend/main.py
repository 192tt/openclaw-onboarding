"""FastAPI 后端主入口"""
import json
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import init_db, get_db, UserCard
from skill_logic import process_message, restart_session, generate_card, SessionState

app = FastAPI(title="OpenClaw 数字身份注册平台", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# ============ API 模型 ============

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    messages: list
    progress: int = 0
    card: Optional[dict] = None
    done: bool = False

class RestartRequest(BaseModel):
    session_id: Optional[str] = None

class CardSyncRequest(BaseModel):
    nickname: str
    avatar: Optional[str] = ""
    role: str
    city: str
    slogan: str
    tracks: Optional[str] = ""
    coop_types: Optional[str] = ""
    role_data: Optional[Dict] = {}
    tags: Optional[list] = []
    card_data: Optional[Dict] = {}

# ============ API 路由 ============

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    sid = req.session_id or str(uuid.uuid4())
    result = process_message(sid, req.message)
    
    # 如果完成，保存到数据库
    if result.get("done") and result.get("card"):
        _save_card_to_db(result["card"], db)
    
    return ChatResponse(
        session_id=sid,
        messages=result.get("messages", []),
        progress=result.get("progress", 0),
        card=result.get("card"),
        done=result.get("done", False)
    )

@app.post("/api/restart")
def restart(req: RestartRequest):
    sid = req.session_id or str(uuid.uuid4())
    result = restart_session(sid)
    return ChatResponse(
        session_id=sid,
        messages=result.get("messages", []),
        progress=result.get("progress", 0),
        done=result.get("done", False)
    )

@app.get("/api/cards")
def list_cards(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    cards = db.query(UserCard).order_by(UserCard.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": c.id,
            "nickname": c.nickname,
            "role": c.role,
            "city": c.city,
            "slogan": c.slogan,
            "tracks": c.tracks,
            "tags": json.loads(c.tags) if c.tags else [],
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in cards
    ]

@app.get("/api/cards/{card_id}")
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(UserCard).filter(UserCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {
        "id": card.id,
        "nickname": card.nickname,
        "avatar": card.avatar,
        "role": card.role,
        "city": card.city,
        "slogan": card.slogan,
        "tracks": card.tracks,
        "coop_types": card.coop_types,
        "role_data": json.loads(card.role_data) if card.role_data else {},
        "tags": json.loads(card.tags) if card.tags else [],
        "card_data": json.loads(card.card_data) if card.card_data else {},
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }

# ============ OpenClaw 同步端点 ============

def _save_card_to_db(card_data: dict, db: Session) -> UserCard:
    """保存或更新卡片到数据库"""
    existing = db.query(UserCard).filter(
        UserCard.nickname == card_data["nickname"]
    ).first()
    
    card_json = json.dumps(card_data, ensure_ascii=False)
    tags_json = json.dumps([t["text"] if isinstance(t, dict) else t for t in card_data.get("tags", [])], ensure_ascii=False)
    role_data_json = json.dumps(card_data.get("role_data", {}), ensure_ascii=False)
    
    if existing:
        existing.avatar = card_data.get("avatar", "")
        existing.role = card_data.get("role", "")
        existing.city = card_data.get("city", "")
        existing.slogan = card_data.get("slogan", "")
        existing.tracks = card_data.get("tracks", "")
        existing.coop_types = card_data.get("coop_types", "")
        existing.role_data = role_data_json
        existing.tags = tags_json
        existing.card_data = card_json
        existing.updated_at = datetime.utcnow()
        card = existing
    else:
        card = UserCard(
            nickname=card_data["nickname"],
            avatar=card_data.get("avatar", ""),
            role=card_data.get("role", ""),
            city=card_data.get("city", ""),
            slogan=card_data.get("slogan", ""),
            tracks=card_data.get("tracks", ""),
            coop_types=card_data.get("coop_types", ""),
            role_data=role_data_json,
            tags=tags_json,
            card_data=card_json,
        )
        db.add(card)
    
    db.commit()
    db.refresh(card)
    return card

@app.post("/api/cards/sync")
def sync_card(req: CardSyncRequest, db: Session = Depends(get_db)):
    """接收 OpenClaw 推送的卡片数据"""
    card_data = req.model_dump()
    card = _save_card_to_db(card_data, db)
    return {
        "success": True,
        "id": card.id,
        "message": f"卡片 '{card.nickname}' 已同步到平台",
        "url": f"http://124.220.221.242:8000"
    }

# ============ 静态文件 ============

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{path:path}")
def catch_all(path: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# ============ 启动 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
