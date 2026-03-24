"""
Memory 模块 - 会话记忆管理
支持短期记忆和 SQLite 持久化
"""
import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class Message:
    """单条消息"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_calls: Optional[List[Dict]] = None


@dataclass
class Session:
    """会话"""
    session_id: str
    created_at: str
    updated_at: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [asdict(m) for m in self.messages],
            "metadata": self.metadata,
        }


class Memory:
    """
    记忆管理器
    - 短期记忆：当前会话的消息列表
    - 长期记忆：SQLite 数据库持久化
    """
    
    def __init__(self, db_path: str = "data/sessions/bioagent.db"):
        self.db_path = db_path
        self._init_db()
        
        # 当前会话
        self.current_session: Optional[Session] = None
        self.short_term_memory: List[Message] = []
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tool_calls TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: Optional[str] = None, metadata: Dict = None) -> Session:
        """创建新会话"""
        now = datetime.now().isoformat()
        session_id = session_id or str(uuid.uuid4())
        
        session = Session(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata or {}
        )
        
        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO sessions (session_id, created_at, updated_at, metadata) VALUES (?, ?, ?, ?)",
            (session_id, now, now, json.dumps(session.metadata))
        )
        
        conn.commit()
        conn.close()
        
        self.current_session = session
        self.short_term_memory = []
        
        return session
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """加载会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取会话信息
        cursor.execute(
            "SELECT session_id, created_at, updated_at, metadata FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        session_id, created_at, updated_at, metadata_json = row
        metadata = json.loads(metadata_json or "{}")
        
        # 获取消息
        cursor.execute(
            "SELECT role, content, timestamp, tool_calls FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,)
        )
        
        messages = []
        for role, content, timestamp, tool_calls_json in cursor.fetchall():
            tool_calls = json.loads(tool_calls_json) if tool_calls_json else None
            messages.append(Message(
                role=role,
                content=content,
                timestamp=timestamp,
                tool_calls=tool_calls
            ))
        
        conn.close()
        
        session = Session(
            session_id=session_id,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            metadata=metadata
        )
        
        self.current_session = session
        self.short_term_memory = messages.copy()
        
        return session
    
    def save_message(self, role: str, content: str, tool_calls: Optional[List[Dict]] = None):
        """保存消息"""
        now = datetime.now().isoformat()
        
        message = Message(
            role=role,
            content=content,
            timestamp=now,
            tool_calls=tool_calls
        )
        
        # 添加到短期记忆
        self.short_term_memory.append(message)
        
        # 如果有当前会话，保存到数据库
        if self.current_session:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, timestamp, tool_calls) VALUES (?, ?, ?, ?, ?)",
                (
                    self.current_session.session_id,
                    role,
                    content,
                    now,
                    json.dumps(tool_calls) if tool_calls else None
                )
            )
            
            # 更新会话时间
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, self.current_session.session_id)
            )
            
            conn.commit()
            conn.close()
            
            self.current_session.messages.append(message)
    
    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """获取最近 N 条消息"""
        return self.short_term_memory[-n:]
    
    def clear_short_term(self):
        """清除短期记忆"""
        self.short_term_memory = []
    
    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """列出最近会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT session_id, created_at, updated_at, metadata FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        
        sessions = []
        for session_id, created_at, updated_at, metadata_json in cursor.fetchall():
            sessions.append({
                "session_id": session_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "metadata": json.loads(metadata_json or "{}")
            })
        
        conn.close()
        return sessions
    
    def delete_session(self, session_id: str):
        """删除会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session = None
            self.short_term_memory = []
