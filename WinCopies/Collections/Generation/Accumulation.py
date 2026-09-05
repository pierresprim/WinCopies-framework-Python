from __future__ import annotations

from abc import abstractmethod
from collections.abc import Generator
from types import TracebackType
from typing import final, Self, Type

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Enumeration import IterationState, IIterationStatus, IterationStatus, GetIterationInactiveError
from WinCopies.Delegates import NoAction
from WinCopies.Enums import ErrorMessages
from WinCopies.Typing import INullable, INullableItem, CreateNullableItem
from WinCopies.Typing.Delegate import Action, Function, Converter as ConverterDelegate
from WinCopies.Typing.Monitoring import IMonitor, Monitor, DoWork, Process, ProcessData

class IAccumulatorAbstract(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetStatus(self) -> IIterationStatus:
        ...
    
    @abstractmethod
    def Start(self) -> bool|None:
        ...
    @abstractmethod
    def Stop(self) -> None:
        ...

    @abstractmethod
    def IsResetSupported(self) -> bool:
        ...
    @abstractmethod
    def TryReset(self) -> bool|None:
        ...
class IAccumulatorBase[TItem, TData](IAccumulatorAbstract):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryGetValue(self) -> INullable[TItem]:
        ...
    @final
    def GetValue(self) -> TItem:
        return self.TryGetValue().GetValue()

    @abstractmethod
    def Send(self, data: TData) -> TItem:
        ...

    @abstractmethod
    def AsGenerator(self) -> Generator[TItem, TData, BaseException]:
        ...
class IAccumulator[T](IAccumulatorBase[T, T]):
    def __init__(self) -> None: super().__init__()

class _IAccumulatorCookie[TItem, TData](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetInitialValue(self) -> INullable[TItem]:
        ...

    @abstractmethod
    def Send(self, data: TData) -> TItem:
        ...

@final
class _AccumulatorEngine[TItem, TData](Abstract):
    def __init__(self, accumulator: _IAccumulatorCookie[TItem, TData]) -> None:
        super().__init__()

        self.__cookie: _IAccumulatorCookie[TItem, TData] = accumulator

        self.__value: INullableItem[TItem] = CreateNullableItem()
        self.__status: IterationStatus = IterationStatus()

        self.__moveNext: Action = self.__MoveNext
        self.__send: ConverterDelegate[TData, TItem] = self.__Send

        self.__start: Function[bool|None] = self.__Start
        self.__stop: Action = self.__Stop

    def __MoveNext(self) -> None:
        if not self.Start(): raise StopIteration()

    def __Start(self) -> bool|None:
        def start() -> bool: return False

        def stop() -> None:
            self.__Stop()

            raise StopIteration()
        
        value: INullable[TItem] = self.__cookie.GetInitialValue()

        if value.HasValue():
            self.__status.Start()
            self.__value.SetValue(value.GetValue())

            self.__moveNext = stop
            self.__send = self.__SendFirst

            self.__start = start

            return True

        self.Stop()

        return None
    def __Stop(self) -> None:
        def start() -> bool: return False

        def moveNext() -> None: raise StopIteration()
        def send(_: TData) -> TItem: raise GetIterationInactiveError()
        
        self.__value.UnsetValue()

        self.__moveNext = moveNext
        self.__send = send

        self.__start = start
        self.__stop = NoAction

        self.__status.Complete()

    def __Send(self, _: TData) -> TItem:
        raise GetIterationInactiveError()
    def __SendValue(self, data: TData) -> TItem:
        value: TItem = self.__cookie.Send(data)

        self.__value.SetValue(value)

        return value
    def __SendFirst(self, data: TData) -> TItem:
        result: TItem = self.__SendValue(data)

        self.__status.NotifyItemProcessed()

        self.__send = self.__SendValue

        return result

    def MoveNext(self) -> None:
        self.__moveNext()

    def Start(self) -> bool|None:
        return self.__start()
    
    def Send(self, data: TData) -> TItem:
        return self.__send(data)

    def Stop(self) -> None:
        return self.__stop()
    
    def GetStatus(self) -> IIterationStatus:
        return self.__status.AsReadOnly()

    def TryGetValue(self) -> INullable[TItem]:
        return self.__value.AsReadOnly()

    def Reset(self) -> None:
        self.__moveNext = self.__MoveNext
        self.__send = self.__Send

        self.__start = self.__Start
        self.__stop = self.__Stop

        self.__status.Reset()

class AccumulatorBase[TItem, TData](Abstract, Generator[TItem, TData, BaseException], IAccumulatorBase[TItem, TData]):
    @final
    class _Cookie[_TItem, _TData](Abstract, _IAccumulatorCookie[_TItem, _TData]):
        def __init__(self, accumulator: AccumulatorBase[_TItem, _TData]) -> None:
            super().__init__()

            self.__accumulator: AccumulatorBase[_TItem, _TData] = accumulator

        def GetInitialValue(self) -> INullable[_TItem]: return self.__accumulator._GetInitialValue()

        def Send(self, data: _TData) -> _TItem: return self.__accumulator._Send(data)
    
    def __init__(self) -> None:
        super().__init__()

        self.__engine: _AccumulatorEngine[TItem, TData] = _AccumulatorEngine[TItem, TData](AccumulatorBase._Cookie[TItem, TData](self))
        self.__monitor: IMonitor = Monitor()

    @final
    def __DoWork(self, worker: Action) -> None:
        DoWork(self.__monitor, worker, ErrorMessages.ReentrancyNotAllowed)
    @final
    def __Process[T](self, worker: Function[T]) -> T:
        return Process(self.__monitor, worker, ErrorMessages.ReentrancyNotAllowed)

    @final
    def __Stop(self) -> None:
        self.__engine.Stop()
    
    @abstractmethod
    def _GetInitialValue(self) -> INullable[TItem]:
        ...

    @abstractmethod
    def _Send(self, data: TData) -> TItem:
        ...

    @abstractmethod
    def _ResetOverride(self) -> bool:
        ...

    @final
    def Start(self) -> bool|None: return self.__Process(self.__engine.Start)
    
    @final
    def Send(self, data: TData) -> TItem: return ProcessData(data, self.__monitor, self.__engine.Send, ErrorMessages.ReentrancyNotAllowed)

    @final
    def Stop(self) -> None: self.__DoWork(self.__Stop)
    
    @final
    def TryReset(self) -> bool|None:
        def tryReset() -> bool|None:
            if self.IsResetSupported():
                if self.GetStatus().GetState() == IterationState.Idle: return True

                self.__Stop()
                
                if self._ResetOverride():
                    self.__engine.Reset()
                    
                    return True
                
                return False
            
            self.__Stop()

            return None

        return self.__Process(tryReset)
    
    @final
    def GetStatus(self) -> IIterationStatus: return self.__engine.GetStatus()

    @final
    def TryGetValue(self) -> INullable[TItem]: return self.__engine.TryGetValue()
    
    @final
    def __next__(self) -> TItem:
        self.__DoWork(self.__engine.MoveNext)

        return self.GetValue()
    
    @final
    def __iter__(self) -> Self: return self

    @final
    def send(self, value: TData) -> TItem: return self.Send(value)

    @final
    def throw(self, typ: BaseException|Type[BaseException], val: object|None = None, tb: TracebackType|None = None) -> TItem:
        self.Stop()
        
        e: BaseException = typ if isinstance(typ, BaseException) else (typ() if val is None else typ(val))

        raise e if tb is None else e.with_traceback(tb)

    @final
    def close(self) -> None: self.Stop()
    
    @final
    def AsGenerator(self) -> Generator[TItem, TData, BaseException]: return self
class Accumulator[T](AccumulatorBase[T, T], IAccumulator[T]):
    def __init__(self) -> None: super().__init__()