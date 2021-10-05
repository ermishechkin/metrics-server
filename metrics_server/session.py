import json
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any, Awaitable, Callable, Dict, Literal, Optional, Tuple

from fastapi import Request, Response

from . import settings
from .storage import SqlStorage

_SCOPE_SID = '_user_session_id'
_SCOPE_SESSION_INITIAL = '_user_session_initial'
_SCOPE_SESSION = '_user_session_value'

sessions_storage = SqlStorage('sessions')


@dataclass
class _SessionInternal:
    u: Optional[str]
    e: int
    o: Dict[str, Optional[str]]


@dataclass
class Session:
    state: Literal['logging_in', 'normal', 'logout']
    user: Optional[str]
    expired_in: int
    oauth_data: Dict[str, Optional[str]]

    @staticmethod
    def from_storage(data: _SessionInternal) -> 'Session':
        state = 'normal' if data.u is not None else 'logging_in'
        return Session(state, data.u, data.e, data.o)

    def to_storage(self) -> _SessionInternal:
        return _SessionInternal(self.user, self.expired_in, self.oauth_data)


def create_session() -> Tuple[str, Session]:
    sid = secrets.token_hex(16)
    dbval = _SessionInternal(
        None,
        int(time.time()) + settings.SESSION_EXPIRE_IN,
        {},
    )
    sessions_storage.set(sid, json.dumps(asdict(dbval)))
    return sid, Session.from_storage(dbval)


def get_session_with_token(request: Request,
                           token: Optional[str] = None) -> Optional[Session]:
    if token is not None:
        token_session = get_session_by_id(token)
        if token_session is not None and token_session.state == 'normal':
            return token_session

    sid = request.cookies.get(settings.SESSION_COOKIE)
    if sid is None:
        return None

    cookie_session = get_session_by_id(sid)
    if cookie_session is not None and cookie_session.state == 'normal':
        return cookie_session

    return None


def get_session(request: Request) -> Session:
    sid = request.cookies.get(settings.SESSION_COOKIE)

    if sid is not None:
        value_in = get_session_by_id(sid)
    else:
        value_in = None

    if value_in is None:
        sid, value = create_session()
    else:
        value = value_in

    dbval = value.to_storage()
    request.scope[_SCOPE_SESSION_INITIAL] = dbval  # type: ignore
    request.scope[_SCOPE_SESSION] = value  # type: ignore
    request.scope[_SCOPE_SID] = sid  # type: ignore

    return value


def get_session_by_id(sid: str) -> Optional[Session]:
    raw_value = sessions_storage.get(sid)
    if raw_value is None:
        return None
    dbval = _SessionInternal(**json.loads(raw_value))
    if 0 < dbval.e <= time.time():
        sessions_storage.delete(sid)
        return None
    return Session.from_storage(dbval)


def set_session(user: str, expired_in: int) -> str:
    sid = secrets.token_hex(16)
    dbval = _SessionInternal(u=user, e=expired_in, o={})
    sessions_storage.set(sid, json.dumps(asdict(dbval)))
    return sid


async def flush_session(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    scope: Dict[str, Any] = request.scope  # type: ignore
    response = await call_next(request)
    sid: Optional[str] = scope.get(_SCOPE_SID)
    if sid is not None:
        session: Session = scope[_SCOPE_SESSION]
        if session.state == 'logout':
            sessions_storage.delete(sid)
            response.delete_cookie(settings.SESSION_COOKIE)
        else:
            new_session_internal = session.to_storage()
            prev_session_internal: _SessionInternal = (
                request.scope[_SCOPE_SESSION_INITIAL])  # type: ignore
            if new_session_internal != prev_session_internal:
                sessions_storage.set(
                    sid,
                    json.dumps(asdict(new_session_internal)),
                )
            response.set_cookie(settings.SESSION_COOKIE, sid)
    return response
