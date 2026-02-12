from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from enum import Enum, Flag, auto
from typing import final, Callable

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerator, Enumerable, EnumeratorProvider, IteratorProvider, AbstractEnumerator, TryAsEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, TryAsStackHandler
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing.Delegate import Function, NullablePredicate
from WinCopies.Typing.Pairing import IKeyValuePair

class Events(Flag):
    Start = auto()
    End = auto()

    @staticmethod
    def TryConvertFromString(value: str, predicate: Callable[[str|None, str], bool]|None = None) -> Events|None:
        def _predicate(name: str|None) -> bool:
            return (name := event.name) is not None and name == value
        
        if predicate is None:
            for event in Events:
                if _predicate(event.name):
                    return event
        
        else:
            for event in Events:
                if predicate(event.name, value):
                    return event
        
        return None

class LoopResult(Enum):
    Continue = 0
    Completed = 1
    SkipChildren = 2
    ExitLevel = 3

class IEnumerationDelegate[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> IKeyValuePair[T, Events]|None:
        pass
    
    @abstractmethod
    def SetCurrent(self, value: IKeyValuePair[T, Events]) -> LoopResult:
        pass
    
    @abstractmethod
    def TrySetCurrent(self, item: IKeyValuePair[T, Events]|None) -> LoopResult:
        pass

class EnumerationDelegate[T](Abstract, IEnumerationDelegate[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__current: IKeyValuePair[T, Events]|None = None
    
    @final
    def GetCurrent(self) -> IKeyValuePair[T, Events]|None:
        return self.__current
    
    def SetCurrent(self, value: IKeyValuePair[T, Events]) -> LoopResult:
        self.__current = value

        return LoopResult.Continue
    
    @final
    def TrySetCurrent(self, item: IKeyValuePair[T, Events]|None) -> LoopResult:
        return LoopResult.Completed if item is None else self.SetCurrent(item)
@final
class EnumerationHandler[T](EnumerationDelegate[T]):
    @final
    class _EnumerationCookie[_T](Abstract):
        def __init__(self, handler: IRecursiveStackedEnumerationHandler[_T]) -> None:
            super().__init__()
            
            self.__root: _T|None = None
            self.__handler: IRecursiveStackedEnumerationHandler[_T] = handler
            self.__onEnteringLevel: NullablePredicate[_T] = self.__GetLevelEntranceDelegate()
        
        def __OnEnteringLevel(self, item: _T) -> bool|None:
            result: bool|None = self.__handler.OnEnteringMainEnumerationLevel(item)

            if result is None:
                return None

            if result is True:
                self.__onEnteringLevel = lambda item: self.__handler.OnEnteringSubenumerationLevel(item)

                self.__root = item

                return True
            
            return False
        
        def __GetLevelEntranceDelegate(self) -> NullablePredicate[_T]:
            return lambda item: self.__OnEnteringLevel(item)
        
        def OnEnteringLevel(self, item: _T) -> bool|None:
            result: bool|None = self.__onEnteringLevel(item)

            if result is None:
                return None
            
            if result is True:
                self.__handler.OnEnteringEnumerationLevel(item)

                return True
            
            return False
        
        def OnExitingLevel(self, item: _T) -> bool|None:
            def getResult() -> bool|None:
                if item is self.__root:
                    self.__onEnteringLevel = self.__GetLevelEntranceDelegate()
                    self.__root = None

                    return self.__handler.OnExitingMainEnumerationLevel(item)
                
                return self.__handler.OnExitingSubenumerationLevel(item)
            
            result: bool|None = getResult()
            self.__handler.OnExitingEnumerationLevel(item)

            return result
    
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[T]) -> None:
        super().__init__()

        self.__cookie: EnumerationHandler._EnumerationCookie[T] = EnumerationHandler._EnumerationCookie[T](handler)
    
    def SetCurrent(self, value: IKeyValuePair[T, Events]) -> LoopResult:
        def getResult(result: bool|None, default: LoopResult) -> LoopResult:
            return LoopResult.Continue if result is True else (LoopResult.Completed if result is None else default)

        super().SetCurrent(value)
        
        match value.GetValue():
            case Events.Start:
                return getResult(self.__cookie.OnEnteringLevel(value.GetKey()), LoopResult.SkipChildren)
            case Events.End:
                return getResult(self.__cookie.OnExitingLevel(value.GetKey()), LoopResult.ExitLevel)
            case _:
                return LoopResult.Continue

class Enumerator[T](AbstractEnumerator[IKeyValuePair[T, Events]]):
    def __init__(self, enumerator: IEnumerator[IKeyValuePair[T, Events]], handler: IRecursiveStackedEnumerationHandler[T]|None) -> None:
        super().__init__(enumerator)

        self.__delegate: IEnumerationDelegate[T] = EnumerationDelegate[T]() if handler is None else EnumerationHandler[T](handler)
        self.__moveNext: Function[bool] = BoolFalse
    
    @final
    def GetCurrent(self) -> IKeyValuePair[T, Events]|None:
        return self.__delegate.GetCurrent()
    
    @final
    def __ResetMoveNext(self) -> None:
        self.__moveNext = self.__MoveNext
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__ResetMoveNext()

            return True
        
        return False
    
    @final
    def __MoveNext(self) -> bool:
        def moveNext() -> bool:
            return enumerator.MoveNext()
        def getCurrent() -> IKeyValuePair[T, Events]|None:
            return enumerator.GetCurrent()
        
        def isEvent(currentEvent: Events, event: Events) -> bool:
            return currentEvent == event
        def isEndEvent(currentEvent: Events) -> bool:
            return isEvent(currentEvent, Events.End)
        
        def updateMoveNext(value: int) -> None:
            self.__moveNext = lambda: skip(value)
        
        def loop() -> bool:
            if moveNext():
                result: LoopResult = self.__delegate.TrySetCurrent(getCurrent())

                match result:
                    case LoopResult.SkipChildren:
                        updateMoveNext(1)

                        return True

                    case LoopResult.ExitLevel:
                        updateMoveNext(2)

                        return True

                    case _:
                        return result != LoopResult.Completed
            
            return False
        
        def skip(start: int) -> bool:
            if moveNext():
                current: IKeyValuePair[T, Events]|None = getCurrent()

                if current is None:
                    return False
                
                self.__ResetMoveNext()
                currentEvent: Events = current.GetValue()
                
                if isEndEvent(currentEvent):
                    self.__delegate.SetCurrent(current)

                    return True
                
                while moveNext():
                    if (current := getCurrent()) is None:
                        return False
                    
                    if isEvent(currentEvent := current.GetValue(), Events.Start):
                        start += 1
                    
                    if isEndEvent(currentEvent):
                        start -= 1

                        if start == 0:
                            return loop()
            
            return False
        
        enumerator: IEnumerator[IKeyValuePair[T, Events]] = self._GetContainer()

        return loop()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnStopped(self) -> None:
        super()._OnStopped()

        self.__moveNext = BoolFalse

class IGeneratorProvider[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetIterator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Iterator[T]:
        pass

    @abstractmethod
    def GetFIFOIterator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Iterator[T]:
        pass
    @abstractmethod
    def GetLIFOIterator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Iterator[T]:
        pass

class GeneratorProvider[T](Abstract, IGeneratorProvider[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @staticmethod
    def __Iterate(iterator: Iterator[IKeyValuePair[T, Events]], event: Events) -> Generator[T]:
        for item in iterator:
            if item.GetValue() == event:
                yield item.GetKey()
    
    def GetIterator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Iterator[T]:
        for item in iterator:
            yield item.GetKey()
    
    def GetFIFOIterator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Generator[T]:
        return GeneratorProvider[T].__Iterate(iterator, Events.Start)
    def GetLIFOIterator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Generator[T]:
        return GeneratorProvider[T].__Iterate(iterator, Events.End)
class ManagedGeneratorProvider[T](GeneratorProvider[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def DisposeItem(self, item: T) -> None:
        pass
    
    def GetGenerator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Generator[T]:
        element: T|None = None

        for item in iterator:
            yield (element := item.GetKey())

            if item.GetValue() == Events.End:
                self.DisposeItem(element)
    
    def GetFIFOEnumerator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Generator[T]:
        element: T|None = None
        value: Events|None = None

        for item in iterator:
            element = item.GetKey()

            if (value := item.GetValue()) == Events.Start:
                yield element
            
            elif value == Events.End:
                self.DisposeItem(element)
    def GetLIFOEnumerator(self, iterator: Iterator[IKeyValuePair[T, Events]]) -> Generator[T]:
        element: T|None = None

        for item in iterator:
            if item.GetValue() == Events.End:
                yield (element := item.GetKey())
                
                self.DisposeItem(element)

class RecursivelyScannable[T](Abstract, IRecursivelyScannable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetGeneratorProvider(self) -> IGeneratorProvider[T]:
        pass
    
    @abstractmethod
    def _GetItems(self, events: Events) -> Enumerable[IKeyValuePair[T, Events]]:
        pass
    
    @final
    def __GetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        def getIterator() -> Iterator[T]|None:
            def getGeneratorProvider() -> IGeneratorProvider[T]:
                return self._GetGeneratorProvider()
            
            if enumerationOrder == EnumerationOrder.LIFO and handler is None:
                return getGeneratorProvider().GetLIFOIterator(self._GetItems(Events.End).GetEnumerator().AsIterator())
            
            enumerator: IEnumerator[IKeyValuePair[T, Events]]|None = self._GetItems(Events.Start|Events.End).TryGetEnumerator()
            
            if enumerator is None:
                return None
            
            enumerator = Enumerator[T](enumerator, handler)
            
            return getGeneratorProvider().GetIterator(enumerator) if enumerationOrder == EnumerationOrder.Both else getGeneratorProvider().GetFIFOIterator(enumerator)
        
        return TryAsEnumerator(getIterator())
    
    @final
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        return self.__GetRecursiveEnumerator(enumerationOrder, TryAsStackHandler(handler))
    @final
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        return self.__GetRecursiveEnumerator(enumerationOrder, handler)
    
    @final
    def AsRecursivelyIterable(self) -> Iterable[T]:
        return EnumeratorProvider[T](self.TryGetRecursiveEnumerator)
class RecursivelyIteratorProvider[T](RecursivelyScannable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetItemsIterator(self, events: Events) -> Iterator[IKeyValuePair[T, Events]]:
        pass
    @final
    def _GetItems(self, events: Events) -> Enumerable[IKeyValuePair[T, Events]]:
        return IteratorProvider[IKeyValuePair[T, Events]](lambda: self._GetItemsIterator(events))