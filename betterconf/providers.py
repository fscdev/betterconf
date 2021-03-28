from configparser import ConfigParser
from typing import Union, Any, Tuple, List, Sequence, Callable, IO

import toml
import os

DEFAULT_PROVIDER = EnvironmentProvider()

TOMLLoadFunction = Callable[[Union[str, list, IO[str]]], dict]


class AbstractProvider:
    """Implement this class and pass to `field`"""

    def get(self, name: str) -> Any:
        """Return a value or None"""
        raise NotImplementedError()


class EnvironmentProvider(AbstractProvider):
    """Default provider. Gets vals from environment"""

    def get(self, name: str) -> Any:
        return os.getenv(name)


class INIProvider(AbstractProvider):
    """Provider that gets values from .INI files"""

    def __init__(
        self,
        files: Union[str, List[str]],
        delimiters: Sequence[str] = ("=", ":"),
        comment_prefixes: Sequence[str] = ("#", ";"),
        section: str = "config"
    ):
        self.cfg = ConfigParser(
            delimiters=delimiters, comment_prefixes=comment_prefixes
        )
        if isinstance(files, str):
            files = [files]
        self.cfg.read(files)
        self.section = section

    def get(self, name: str) -> str:
        return self.cfg.get(self.section, name)


class TOMLProvider(AbstractProvider):
    """Provider that gets values from .TOML files"""

    def __init__(self, load: TOMLLoadFunction, files: Union[str, List[str]]):
        self.data = load(files)

    def get(self, name: str) -> Any:
        return self.data[name]
