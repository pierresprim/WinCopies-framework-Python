from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator as IteratorCollection, Generator as _GeneratorCollection
from types import TracebackType
from typing import final, Any, Callable, Self, Type

from WinCopies import IInterface, IDisposableAbstract, Abstract
from WinCopies.Collections import Generator as GeneratorCollection
from WinCopies.Collections.Enumeration import IterationState, IIterationStatus, IEnumerable, IEnumeratorBase, IEnumerator, IterationStatus, IteratorBase as _IteratorBase, Iterator as _Iterator, ConverterEnumeratorBase, AsEnumerable, GetIterable, GetIterationInactiveError, GetNoDataEnumerationStatus
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Collections.Iteration import TryEnumerate, Select
from WinCopies.Delegates import NoAction, GetNotPredicate
from WinCopies.Enums import ErrorMessages
from WinCopies.Typing import INullable, INullableItem, CreateNullableItem
from WinCopies.Typing.Delegate import Action, Function, Predicate, Converter as ConverterDelegate, Selector
from WinCopies.Typing.Discard import DiscardReason, IDisposableCookie, IDisposable, DisposableAbstract
from WinCopies.Typing.Monitoring import IMonitor, Monitor, DoWork, Process, ProcessData

class IResumable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Resume(self) -> None:
        ...

class IMovable(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryMoveToTop(self) -> bool|None:
        ...
    @abstractmethod
    def TryMoveToBottom(self) -> bool|None:
        ...

class IRemovable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Remove(self) -> None:
        ...

class INode(IMovable, IRemovable):
    def __init__(self) -> None: super().__init__()

class IIterator[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Include(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...
    @abstractmethod
    def Exclude(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...

    @abstractmethod
    def IncludeWhile(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...
    @abstractmethod
    def IncludeUntil(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...

    @abstractmethod
    def DoIncludeWhile(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...
    @abstractmethod
    def DoIncludeUntil(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...

    @abstractmethod
    def ExcludeWhile(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...
    @abstractmethod
    def ExcludeUntil(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        ...
    
    @abstractmethod
    def WhereOfType[TResult](self, t: Type[TResult]) -> GeneratorCollection[TResult]:
        ...
class INullableIterator[T](IIterator[T|None]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def WhereNotNone(self) -> GeneratorCollection[T]:
        ...

class IteratorBase[T](Abstract, IIterator[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetItems(self) -> Iterable[T]:
        ...
    
    @abstractmethod
    def _ProcessItem(self, item: T) -> bool:
        ...
    
    @final
    def Include(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        for item in self._GetItems():
            if predicate(item):
                yield item

                if self._ProcessItem(item): break
    @final
    def Exclude(self, predicate: Predicate[T]) -> GeneratorCollection[T]: return self.Include(GetNotPredicate(predicate))

    @final
    def IncludeWhile(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        for item in self._GetItems():
            if predicate(item):
                yield item

                if self._ProcessItem(item): break

            else: break
    @final
    def IncludeUntil(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        for item in self._GetItems():
            if predicate(item): break

            yield item

            if self._ProcessItem(item): break
    
    @final
    def DoIncludeUntil(self, predicate: Predicate[T]) -> GeneratorCollection[T]:
        for item in self._GetItems():
            yield item

            if self._ProcessItem(item) or predicate(item): break
    @final
    def DoIncludeWhile(self, predicate: Predicate[T]) -> GeneratorCollection[T]: return self.DoIncludeUntil(GetNotPredicate(predicate))

    @final
    def __Exclude(self, selector: Selector[IEnumerator[T]]) -> GeneratorCollection[T]:
        def getIterator(enumerable: IEnumerable[T]) -> IteratorCollection[T]|None:
            enumerator: IEnumerator[T]|None = enumerable.TryGetEnumerator()
            
            return None if enumerator is None else selector(enumerator).AsIterator()
        
        for item in TryEnumerate(getIterator(AsEnumerable(self._GetItems()))):
            yield item

            if self._ProcessItem(item): break
    
    @final
    def ExcludeWhile(self, predicate: Predicate[T]) -> GeneratorCollection[T]: return self.__Exclude(lambda enumerator: ExcluerEnumerator(enumerator, predicate))
    @final
    def ExcludeUntil(self, predicate: Predicate[T]) -> GeneratorCollection[T]: return self.__Exclude(lambda enumerator: ExcluerUntilEnumerator(enumerator, predicate))
    
    @final
    def WhereOfType[TResult](self, t: Type[TResult]) -> GeneratorCollection[TResult]:
        _item: T|None = None
        
        for item in self._GetItems():
            if isinstance(_item := item, t):
                yield _item

                self._ProcessItem(item)
class Iterator[T](IteratorBase[T]):
    def __init__(self, items: Iterable[T]|None) -> None:
        super().__init__()

        self.__items: Iterable[T] = GetIterable(items)
    
    @final
    def _GetItems(self) -> Iterable[T]:
        return self.__items

class NullableIteratorBase[T](IteratorBase[T|None], INullableIterator[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def WhereNotNone(self) -> GeneratorCollection[T]:
        for item in self._GetItems():
            if item is not None:
                yield item

                if self._ProcessItem(item): break
class NullableIterator[T](NullableIteratorBase[T]):
    def __init__(self, items: Iterable[T]|None) -> None:
        super().__init__()

        self.__items: Iterable[T] = GetIterable(items)
    
    @final
    def _GetItems(self) -> Iterable[T]:
        return self.__items

class GeneratorAbstract[T: IRemovable](IteratorBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _OnItemProcessed(self, item: T) -> bool:
        ...
    
    def _ProcessItem(self, item: T) -> bool:
        item.Remove()

        return self._OnItemProcessed(item)
class GeneratorBase[T: IRemovable](GeneratorAbstract[T]):
    def __init__(self, items: Iterable[T]|None) -> None:
        super().__init__()

        self.__items: Iterable[T] = GetIterable(items)
    
    @final
    def _GetItems(self) -> Iterable[T]:
        return self.__items

class Generator[T: IRemovable](GeneratorBase[T]):
    def __init__(self, items: Iterable[T], func: Function[bool]) -> None:
        super().__init__(items)

        self.__func: Function[bool] = func
    
    @final
    def _OnItemProcessed(self, item: T) -> bool:
        return self.__func()
class ExtendedGenerator[T: IRemovable](GeneratorBase[T]):
    def __init__(self, items: Iterable[T], predicate: Predicate[T]) -> None:
        super().__init__(items)

        self.__predicate: Predicate[T] = predicate
    
    @final
    def _OnItemProcessed(self, item: T) -> bool:
        return self.__predicate(item)

class DefaultGenerator[T: IRemovable](GeneratorBase[T]):
    def __init__(self, items: Iterable[T]|None) -> None:
        super().__init__(items)
    
    @final
    def _OnItemProcessed(self, item: T) -> bool:
        return False

class ConverterBase[TIn, TOut](Abstract, IIterator[TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetItems(self) -> IIterator[TIn]:
        ...

    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...

    @final
    def _GetPredicate(self, predicate: Predicate[TOut]) -> Predicate[TIn]:
        return lambda item: predicate(self._Convert(item))

    @final
    def _GetConverter(self) -> ConverterDelegate[TIn, TOut]:
        return lambda item: self._Convert(item)
    
    @final
    def _Select(self, converter: Callable[[IIterator[TIn], Predicate[TIn]], GeneratorCollection[TIn]], predicate: Predicate[TOut]) -> GeneratorCollection[TOut]:
        return Select(converter(self._GetItems(), self._GetPredicate(predicate)), self._GetConverter())
    
    @final
    def Include(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.Include(predicate), predicate)
    @final
    def Exclude(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.Exclude(predicate), predicate)

    @final
    def IncludeWhile(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.IncludeWhile(predicate), predicate)
    @final
    def IncludeUntil(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.IncludeUntil(predicate), predicate)

    @final
    def DoIncludeWhile(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.DoIncludeWhile(predicate), predicate)
    @final
    def DoIncludeUntil(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.DoIncludeUntil(predicate), predicate)

    @final
    def ExcludeWhile(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.ExcludeWhile(predicate), predicate)
    @final
    def ExcludeUntil(self, predicate: Predicate[TOut]) -> GeneratorCollection[TOut]: return self._Select(lambda items, predicate: items.ExcludeUntil(predicate), predicate)
    
    @final
    def WhereOfType[TResult](self, t: type[TResult]) -> GeneratorCollection[TResult]: return self._GetItems().WhereOfType(t)
class Converter[TIn, TOut](ConverterBase[TIn, TOut]):
    def __init__(self, items: IIterator[TIn]) -> None:
        super().__init__()

        self.__items: IIterator[TIn] = items
    
    @final
    def _GetItems(self) -> IIterator[TIn]: return self.__items

class DelegateConverterBase[TIn, TOut](ConverterBase[TIn, TOut]):
    def __init__(self, converter: ConverterDelegate[TIn, TOut]) -> None:
        super().__init__()

        self.__converter: ConverterDelegate[TIn, TOut] = converter
    
    @final
    def _Convert(self, item: TIn) -> TOut: return self.__converter(item)
class DelegateConverter[TIn, TOut](DelegateConverterBase[TIn, TOut]):
    def __init__(self, items: IIterator[TIn], converter: ConverterDelegate[TIn, TOut]) -> None:
        super().__init__(converter)

        self.__items: IIterator[TIn] = items
    
    @final
    def _GetItems(self) -> IIterator[TIn]: return self.__items

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
    def AsGenerator(self) -> _GeneratorCollection[TItem, TData, BaseException]:
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

class AccumulatorBase[TItem, TData](Abstract, _GeneratorCollection[TItem, TData, BaseException], IAccumulatorBase[TItem, TData]):
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
    def AsGenerator(self) -> _GeneratorCollection[TItem, TData, BaseException]: return self
class Accumulator[T](AccumulatorBase[T, T], IAccumulator[T]):
    def __init__(self) -> None: super().__init__()

class ICursorBase(IEnumeratorBase, IDisposable):
    def __init__(self) -> None: super().__init__()
class ICursor[T](IEnumerator[T], ICursorBase):
    def __init__(self) -> None: super().__init__()

@final
class _EmptyCursor[T](_IteratorBase[T], ICursor[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetCurrent(self) -> T: raise GetIterationInactiveError()
    def MoveNext(self) -> bool: return False
    def Stop(self) -> None: pass
    def TryReset(self) -> bool|None: return None
    def IsResetSupported(self) -> bool: return False
    
    def GetStatus(self) -> IIterationStatus: return GetNoDataEnumerationStatus()

    def Dispose(self) -> None: pass

__emptyCursor = _EmptyCursor[Any]()

def GetEmptyCursor[T]() -> ICursor[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyCursor

class IScannable[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryGetCursor(self) -> ICursor[T]|None:
        ...
    @final
    def GetCursor(self) -> ICursor[T]:
        cursor: ICursor[T]|None = self.TryGetCursor()

        return GetEmptyCursor() if cursor is None else cursor
class Scannable[T](Abstract, IScannable[T]):
    def __init__(self) -> None: super().__init__()

class Cursor[TRoot, THandle, TItem](ConverterEnumeratorBase[THandle, TItem], DisposableAbstract, ICursor[TItem]):
    def __init__(self, root: TRoot) -> None:
        def enumerate() -> IteratorCollection[THandle]:
            handle: INullable[THandle] = self._GetFirstHandle(root)

            def setNext() -> None:
                nonlocal handle

                handle = self._GetNextHandle(value)

            if self._OnRootHandleProcessed(root) and handle.HasValue():
                value: THandle = handle.GetValue()

                def setCurrent() -> bool:
                    nonlocal value

                    return self._OnHandleProcessing(value := handle.GetValue())

                if self._OnHandleProcessing(value):
                    yield value

                    setNext()

                    while self._OnHandleProcessed(value) and handle.HasValue() and setCurrent():
                        yield value

                        setNext()

        def updateCookie(cookie: IDisposableCookie) -> None: self.__disposableCookie = cookie
        
        super().__init__(_Iterator[THandle](enumerate()))

        self.__disposableCookie: IDisposableCookie = self._CreateDisposableCookie(updateCookie) # type: ignore[no-redef]

    @final
    def _GetDisposableCookie(self) -> IDisposableCookie: return self.__disposableCookie

    @abstractmethod
    def _GetFirstHandle(self, handle: TRoot) -> INullable[THandle]:
        ...
    @abstractmethod
    def _GetNextHandle(self, handle: THandle) -> INullable[THandle]:
        ...

    def _OnRootHandleProcessed(self, handle: TRoot) -> bool:
        return True
    
    def _OnHandleProcessing(self, handle: THandle) -> bool:
        return True
    def _OnHandleProcessed(self, handle: THandle) -> bool:
        return True

    def _OnStopping(self, enumerator: IEnumerator[THandle]) -> None:
        self._DisposeHandle(enumerator.GetCurrent())

        super()._OnStopping(enumerator)

    @abstractmethod
    def _DisposeHandle(self, handle: THandle) -> None:
        ...

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        self.Stop()

        super()._DisposeOverride(reason)

    def _Finalize(self) -> None:
        enumerator: IEnumerator[THandle] = self._GetContainer()

        if enumerator.IsStarted(): self._DisposeHandle(enumerator.GetCurrent())
        
        super()._Finalize()
class DisposableCursor[TRoot: IDisposableAbstract, THandle: IDisposableAbstract, TItem](Cursor[TRoot, THandle, TItem]):
    def __init__(self, root: TRoot) -> None: super().__init__(root)

    def _DisposeHandle(self, handle: TRoot|THandle) -> None:
        handle.Dispose()
    
    def _DisposeProcessedHandle(self, handle: TRoot|THandle) -> bool:
        self._DisposeHandle(handle)
        
        return True

    def _OnRootHandleProcessed(self, handle: TRoot) -> bool:
        return self._DisposeProcessedHandle(handle)
    def _OnHandleProcessed(self, handle: THandle) -> bool:
        return self._DisposeProcessedHandle(handle)