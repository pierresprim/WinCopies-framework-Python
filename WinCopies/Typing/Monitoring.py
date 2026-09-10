from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Delegates import GetMethodAsFunction
from WinCopies.Enums import ErrorMessages
from WinCopies.String import GetValueOrDefault
from WinCopies.Typing import INullable, InvalidOperationError, GetUnexpectedError, GetNullValue, GetNullable
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

def GetMonitorBusyError(errorMessage: str|ErrorMessages|None = None) -> InvalidOperationError:
    return InvalidOperationError(GetValueOrDefault(errorMessage, "The given monitor is already busy."))
def ThrowMonitorBusyError(errorMessage: str|ErrorMessages|None = None) -> InvalidOperationError:
    raise GetMonitorBusyError(errorMessage)

def __CheckMonitor(monitor: IMonitor, errorMessage: str|ErrorMessages|None = None) -> None:
    if monitor.IsBusy(): ThrowMonitorBusyError(errorMessage)

def DoWork(monitor: IMonitor, worker: Action, errorMessage: str|ErrorMessages|None = None) -> None:
    __CheckMonitor(monitor, errorMessage)

    with monitor: worker()
def TryDoWork(monitor: IMonitor, worker: Action) -> bool:
    if monitor.IsBusy(): return False

    with monitor: worker()

    return True

def Process[T](monitor: IMonitor, worker: Function[T], errorMessage: str|ErrorMessages|None = None) -> T:
    __CheckMonitor(monitor, errorMessage)
    
    with monitor: return worker()

    raise GetUnexpectedError()
def TryProcess[T](monitor: IMonitor, worker: Function[T]) -> INullable[T]:
    if monitor.IsBusy(): return GetNullValue()
    
    with monitor: return GetNullable(worker())

    raise GetUnexpectedError()

def ProcessData[TIn, TOut](data: TIn, monitor: IMonitor, worker: Converter[TIn, TOut], errorMessage: str|ErrorMessages|None = None) -> TOut:
    return Process(monitor, GetMethodAsFunction(data, worker), errorMessage)
def TryProcessData[TIn, TOut](data: TIn, monitor: IMonitor, worker: Converter[TIn, TOut]) -> INullable[TOut]:
    return TryProcess(monitor, GetMethodAsFunction(data, worker))