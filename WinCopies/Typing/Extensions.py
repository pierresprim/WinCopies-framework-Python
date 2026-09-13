from abc import abstractmethod
from typing import Iterable

from WinCopies.Collections.Generation.Buffering import IGroupBuilder, GroupBuilder
from WinCopies.Collections.Util import MakeSequence

class IExceptionGroupBuilder(IGroupBuilder[Exception, ExceptionGroup]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryThrow(self) -> None:
        ...
class ExceptionGroupBuilder(GroupBuilder[Exception, ExceptionGroup], IExceptionGroupBuilder):
    def __init__(self) -> None: super().__init__()

    def _CreateList(self, items: Iterable[Exception]) -> ExceptionGroup[Exception]: return ExceptionGroup("Multiple exceptions occurred.", MakeSequence(*items))

    def _AsContainer(self, container: ExceptionGroup[Exception]) -> Exception: return container

    def TryThrow(self) -> None:
        exception: Exception|None = self.TryBuildGroup().TryGetValue()
        
        if exception is not None: raise exception