from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from .metrics import (CommitMetrics, MetricsBody, metrics_get, metrics_list,
                      metrics_post, repo)
from .session import get_session


def valid_session(request: Request):
    session = get_session(request)
    if session.state != 'normal':
        raise HTTPException(status_code=403)


router = APIRouter(prefix='/api', dependencies=[Depends(valid_session)])

REF_NOT_FOUND_MSG = 'ref not found'


@router.get('/update_git')
def update_git():
    repo.update()


@router.get('/branches')
def branches() -> List[str]:
    return list(repo.branches())


@router.get('/metrics')
def api_metrics_list(ref: str) -> Optional[List[CommitMetrics]]:
    result = metrics_list(ref)
    if result is None:
        raise HTTPException(status_code=404,
                            detail=f'Unable to fetch commits for {ref}')
    return result


@router.get('/metrics/{ref}')
def api_metrics_get(ref: str) -> Optional[CommitMetrics]:
    result = metrics_get(ref)
    if result is None:
        raise HTTPException(404, REF_NOT_FOUND_MSG)
    return result


@router.post('/metrics/{ref}')
def api_metrics_post(ref: str, body: MetricsBody):
    if metrics_post(ref, body) is None:
        raise HTTPException(404, REF_NOT_FOUND_MSG)
