from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter

from .session import get_session_by_id, sessions_storage, set_session

router = APIRouter(prefix='/admin/api')


@dataclass
class SessionInfo:
    user: str
    expired_in: int


@dataclass
class SidInfo:
    sid: str


@router.get('/session')
def admin_session_get(sid: str) -> Optional[SessionInfo]:
    session = get_session_by_id(sid)
    if session is None or session.user is None:
        return None
    return SessionInfo(user=session.user, expired_in=session.expired_in)


@router.post('/session')
def admin_session_post(session: SessionInfo) -> SidInfo:
    sid = set_session(user=session.user, expired_in=session.expired_in)
    return SidInfo(sid=sid)


@router.delete('/session')
def admin_session_delete(sid: str) -> None:
    sessions_storage.delete(sid)
