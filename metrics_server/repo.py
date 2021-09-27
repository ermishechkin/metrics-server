from os import makedirs, path
from typing import Iterable, Optional

from git.exc import GitError
from git.objects import Object as GitObject
from git.refs import Head
from git.repo import Repo
from gitdb.exc import BadName

from . import settings


class RepoFolder:
    def __init__(self, subdirectory: str):
        storage_root = path.abspath(settings.STORAGE_PATH)
        makedirs(storage_root, exist_ok=True)
        subdir = path.join(storage_root, subdirectory)
        self._path = subdir
        self._repo = self._init_git(subdir)

    def _init_git(self, subdir: str):
        result: Repo
        if path.exists(subdir):
            result = Repo(subdir)
            result.remote('origin').set_url(settings.REPO_URL)
        else:
            result = Repo.clone_from(
                settings.REPO_URL,
                subdir,
                bare=True,
                filter='blob:none',
            )
        return result

    def update(self):
        self._repo.remote().fetch("+refs/heads/*:refs/heads/*")

    def branches(self) -> Iterable[str]:
        head: Head
        for head in self._repo.branches:
            yield head.name
        pass

    def commits(self, head: str) -> Iterable[str]:
        try:
            for commit in self._repo.iter_commits(head):
                yield commit.hexsha
        except GitError:
            raise ValueError

    def get_sha(self, ref: str) -> Optional[str]:
        try:
            obj: GitObject = self._repo.rev_parse(ref)
            return obj.hexsha
        except (GitError, BadName):
            return None
