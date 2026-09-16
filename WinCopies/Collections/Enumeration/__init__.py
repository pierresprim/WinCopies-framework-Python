from __future__ import annotations

from abc import abstractmethod
from enum import Flag, auto
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Util import _Outside # pyright: ignore[reportPrivateUsage]
from WinCopies.Enum import AddFlag, HasFlag
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Discard import InvalidatedError, BrokenObjectError
from WinCopies.Typing.Enum import IntEnum

def GetIterationInactiveError() -> InvalidOperationError:
    return InvalidOperationError("Iteration is not active.")

class IterationState(IntEnum):
    Idle = 0
    """Iteration has not yet started."""
    Started = 1
    """Iterator is in run state."""
    Ended = 2
    """Iteration has terminated."""
class IterationResult(IntEnum):
    Faulted = -5
    "Iteration terminated because an error occurred."
    Invalidated = -4
    """Iteration was invalidated because the source mutated."""
    Stopped = -3
    """Iteration was canceled."""
    Failed = -2
    """Iteration failed to start."""
    Idle = -1
    """Iteration has not yet started."""
    Running = 0
    """Iterator is in run state."""
    Completed = 1
    """Iteration was successfully completed, possibly without yielding any item. If the enumerator is empty by design, NoData should be reported."""
    NoData = 2
    """The enumerator is empty by design. An enumeration that completed without yielding any item should report Completed."""

    @final
    def HasCompleted(self) -> bool:
        return self > IterationResult.Running
    @final
    def HasTerminated(self) -> bool:
        return _Outside(IterationResult.Idle, self, IterationResult.Running)

class IterationData(Flag):
    Null = 0
    HasProcessedItems = auto()
    Faulted = auto()

class EnumerationAbortReason(IntEnum):
    Null = 0
    Stopped = 1
    Invalidated = 2
    Errored = 3

class IIterationStatusBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetState(self) -> IterationState:
        ...
    
    @final
    def IsStarted(self) -> bool:
        return self.GetState() == IterationState.Started
class IIterationStatus(IIterationStatusBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetResult(self) -> IterationResult:
        ...
    
    @abstractmethod
    def GetData(self) -> IterationData:
        ...
    
    @final
    def HasProcessedItems(self) -> bool:
        return HasFlag(self.GetData(), IterationData.HasProcessedItems)
    @final
    def HasFaulted(self, strict: bool|None = None) -> bool:
        def hasResult() -> bool: return self.GetResult() < IterationResult.Stopped
        def hasFlag() -> bool: return HasFlag(self.GetData(), IterationData.Faulted)

        match strict:
            case True: return hasResult()
            case False: return hasFlag()
            
            case _: return hasResult() or hasFlag()
    
    @final
    def IsErrored(self, strict: bool|None = None) -> bool:
        def getValue() -> IterationResult:
            match strict:
                case True: return IterationResult.Invalidated
                case False: return IterationResult.Stopped

                case _: return IterationResult.Failed
        
        return self.GetResult() < getValue()
    @final
    def TryGetIterationError(self) -> InvalidOperationError|None:
        match self.GetResult():
            case IterationResult.Faulted: return BrokenObjectError("The iteration has faulted.")
            case IterationResult.Invalidated: return InvalidatedError()
            case IterationResult.Stopped: return InvalidOperationError("The iteration has been stopped.")

            case _: return None
    @final
    def ThrowIfErrored(self) -> None:
        exception: InvalidOperationError|None = self.TryGetIterationError()

        if exception is not None: raise exception

@final
class _ReadOnlyIterationStatus(Abstract, IIterationStatus):
    def __init__(self, iterationStatus: IterationStatus) -> None:
        super().__init__()

        self.__iterationStatus: IterationStatus = iterationStatus

    def GetState(self) -> IterationState: return self.__iterationStatus.GetState()
    def GetResult(self) -> IterationResult: return self.__iterationStatus.GetResult()

    def GetData(self) -> IterationData: return self.__iterationStatus.GetData()
class IterationStatus(Abstract, IIterationStatusBase):
    def __init__(self) -> None:
        super().__init__()

        self.__state: IterationState = IterationState.Idle
        self.__result: IterationResult = IterationResult.Idle

        self.__data: IterationData = IterationData.Null

        self.__readOnly: IIterationStatus = _ReadOnlyIterationStatus(self)

    @final
    def __AddFlag(self, value: IterationData) -> None:
        self.__data = AddFlag(self.__data, value)

    @final
    def GetState(self) -> IterationState: return self.__state
    @final
    def GetResult(self) -> IterationResult: return self.__result
    
    @final
    def GetData(self) -> IterationData: return self.__data

    @final
    def NotifyItemProcessed(self) -> None:
        self.__AddFlag(IterationData.HasProcessedItems)

    @final
    def Reset(self) -> None:
        self.__state = IterationState.Idle
        self.__result = IterationResult.Idle

        self.__data = IterationData.Null

    @final
    def Start(self) -> None:
        self.__state = IterationState.Started
        self.__result = IterationResult.Running

    @final
    def __Terminate(self, result: IterationResult) -> None:
        self.__state = IterationState.Ended
        self.__result = result

    @final
    def Complete(self) -> None:
        self.__Terminate(IterationResult.Completed)

    @final
    def Fail(self) -> None:
        self.__Terminate(IterationResult.Failed)
    
    @final
    def Stop(self) -> None:
        self.__Terminate(IterationResult.Stopped)
    @final
    def Invalidate(self) -> None:
        self.__Terminate(IterationResult.Invalidated)

    @final
    def Fault(self, notify: bool = True) -> bool:
        running: bool = self.IsStarted()

        if notify and running: self.__result = IterationResult.Faulted

        self.__AddFlag(IterationData.Faulted)

        return running
    @final
    def Unfault(self) -> None:
        if self.IsStarted(): self.__result = IterationResult.Running

    @final
    def Abort(self) -> None:
        self.__Terminate(IterationResult.Faulted)

        self.__AddFlag(IterationData.Faulted)

    @final
    def AsReadOnly(self) -> IIterationStatus:
        return self.__readOnly

@final
class _NoData(Abstract, IIterationStatus):
    def __init__(self) -> None: super().__init__()

    def GetState(self) -> IterationState: return IterationState.Ended
    def GetResult(self) -> IterationResult: return IterationResult.NoData

    def GetData(self) -> IterationData: return IterationData.Null

__noData: IIterationStatus = _NoData()

def GetNoDataEnumerationStatus() -> IIterationStatus:
    return __noData