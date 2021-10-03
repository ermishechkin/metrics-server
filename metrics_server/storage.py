from os import makedirs, path, remove
from re import compile
from sqlite3 import connect
from typing import Any, Optional

from . import settings


class BaseStorage:
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError


class FolderStorage(BaseStorage):
    def __init__(self, subdirectory: str):
        subdir = path.join(path.abspath(settings.STORAGE_PATH), subdirectory)
        makedirs(subdir, exist_ok=True)
        self._subdir = subdir

    def get(self, key: str) -> Optional[str]:
        validate_name(key)
        try:
            with open(f'{self._subdir}/{key}', 'r') as inf:
                return inf.read()
        except OSError:
            return None

    def set(self, key: str, value: Any) -> None:
        validate_name(key)
        with open(f'{self._subdir}/{key}', 'w') as inf:
            inf.write(str(value))

    def delete(self, key: str) -> None:
        validate_name(key)
        remove(f'{self._subdir}/{key}')


class SqlStorage(BaseStorage):
    def __init__(self, key: str):
        subdir = path.abspath(settings.STORAGE_PATH)
        makedirs(subdir, exist_ok=True)
        db_path = path.join(subdir, f'{key}.db')
        self._con = con = connect(db_path, check_same_thread=False)
        with con:
            con.execute('CREATE TABLE IF NOT EXISTS table1 '
                        '(key TEXT PRIMARY KEY, value TEXT)')

    def get(self, key: str) -> Optional[str]:
        validate_name(key)
        cursor = self._con.cursor()
        cursor.execute('SELECT VALUE FROM table1 WHERE key=?', (key, ))
        result = cursor.fetchone()
        if result is not None:
            result = result[0]
        return result

    def set(self, key: str, value: Any) -> None:
        validate_name(key)
        cursor = self._con.cursor()
        cursor.execute('REPLACE INTO table1 VALUES (?,?)', (key, value))
        self._con.commit()

    def delete(self, key: str) -> None:
        validate_name(key)
        cursor = self._con.cursor()
        cursor.execute('DELETE FROM table1 WHERE key=?', (key, ))
        self._con.commit()


_allowed_key = compile(r'[0-9A-Za-z]+')


def validate_name(name: str) -> None:
    if not _allowed_key.fullmatch(name):
        raise ValueError(f'Invalid key name "{name}"')
