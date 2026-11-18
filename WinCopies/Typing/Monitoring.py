from abc import abstractmethod
from threading import Lock
from typing import final, NoReturn

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Delegates import GetMethodAsFunction
from WinCopies.Enums import ErrorMessages
from WinCopies.String import GetValueOrDefault
from WinCopies.Typing import INullable, InvalidOperationError, GetUnexpectedError, GetNullValue, GetNullable
from WinCopies.Typing.Delegate import Action, Function, Converter

def GetMonitorError(busy: bool = True, errorMessage: str|ErrorMessages|None = None) -> InvalidOperationError:
    return InvalidOperationError(GetValueOrDefault(errorMessage, f"The given monitor is {"already" if busy else "not"} busy."))
def ThrowMonitorError(busy: bool = True, errorMessage: str|ErrorMessages|None = None) -> NoReturn:
    raise GetMonitorError(busy, errorMessage)

def GetMonitorBusyError(errorMessage: str|ErrorMessages|None = None) -> InvalidOperationError:
    return GetMonitorError(errorMessage=errorMessage)
def ThrowMonitorBusyError(errorMessage: str|ErrorMessages|None = None) -> NoReturn:
    ThrowMonitorError(errorMessage=errorMessage)

def GetMonitorNotBusyError(errorMessage: str|ErrorMessages|None = None) -> InvalidOperationError:
    return GetMonitorError(False, errorMessage)
def ThrowMonitorNotBusyError(errorMessage: str|ErrorMessages|None = None) -> NoReturn:
    ThrowMonitorError(False, errorMessage)

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
    def Initialize(self) -> None:
        if self.IsBusy(): ThrowMonitorBusyError()

        self.__isBusy = True
    
    @final
    def IsBusy(self) -> bool: return self.__isBusy
    
    @final
    def Dispose(self) -> None: self.__isBusy = False

class ISafeMonitor(IMonitor):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryInitialize(self) -> bool:
        ...
    @final
    def Initialize(self) -> None:
        if not self.TryInitialize(): ThrowMonitorBusyError()
class AtomicMonitor(Abstract, ISafeMonitor):
    def __init__(self) -> None:
        super().__init__()

        self.__lock: Lock = Lock()
    
    @final
    def IsBusy(self) -> bool: return self.__lock.locked()

    @final
    def TryInitialize(self) -> bool:
        return self.__lock.acquire(False)
    
    @final
    def Dispose(self) -> None:
        try: self.__lock.release()
        except RuntimeError as e: raise GetMonitorNotBusyError() from e

def __CheckMonitor(monitor: IMonitor, errorMessage: str|ErrorMessages|None = None) -> None:
    if monitor.IsBusy(): ThrowMonitorBusyError(errorMessage)

def DoWork(monitor: IMonitor, worker: Action, errorMessage: str|ErrorMessages|None = None) -> None:
    __CheckMonitor(monitor, errorMessage)

    with monitor: worker()
def TryDoWork(monitor: IMonitor, worker: Action) -> bool:
    if isinstance(monitor, ISafeMonitor):
        if monitor.TryInitialize():
            try:
                worker()

                return True
            
            finally: monitor.Dispose()

        return False
    
    if monitor.IsBusy(): return False

    with monitor: worker()

    return True

def Process[T](monitor: IMonitor, worker: Function[T], errorMessage: str|ErrorMessages|None = None) -> T:
    __CheckMonitor(monitor, errorMessage)
    
    with monitor: return worker()

    raise GetUnexpectedError()
def TryProcess[T](monitor: IMonitor, worker: Function[T]) -> INullable[T]:
    if isinstance(monitor, ISafeMonitor):
        if monitor.TryInitialize():
            try: return GetNullable(worker())
            finally: monitor.Dispose()

        return GetNullValue()
    
    if monitor.IsBusy(): return GetNullValue()
    
    with monitor: return GetNullable(worker())

    raise GetUnexpectedError()

def ProcessData[TIn, TOut](data: TIn, monitor: IMonitor, worker: Converter[TIn, TOut], errorMessage: str|ErrorMessages|None = None) -> TOut:
    return Process(monitor, GetMethodAsFunction(data, worker), errorMessage)
def TryProcessData[TIn, TOut](data: TIn, monitor: IMonitor, worker: Converter[TIn, TOut]) -> INullable[TOut]:
    return TryProcess(monitor, GetMethodAsFunction(data, worker))