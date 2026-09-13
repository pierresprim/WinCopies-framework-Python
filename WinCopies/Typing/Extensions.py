
from typing import Iterable

from WinCopies.Collections.Generation.Buffering import IAbstractionBuilder, AbstractionBuilder
from WinCopies.Collections.Util import MakeSequence

class IExceptionGroupBuilder(IAbstractionBuilder[Exception, ExceptionGroup]):
    def __init__(self) -> None: super().__init__()
class ExceptionGroupBuilder(AbstractionBuilder[Exception, ExceptionGroup], IExceptionGroupBuilder):
    def __init__(self) -> None: super().__init__()

    def _CreateList(self, items: Iterable[Exception]) -> ExceptionGroup[Exception]:
        return ExceptionGroup("Multiple exceptions occurred.", MakeSequence(*items))