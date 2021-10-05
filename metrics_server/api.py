from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from .metrics import (CommitMetrics, MetricsBody, metrics_get, metrics_list,
                      metrics_post, repo)
from .session import Session, get_session_with_token


def valid_session_with_token(
        session: Optional[Session] = Depends(get_session_with_token)):
    if session is None:
        raise HTTPException(status_code=403)
    return session


router = APIRouter(
    prefix='/api',
    dependencies=[Depends(valid_session_with_token)],
)

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
