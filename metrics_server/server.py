from fastapi import FastAPI

from .api import router as api_router
from .auth import router as auth_router
from .session import flush_session
from .web import get_base_url
from .web import router as web_router
from .web import statics_app

app = FastAPI(root_path=get_base_url())
app.middleware('http')(flush_session)

app.include_router(auth_router)
app.include_router(api_router)
app.include_router(web_router)
app.mount('/static', statics_app, name='static')
