from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Delegates import GetMethodAsFunction
from WinCopies.Enums import ErrorMessages
from WinCopies.String import GetValueOrDefault
from WinCopies.Typing import InvalidOperationError, GetUnexpectedError
from WinCopies.Typing.Delegate import Action, Function, Converter

class IWorker(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsBusy(self) -> bool:
        ...
class IMonitor(IWorker, IDisposable):
    def __init__(self) -> None: super().__init__()
class Monitor(Abstract, IMonitor):
    def __init__(self) -> None:
        super().__init__()

        self.__isBusy: bool = False
    
    @final
    def Initialize(self) -> None: self.__isBusy = True
    
    @final
    def IsBusy(self) -> bool: return self.__isBusy
    
    @final
    def Dispose(self) -> None: self.__isBusy = False

def __CheckMonitor(monitor: IMonitor, errorMessage: str|ErrorMessages|None = None) -> None:
    if monitor.IsBusy(): raise InvalidOperationError(GetValueOrDefault(errorMessage, "The given monitor is already busy."))

def DoWork(monitor: IMonitor, worker: Action, errorMessage: str|ErrorMessages|None = None) -> None:
    __CheckMonitor(monitor, errorMessage)

    with monitor: worker()
def Process[T](monitor: IMonitor, worker: Function[T], errorMessage: str|ErrorMessages|None = None) -> T:
    __CheckMonitor(monitor, errorMessage)
    
    with monitor: return worker()

    raise GetUnexpectedError()
def ProcessData[TIn, TOut](data: TIn, monitor: IMonitor, worker: Converter[TIn, TOut], errorMessage: str|ErrorMessages|None = None) -> TOut:
    return Process(monitor, GetMethodAsFunction(data, worker), errorMessage)