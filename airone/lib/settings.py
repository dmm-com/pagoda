from collections.abc import ValuesView
from typing import Any


class Settings(object):
    def __init__(self, conf: dict[str, Any] = {}) -> None:
        self.conf = conf

    def __getattr__(self, key: str) -> Any:
        return self.conf[key]

    def __contains__(self, key: object) -> bool:
        return key in self.conf

    def values(self) -> ValuesView[Any]:
        return self.conf.values()
