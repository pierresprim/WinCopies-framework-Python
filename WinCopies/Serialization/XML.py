from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import Enum, Flag, auto
from typing import final
from xml.etree.ElementTree import Element, iterparse

from WinCopies import Abstract
from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, EnumeratorProvider, IteratorProvider, AbstractEnumerator, TryAsEnumerator, AsEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, TryAsStackHandler
from WinCopies.Enum import EnumerateFieldNames
from WinCopies.IO.Stream import ITextStreamReader
from WinCopies.Serialization import DataReader
from WinCopies.Typing.Delegate import NullablePredicate
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult

class Events(Flag):
    Start = auto()
    End = auto()

    @staticmethod
    def TryConvertFromString(value: str) -> Events|None:
        name: str|None = None

        for event in Events:
            if (name := event.name) is not None and name.lower() == value.lower():
                return event
        
        return None

def GetGenerator(stream: ITextStreamReader, events: Events) -> Generator[IKeyValuePair[Element, Events]]:
    event: Events|None = None

    for item in iterparse(stream.AsReader(), events=tuple(event.lower() for event in EnumerateFieldNames(events))):
        if (event := Events.TryConvertFromString(item[0])) is not None:
            yield DualResult[Element, Events](item[1], event)
def GetEnumerator(stream: ITextStreamReader, events: Events) -> IEnumerator[IKeyValuePair[Element, Events]]:
    return AsEnumerator(GetGenerator(stream, events))
def GetEnumerable(stream: ITextStreamReader, events: Events) -> IEnumerable[IKeyValuePair[Element, Events]]:
    return IteratorProvider[IKeyValuePair[Element, Events]](lambda: GetGenerator(stream, events))

class _LoopResult(Enum):
    Continue = 0
    Completed = 1
    SkipChildren = 2
    ExitLevel = 3

class _EnumerationDelegate(Abstract):
    def __init__(self) -> None:
        super().__init__()

        self.__current: IKeyValuePair[Element, Events]|None = None
    
    @final
    def GetCurrent(self) -> IKeyValuePair[Element, Events]|None:
        return self.__current
    
    def SetCurrent(self, value: IKeyValuePair[Element, Events]) -> _LoopResult:
        self.__current = value

        return _LoopResult.Continue
    
    @final
    def TrySetCurrent(self, item: IKeyValuePair[Element, Events]|None) -> _LoopResult:
        return _LoopResult.Completed if item is None else self.SetCurrent(item)
@final
class _EnumerationHandler(_EnumerationDelegate):
    @final
    class _EnumerationCookie(Abstract):
        def __init__(self, handler: IRecursiveStackedEnumerationHandler[Element]) -> None:
            super().__init__()
            
            self.__root: Element|None = None
            self.__handler: IRecursiveStackedEnumerationHandler[Element] = handler
            self.__onEnteringLevel: NullablePredicate[Element] = self.__GetLevelEntranceDelegate()
        
        def __OnEnteringLevel(self, item: Element) -> bool|None:
            result: bool|None = self.__handler.OnEnteringMainEnumerationLevel(item)

            if result is None:
                return None

            if result is True:
                self.__onEnteringLevel = lambda item: self.__handler.OnEnteringSubenumerationLevel(item)

                self.__root = item

                return True
            
            return False
        
        def __GetLevelEntranceDelegate(self) -> NullablePredicate[Element]:
            return lambda item: self.__OnEnteringLevel(item)
        
        def OnEnteringLevel(self, item: Element) -> bool|None:
            result: bool|None = self.__onEnteringLevel(item)

            if result is None:
                return None
            
            if result is True:
                self.__handler.OnEnteringEnumerationLevel(item)

                return True
            
            return False
        
        def OnExitingLevel(self, item: Element) -> bool|None:
            def getResult() -> bool|None:
                if item is self.__root:
                    self.__onEnteringLevel = self.__GetLevelEntranceDelegate()
                    self.__root = None

                    return self.__handler.OnExitingMainEnumerationLevel(item)
                
                return self.__handler.OnExitingSubenumerationLevel(item)
            
            result: bool|None = getResult()
            self.__handler.OnExitingEnumerationLevel(item)

            return result
    
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[Element]) -> None:
        super().__init__()

        self.__cookie: _EnumerationHandler._EnumerationCookie = _EnumerationHandler._EnumerationCookie(handler)
    
    def SetCurrent(self, value: IKeyValuePair[Element, Events]) -> _LoopResult:
        def getResult(result: bool|None, default: _LoopResult) -> _LoopResult:
            return _LoopResult.Continue if result is True else (_LoopResult.Completed if result is None else default)

        super().SetCurrent(value)
        
        match value.GetValue():
            case Events.Start:
                return getResult(self.__cookie.OnEnteringLevel(value.GetKey()), _LoopResult.SkipChildren)
            case Events.End:
                return getResult(self.__cookie.OnExitingLevel(value.GetKey()), _LoopResult.ExitLevel)
            case _:
                return _LoopResult.Continue

class Reader(DataReader[Element]):
    class _Enumerable(Abstract, IRecursivelyScannable[Element]):
        class _Enumerator(AbstractEnumerator[IKeyValuePair[Element, Events]]):
            def __init__(self, enumerator: IEnumerator[IKeyValuePair[Element, Events]], handler: IRecursiveStackedEnumerationHandler[Element]|None) -> None:
                super().__init__(enumerator)

                self.__delegate: _EnumerationDelegate = _EnumerationDelegate() if handler is None else _EnumerationHandler(handler)
                self.__continue: _LoopResult = _LoopResult.Continue
            
            @final
            def GetCurrent(self) -> IKeyValuePair[Element, Events]|None:
                return self.__delegate.GetCurrent()
            
            def _MoveNextOverride(self) -> bool:
                def moveNext() -> bool:
                    return enumerator.MoveNext()
                def getCurrent() -> IKeyValuePair[Element, Events]|None:
                    return enumerator.GetCurrent()
                
                def isEvent(currentEvent: Events, event: Events) -> bool:
                    return currentEvent == event
                def isEndEvent(currentEvent: Events) -> bool:
                    return isEvent(currentEvent, Events.End)
                
                def loop() -> bool:
                    if moveNext():
                        self.__continue = self.__delegate.TrySetCurrent(getCurrent())

                        return self.__continue != _LoopResult.Completed
                    
                    return False
                
                def skip(start: int) -> bool:
                    if moveNext():
                        current: IKeyValuePair[Element, Events]|None = getCurrent()

                        if current is None:
                            return False
                        
                        self.__continue = _LoopResult.Continue
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
                
                if self.__continue == _LoopResult.Completed:
                    return False
                
                enumerator: IEnumerator[IKeyValuePair[Element, Events]] = self._GetContainer()

                match self.__continue:
                    case _LoopResult.SkipChildren:
                        return skip(1)

                    case _LoopResult.ExitLevel:
                        return skip(2)
                    
                    case _:
                        return loop()
        
        def __init__(self, stream: ITextStreamReader) -> None:
            super().__init__()

            self.__stream: ITextStreamReader = stream
        
        @final
        def _GetStream(self) -> ITextStreamReader:
            return self.__stream
        
        @final
        def __GetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[Element]|None) -> IEnumerator[Element]|None:
            def getGenerator() -> Generator[Element]|None:
                def getItems(events: Events) -> Enumerable[IKeyValuePair[Element, Events]]:
                    return IteratorProvider[IKeyValuePair[Element, Events]](lambda: GetGenerator(self._GetStream(), events))
                
                def enumerateBoth(iterator: Iterator[IKeyValuePair[Element, Events]]) -> Generator[Element]:
                    element: Element|None = None

                    for item in iterator:
                        yield (element := item.GetKey())

                        if item.GetValue() == Events.End:
                            element.clear()
                
                def enumerateFIFO(iterator: Iterator[IKeyValuePair[Element, Events]]) -> Generator[Element]:
                    element: Element|None = None
                    value: Events|None = None

                    for item in iterator:
                        element = item.GetKey()

                        if (value := item.GetValue()) == Events.Start:
                            yield element
                        
                        elif value == Events.End:
                            element.clear()
                def enumerateLIFO(iterator: Iterator[IKeyValuePair[Element, Events]]) -> Generator[Element]:
                    element: Element|None = None

                    for item in iterator:
                        if item.GetValue() == Events.End:
                            yield (element := item.GetKey())

                            element.clear()
                
                if enumerationOrder == EnumerationOrder.LIFO and handler is None:
                    return enumerateLIFO(getItems(Events.End).GetEnumerator().AsIterator())
                
                enumerator: IEnumerator[IKeyValuePair[Element, Events]]|None = getItems(Events.Start|Events.End).TryGetEnumerator()
                
                if enumerator is None:
                    return None
                
                enumerator = Reader._Enumerable._Enumerator(enumerator, handler)
                
                return enumerateBoth(enumerator) if enumerationOrder == EnumerationOrder.Both else enumerateFIFO(enumerator)
            
            return TryAsEnumerator(getGenerator())
        
        @final
        def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[Element]|None = None) -> IEnumerator[Element]|None:
            return self.__GetRecursiveEnumerator(enumerationOrder, TryAsStackHandler(handler))
        @final
        def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[Element]|None = None) -> IEnumerator[Element]|None:
            return self.__GetRecursiveEnumerator(enumerationOrder, handler)
        
        @final
        def AsRecursivelyIterable(self) -> Iterable[Element]:
            return EnumeratorProvider[Element](self.TryGetRecursiveEnumerator)
    
    def __init__(self, stream: ITextStreamReader) -> None:
        super().__init__(stream)
    
    @final
    def _Parse(self, stream: ITextStreamReader) -> IRecursivelyScannable[Element]:
        return Reader._Enumerable(stream)