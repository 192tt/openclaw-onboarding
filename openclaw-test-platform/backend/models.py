"""数据模型"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class UserCard(Base):
    __tablename__ = "user_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(100), nullable=False)
    avatar = Column(Text, default="")
    role = Column(String(50), nullable=False)  # founder / investor / incubator / enterprise
    city = Column(String(100), nullable=False)
    slogan = Column(String(500), nullable=False)
    tracks = Column(Text, default="")  # 逗号分隔
    coop_types = Column(Text, default="")  # 逗号分隔
    
    # 角色专属字段（JSON 字符串）
    role_data = Column(Text, default="{}")
    
    # 自动生成的标签
    tags = Column(Text, default="")
    
    # 卡片展示数据（完整卡片 JSON）
    card_data = Column(Text, default="{}")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "openclaw.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite 数据库
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
