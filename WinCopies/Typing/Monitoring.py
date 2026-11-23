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
    """A monitor that can be tried, which tells whether it was taken instead of raising when it is busy."""

    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryInitialize(self) -> bool:
        """
        Takes this monitor if it is free, without blocking.

        Returns:
            True if this monitor was free and is now taken, False if it was busy."""
        ...
    @final
    def Initialize(self) -> None:
        """
        Takes this monitor.

        Raises:
            InvalidOperationError: This monitor is busy.
        """
        if not self.TryInitialize(): ThrowMonitorBusyError()
class AtomicMonitor(Abstract, ISafeMonitor):
    """
    A monitor that is taken in one indivisible step, through a lock acquired without blocking.

    Unlike Monitor, whose busy flag is tested and then set, this monitor cannot be taken twice by a finalizer or a weak reference callback that interrupts the code taking it, nor by two threads. Trying to take it never blocks, so a finalizer can try it even while the code it interrupted holds it.
    """
    def __init__(self) -> None:
        super().__init__()

        self.__lock: Lock = Lock()
    
    @final
    def IsBusy(self) -> bool:
        """
        Tells whether this monitor is taken.

        Between threads, the result is a snapshot, which another thread can make obsolete at once. To take this monitor only if it is free, use TryInitialize, which tests and takes it in one step.

        Returns:
            True if this monitor is taken, False otherwise.
        """
        return self.__lock.locked()

    @final
    def TryInitialize(self) -> bool:
        return self.__lock.acquire(False)
    
    @final
    def Dispose(self) -> None:
        """
        Releases this monitor.

        Only the code that took this monitor may release it. This method does not check it, since releasing a monitor one does not hold is a programming error.

        Raises:
            InvalidOperationError: This monitor is not busy.
        """
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