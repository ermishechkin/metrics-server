from typing import Dict, Optional, cast

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.integration import \
    StarletteRemoteApp
from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from . import settings
from .session import Session, get_session

router = APIRouter(prefix='/oauth', default_response_class=HTMLResponse)
oauth = OAuth()


async def normalize_userinfo(
    _,
    data: Dict[str, str],
) -> Dict[str, Optional[str]]:
    return {
        'nickname': str(data[settings.OAUTH_USERINFO_NAME]),
    }


oauth_client: StarletteRemoteApp = cast(
    StarletteRemoteApp,
    oauth.register(
        name='custom',
        client_id=settings.OAUTH_CLIENT_ID,
        client_secret=settings.OAUTH_CLIENT_SECRET,
        access_token_url=settings.OAUTH_ACCESS_TOKEN_URL,
        authorize_url=settings.OAUTH_AUTHORIZE_URL,
        client_kwargs={
            'code_challenge_method': 'S256',
            'scope': settings.OAUTH_SCOPE,
        },
        userinfo_endpoint=settings.OAUTH_USERINFO_URL,
        userinfo_compliance_fix=normalize_userinfo,
    ))


def get_referer(request: Request) -> Optional[str]:
    return request.headers.get('Referer')


@router.get('/login')
async def login_via_oauth(request: Request,
                          session: Session = Depends(get_session),
                          referer: Optional[str] = Depends(get_referer)):
    request.scope['session'] = session.oauth_data = {
        'internal_redirect': referer,
    }
    redirect_uri = request.url_for('auth_via_oauth')
    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get('/callback')
async def auth_via_oauth(request: Request,
                         session: Session = Depends(get_session)):
    request.scope['session'] = session.oauth_data
    referer = session.oauth_data.pop('internal_redirect')
    token = await oauth_client.authorize_access_token(request)
    user = await oauth_client.userinfo(token=token)
    session.state = 'normal'
    session.user = user['nickname']
    if referer is not None:
        return RedirectResponse(url=referer)
    return 'Successfull login'


@router.get('/logout')
async def logout(session: Session = Depends(get_session),
                 referer: Optional[str] = Depends(get_referer)):
    if session.user is None:
        raise HTTPException(403)
    session.state = 'logout'
    if referer:
        return RedirectResponse(url=referer)
    return 'Successfull logout'
