from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator as IteratorCollection, Generator as _GeneratorCollection
from types import TracebackType
from typing import final, Callable, Self, Type

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator as GeneratorCollection
from WinCopies.Collections.Enumeration import IterationState, IIterationStatus, IEnumerable, IEnumerator, EnumerationStatus, AsEnumerable, GetIterable
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Collections.Iteration import TryEnumerate, Select
from WinCopies.Delegates import NoAction, GetNotPredicate
from WinCopies.Typing import INullable, INullableItem, CreateNullableItem, InvalidOperationError
from WinCopies.Typing.Delegate import Action, Function, Predicate, Converter as ConverterDelegate, Selector

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

class AccumulatorBase[TItem, TData](Abstract, _GeneratorCollection[TItem, TData, BaseException], IAccumulatorBase[TItem, TData]):
    def __init__(self) -> None:
        super().__init__()

        self.__value: INullableItem[TItem] = CreateNullableItem()
        self.__status: EnumerationStatus = EnumerationStatus()

        self.__moveNext: Action = self.__MoveNext
        self.__send: ConverterDelegate[TData, TItem] = self.__Send

        self.__start: Function[bool|None] = self.__Start
        self.__stop: Action = self.__Stop

    @final
    def __MoveNext(self) -> None:
        if not self.Start(): raise StopIteration()

    @final
    def __Start(self) -> bool|None:
        def start() -> bool: return False

        def stop() -> None:
            self.__Stop()

            raise StopIteration()
        
        value: INullable[TItem] = self._GetInitialValue()

        if value.HasValue():
            self.__status.Start()
            self.__value.SetValue(value.GetValue())

            self.__moveNext = stop
            self.__send = self.__SendFirst

            self.__start = start

            return True

        self.Stop()

        return None
    @final
    def __Stop(self) -> None:
        def start() -> bool: return False

        def moveNext() -> None: raise StopIteration()
        def send(_: TData) -> TItem: raise InvalidOperationError("Iteration has terminated.")
        
        self.__value.UnsetValue()

        self.__moveNext = moveNext
        self.__send = send

        self.__start = start
        self.__stop = NoAction

        self.__status.Complete()

    @final
    def __Send(self, _: TData) -> TItem:
        raise InvalidOperationError("Iteration has not yet started.")
    @final
    def __SendValue(self, data: TData) -> TItem:
        value: TItem = self._Send(data)

        self.__value.SetValue(value)

        return value
    @final
    def __SendFirst(self, data: TData) -> TItem:
        result: TItem = self.__SendValue(data)

        self.__status.NotifyItemProcessed()

        self.__send = self.__SendValue

        return result
    
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
    def Start(self) -> bool|None: return self.__start()
    
    @final
    def Send(self, data: TData) -> TItem: return self.__send(data)

    @final
    def Stop(self) -> None: self.__stop()
    
    @final
    def TryReset(self) -> bool|None:
        if self.IsResetSupported():
            if self.GetStatus().GetState() == IterationState.Idle: return True

            self.Stop()
            
            if self._ResetOverride():
                self.__moveNext = self.__MoveNext
                self.__send = self.__Send

                self.__start = self.__Start
                self.__stop = self.__Stop

                self.__status.Reset()
                
                return True
            
            return False
        
        self.Stop()
        
        return None
    
    @final
    def GetStatus(self) -> IIterationStatus: return self.__status.AsReadOnly()

    @final
    def TryGetValue(self) -> INullable[TItem]: return self.__value.AsReadOnly()
    
    @final
    def __next__(self) -> TItem:
        self.__moveNext()

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