import json
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any, Awaitable, Callable, Dict, Literal, Optional

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


def get_session(request: Request) -> Session:
    sid = request.cookies.get(settings.SESSION_COOKIE)

    if sid is not None:
        value_in = sessions_storage.get(sid)
    else:
        value_in = None

    if sid is None or value_in is None:
        sid = secrets.token_hex(16)
        dbval = _SessionInternal(
            None,
            int(time.time()) + settings.SESSION_EXPIRE_IN,
            {},
        )
        sessions_storage.set(sid, json.dumps(asdict(dbval)))
    else:
        dbval = _SessionInternal(**json.loads(value_in))

    value = Session.from_storage(dbval)
    request.scope[_SCOPE_SESSION_INITIAL] = dbval  # type: ignore
    request.scope[_SCOPE_SESSION] = value  # type: ignore
    request.scope[_SCOPE_SID] = sid  # type: ignore

    return value


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
