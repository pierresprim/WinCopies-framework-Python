from __future__ import annotations

from typing import final

from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater

@final
class __DefaultFunction(IFunction[None]):
    def __init__(self):
        super().__init__()
    
    def GetValue(self) -> None:
        return None

@final
class __ValueFunctionUpdater(ValueFunctionUpdater[IFunction[None]]):
    def __init__(self, updater: Method[IFunction[IFunction[None]]]):
        super().__init__(updater)
    
    def _GetValue(self) -> IFunction[None]:
        return __DefaultFunction()

__getDefaultFunction: IFunction[__DefaultFunction]|None = None

def __updateDefaultFunction(function: IFunction[None]):
    global __getDefaultFunction

    __getDefaultFunction = function

__getDefaultFunction = __ValueFunctionUpdater(__updateDefaultFunction)

def GetDefaultFunction() -> IFunction[None]:
    return __getDefaultFunction()