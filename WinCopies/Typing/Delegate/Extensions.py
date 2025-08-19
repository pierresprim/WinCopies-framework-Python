from __future__ import annotations

from typing import final

from WinCopies.Typing.Delegate import IFunction

@final
class __DefaultFunction(IFunction[None]):
    def __init__(self):
        super().__init__()
    
    def GetValue(self) -> None:
        return None

__getDefaultFunction: IFunction[None] = __DefaultFunction()

def GetDefaultFunction() -> IFunction[None]:
    return __getDefaultFunction