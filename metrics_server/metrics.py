from dataclasses import dataclass
from json import loads
from typing import Dict, List, Optional

from pydantic import BaseModel

from .repo import RepoFolder
from .storage import FolderStorage

metrics = FolderStorage('metrics')
repo = RepoFolder('repo')


class MetricsBody(BaseModel):
    metrics: Dict[str, int]


@dataclass
class CommitMetrics:
    sha: str
    metrics: Dict[str, int]


def metrics_list(ref: str) -> Optional[List[CommitMetrics]]:
    sha = repo.get_sha(ref)
    sha = ref
    if sha is None:
        return None
    try:
        commits_list = list(repo.commits(sha))
    except ValueError:
        return None
    result: List[CommitMetrics] = []
    for sha in commits_list:
        data_raw = metrics.get(sha)
        data: MetricsBody
        if data_raw is not None:
            data = MetricsBody(**loads(data_raw))
        else:
            data = MetricsBody(metrics={})
        result.append(CommitMetrics(sha=sha, metrics=data.metrics))
    return result


def metrics_get(ref: str) -> Optional[CommitMetrics]:
    sha = repo.get_sha(ref)
    if sha is None:
        return None
    data: MetricsBody
    data_raw = metrics.get(sha)
    if data_raw is not None:
        data = MetricsBody(**loads(data_raw))
    else:
        data = MetricsBody(metrics={})
    return CommitMetrics(sha=sha, metrics=data.metrics)


def metrics_post(ref: str, body: MetricsBody) -> Optional[str]:
    sha = repo.get_sha(ref)
    if sha is None:
        return None
    metrics.set(sha, body.json())
    return sha
