# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IInterface, NullableBoolean, ToNullableBoolean
from WinCopies.Collections.Enumeration import IIterable, SystemIterable, SystemIterator, IEnumerator, AbstractEnumerator, Iterator, AsIterator, AsEnumerator
from WinCopies.Collections.Linked.Singly import Stack
from WinCopies.Typing import InvalidOperationError, INullable
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Pairing import DualResult

class _RecursiveEnumeratorBase[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetEnumerationItems(self, enumerationItems: T) -> SystemIterable[T]:
        pass
class RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems](AbstractEnumerator[TEnumerationItems], _RecursiveEnumeratorBase[TEnumerationItems]):
    def __init__(self, enumerator: IEnumerator[TEnumerationItems]):
        super().__init__(enumerator)
        
        self.__moveNext: Function[bool]|None = None
        self.__first: TStackItems|None = None
        self.__currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        self.__enumerators: Stack[TStackItems]|None = None
    
    @abstractmethod
    def _GetStackItems(self, stackItems: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    
    @abstractmethod
    def _CreateStack(self) -> Stack[TStackItems]:
        pass

    @abstractmethod
    def _GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        pass
    @abstractmethod
    def _GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    @abstractmethod
    def _GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass
    
    @final
    def _Push(self, item: TStackItems) -> None:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.Push(item)

    @final
    def _TryPeek(self) -> INullable[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        return self.__enumerators.TryPeek()
    @final
    def _TryPop(self) -> INullable[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.TryPop()

        return self._TryPeek()

    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__enumerators = self._CreateStack()
            self.__moveNext = self.__MoveNext

            return True
        
        return False
    
    def _OnEnteringLevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> None:
        pass
    def _OnExitingLevel(self, cookie: TCookie) -> None:
        pass
    
    def _OnEnteringSublevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        return True
    def _OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        return True
    
    def _OnEnteringMainLevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        return True
    def _OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        return True
    
    @final
    def __OnEnteringSublevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        if self._OnEnteringSublevel(item, enumerator):
            self._OnEnteringLevel(item, enumerator)

            return True
        
        return False
    @final
    def __OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        if self._OnExitingSublevel(cookie):
            self._OnExitingLevel(cookie)

            return True
        
        return False
    
    @final
    def __OnEnteringMainLevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        if self._OnEnteringMainLevel(item, enumerator):
            self._OnEnteringLevel(item, enumerator)

            return True
        
        return False
    @final
    def __OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        if self._OnExitingMainLevel(cookie):
            self._OnExitingLevel(cookie)

            return True
        
        return False
    
    @final
    def __MoveNext(self) -> bool:
        def setCurrentEnumerator(value: IEnumerator[TEnumerationItems]) -> None:
            self.__currentEnumerator = value
        
        def moveNext() -> bool:
            def getEnumerator() -> DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]:
                item: TEnumerationItems = self.__currentEnumerator.GetCurrent() # type: ignore
                iterator: SystemIterator[TEnumerationItems] = self._GetEnumerationItems(item).__iter__()

                return DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]](item, iterator if isinstance(iterator, IEnumerator) else Iterator[TEnumerationItems](iterator))
            
            def moveNext(enumerator: IEnumerator[TEnumerationItems]) -> bool:
                return enumerator.MoveNext()
            
            def tryEnterLevel() -> NullableBoolean:
                def processEnumerator(currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> NullableBoolean:
                    while enumerator.MoveNext():
                        result: bool|None = self.__OnEnteringSublevel(currentItem, enumerator)
                        
                        if result is None:
                            return NullableBoolean.Null
                        
                        if result is True:
                            self._Push(self._GetStackItem(currentItem, enumerator))

                            setCurrentEnumerator(enumerator)
                            
                            return NullableBoolean.BoolTrue
                    
                    return NullableBoolean.BoolFalse
                
                result: DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]] = getEnumerator()
                
                return processEnumerator(result.GetKey(), result.GetValue())
            
            def loop() -> bool|None:
                nonlocal result

                enumerator: IEnumerator[TEnumerationItems]|None = None
                
                def loop(result: TStackItems) -> bool|None:
                    nonlocal enumerator

                    match ToNullableBoolean(self.__OnExitingSublevel(self._GetStackItemAsCookie(result))):
                        case NullableBoolean.BoolTrue:
                            if moveNext(enumerator := self._GetStackItemAsEnumerator(result)):
                                setCurrentEnumerator(enumerator)

                                return True
                        
                        case NullableBoolean.Null:
                            return False
                        
                        case _:
                            return None
                    
                    return None
                
                result = self._TryPop()
                loopResult: bool|None = None

                while result.HasValue():
                    if (loopResult := loop(result.GetValue())) is not None:
                        return loopResult
                    
                    result = self._TryPop()
                
                return None

            match tryEnterLevel():
                case NullableBoolean.BoolTrue:
                    return True
                case NullableBoolean.Null:
                    return False
                case _:
                    pass
            
            result: INullable[TStackItems] = self._TryPeek()

            if result.HasValue():
                if moveNext(self._GetStackItems(result.GetValue())):
                    return True
                
                loopResult: bool|None = loop()

                if loopResult is not None:
                    return loopResult
        
            self.__OnExitingMainLevel(self._GetStackItemAsCookie(self.__first)) # type: ignore

            self.__moveNext = self.__MoveNext

            return self.__moveNext()
        
        current: TEnumerationItems|None = None

        while super()._MoveNextOverride():
            setCurrentEnumerator(self._GetEnumerator())

            match ToNullableBoolean(self.__OnEnteringMainLevel(current := self.__currentEnumerator.GetCurrent(), self.__currentEnumerator)): # type: ignore
                case NullableBoolean.BoolTrue:
                    self.__first = self._GetStackItemAsCookie(self._GetStackItem(current, self.__currentEnumerator)) # type: ignore
                    
                    self.__moveNext = moveNext

                    return True
                
                case NullableBoolean.Null:
                    return False
                
                case _:
                    continue
        
        return False
    
    @final
    def GetCurrent(self) -> TEnumerationItems|None:
        return None if self.__currentEnumerator is None else self.__currentEnumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return False if self.__moveNext is None else self.__moveNext()
    
    def _OnEnded(self) -> None:
        self.__currentEnumerator = None
        self.__first = None

        if self.__enumerators is not None:
            self.__enumerators.Clear()
            self.__enumerators = None

        self.__moveNext = None

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
class RecursiveEnumerator[T](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    @final
    def _GetStackItems(self, stackItems: IEnumerator[T]) -> IEnumerator[T]:
        return stackItems
    
    @final
    def _CreateStack(self) -> Stack[IEnumerator[T]]:
        return Stack[IEnumerator[T]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> IEnumerator[T]:
        return enumerator
    @final
    def _GetStackItemAsEnumerator(self, item: IEnumerator[T]) -> IEnumerator[T]:
        return item
    @final
    def _GetStackItemAsCookie(self, item: IEnumerator[T]) -> None:
        return None
class StackedRecursiveEnumerator[T](RecursiveEnumeratorBase[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    @final
    def _GetStackItems(self, stackItems: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return stackItems.GetValue()
    
    @final
    def _CreateStack(self) -> Stack[DualResult[T, IEnumerator[T]]]:
        return Stack[DualResult[T, IEnumerator[T]]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> DualResult[T, IEnumerator[T]]:
        return DualResult[T, IEnumerator[T]](item, enumerator)
    @final
    def _GetStackItemAsEnumerator(self, item: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return item.GetValue()
    @final
    def _GetStackItemAsCookie(self, item: DualResult[T, IEnumerator[T]]) -> T:
        return item.GetKey()

class IRecursivelyIterable[T](IIterable[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def TryGetRecursiveIterator(self) -> SystemIterator[T]|None:
        pass
    @final
    def GetRecursiveIterator(self) -> SystemIterator[T]:
        return AsIterator(self.TryGetRecursiveIterator())

class RecursivelyIterable[T](IRecursivelyIterable[T]):
    class __IEnumerator(_RecursiveEnumeratorBase[T]):
        def __init__(self):
            super().__init__()
        
        @abstractmethod
        def _GetIterable(self) -> RecursivelyIterable[T]:
            pass
        
        @final
        def _GetEnumerationItems(self, enumerationItems: T) -> SystemIterable[T]:
            return self._GetIterable()._AsRecursivelyIterable(enumerationItems)

    class Enumerator(RecursiveEnumerator[T], __IEnumerator[T]):
        def __init__(self, iterable: RecursivelyIterable[T], enumerator: IEnumerator[T]):
            super().__init__(enumerator)

            self.__iterable: RecursivelyIterable[T] = iterable
        
        @final
        def _GetIterable(self) -> RecursivelyIterable[T]:
            return self.__iterable
    class StackedEnumerator(StackedRecursiveEnumerator[T], __IEnumerator[T]):
        def __init__(self, iterable: RecursivelyIterable[T], enumerator: IEnumerator[T]):
            super().__init__(enumerator)

            self.__iterable: RecursivelyIterable[T] = iterable
        
        @final
        def _GetIterable(self) -> RecursivelyIterable[T]:
            return self.__iterable
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsRecursivelyIterable(self, container: T) -> IRecursivelyIterable[T]:
        pass
    
    def _TryGetRecursiveIterator(self, iterator: IEnumerator[T]) -> SystemIterator[T]|None:
        return RecursivelyIterable[T].Enumerator(self, iterator)

    def TryGetRecursiveIterator(self) -> SystemIterator[T]|None:
        iterator: SystemIterator[T]|None = self.TryGetIterator()

        return None if iterator is None else self._TryGetRecursiveIterator(AsEnumerator(iterator))