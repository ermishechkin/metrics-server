from os import makedirs, path

import uvicorn

from . import settings
from .metrics import repo
from .web import get_base_url

if __name__ == '__main__':
    makedirs(path.abspath(settings.STORAGE_PATH), exist_ok=True)
    repo.update()
    uvicorn.run(
        'metrics_server.server:app',
        host=settings.LISTEN_HOST,
        port=settings.LISTEN_PORT,
        workers=settings.WORKERS,
        root_path=get_base_url(),
    )
