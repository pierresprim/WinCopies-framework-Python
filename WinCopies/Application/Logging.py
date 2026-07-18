import sys

from abc import abstractmethod
from enum import Enum
from logging import Logger as LoggerBase, Formatter, StreamHandler, getLogger, NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
from typing import final, TextIO

from WinCopies import IInterface, Abstract
from WinCopies.Typing.Delegate import Method

class Level(Enum):
    Null = NOTSET
    Debug = DEBUG
    Info = INFO
    Warning = WARNING
    Error = ERROR
    Critical = CRITICAL

class ILogger(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def SetVerbosity(self, verbose: bool = False) -> None: ...
    @abstractmethod
    def SetLevel(self, level: Level = Level.Info) -> None: ...

    @abstractmethod
    def Write(self, level: Level, msg: str) -> None: ...
class Logger(Abstract, ILogger):
    def __init__(self, name: str) -> None:
        super().__init__()

        log: LoggerBase = getLogger(name)
        
        handler: StreamHandler[TextIO] = StreamHandler[TextIO](sys.stderr)

        handler.setFormatter(Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        log.addHandler(handler)

        self.__log: LoggerBase = log
    
    @final
    def _GetLog(self) -> LoggerBase:
        return self.__log
    
    @final
    def SetVerbosity(self, verbose: bool = False) -> None:
        self._GetLog().setLevel(DEBUG if verbose else INFO)
    @final
    def SetLevel(self, level: Level = Level.Info) -> None:
        self._GetLog().setLevel(level.value)
    
    @final
    def Write(self, level: Level, msg: str) -> None:
        def map(log: LoggerBase) -> Method[str]:
            match level:
                case Level.Debug: return log.debug
                case Level.Info: return log.info
                case Level.Warning: return log.warning
                case Level.Error: return log.error
                case Level.Critical: return log.critical

                case _: raise ValueError()
        
        map(self._GetLog())(msg)