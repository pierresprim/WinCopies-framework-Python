# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from abc import abstractmethod
from typing import final

from WinCopies import NullableBoolean, ToNullableBoolean
from WinCopies.Collections.Enumeration import SystemIterable, SystemIterator, IEnumerator, AbstractEnumerator, Iterator
from WinCopies.Collections.Linked.Singly import Stack
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Pairing import DualResult, DualNullableValueBool

class RecursiveEnumeratorBase[TEnumerationItems: SystemIterable[TEnumerationItems], TCookie, TStackItems: IEnumerator[TEnumerationItems]](AbstractEnumerator[TEnumerationItems]):
    def __init__(self, enumerator: IEnumerator[TEnumerationItems]):
        super().__init__(enumerator)
        
        self.__moveNext: Function[bool]|None = None
        self.__currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        self.__enumerators: Stack[TStackItems]|None = None
    
    @abstractmethod
    def _CreateStack(self) -> Stack[TStackItems]:
        pass

    @abstractmethod
    def _GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        pass
    @abstractmethod
    def _GetStackItemTryAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    @abstractmethod
    def _GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass

    @abstractmethod
    def _GetFirst(self) -> TCookie:
        pass
    @abstractmethod
    def _SetFirst(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> None:
        pass
    
    @final
    def _Push(self, item: TStackItems) -> None:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.Push(item)

    @final
    def _TryPeek(self) -> DualNullableValueBool[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        return self.__enumerators.TryPeek()
    @final
    def _TryPop(self) -> DualNullableValueBool[TStackItems]:
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
        if self._OnExitingSublevel():
            self._OnExitingLevel()

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
                item: TEnumerationItems = self.__currentEnumerator.GetCurrent()
                iterator: SystemIterator[TEnumerationItems] = item.__iter__()

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

            match tryEnterLevel():
                case NullableBoolean.BoolTrue:
                    return True
                case NullableBoolean.Null:
                    return False
                case _:
                    pass
            
            result: DualNullableValueBool[TStackItems] = self._TryPeek()

            if result.GetValue():
                if moveNext(result.GetKey()):
                    return True
                
                enumerator: IEnumerator[TEnumerationItems]|None = None
                result = self._TryPop()

                while result.GetValue():
                    match ToNullableBoolean(self.__OnExitingSublevel(self._GetStackItemAsCookie(result))):
                        case NullableBoolean.BoolTrue:
                            if moveNext(enumerator := self._GetStackItemTryAsEnumerator(result)):
                                setCurrentEnumerator(enumerator)

                                return True
                        
                        case NullableBoolean.Null:
                            return False
                    
                    result = self._TryPop()
        
            self.__OnExitingMainLevel(self._GetFirst())

            self.__moveNext = self.__MoveNext

            return self.__moveNext()
        
        current: TEnumerationItems|None = None

        while super()._MoveNextOverride():
            setCurrentEnumerator(self._GetEnumerator())

            match ToNullableBoolean(self.__OnEnteringMainLevel(current := self.__currentEnumerator.GetCurrent(), self.__currentEnumerator)):
                case NullableBoolean.BoolTrue:
                    self._SetFirst(current)
                    
                    self.__moveNext = moveNext

                    return True
                
                case NullableBoolean.Null:
                    return False
        
        return False
    
    @final
    def GetCurrent(self) -> TEnumerationItems|None:
        return None if self.__currentEnumerator is None else self.__currentEnumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnEnded(self) -> None:
        self.__currentEnumerator = None

        self.__enumerators.Clear()
        self.__enumerators = None

        self.__moveNext = None

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
class RecursiveEnumerator[T: SystemIterable[T]](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    @final
    def _CreateStack(self) -> Stack[IEnumerator[T]]:
        return Stack[IEnumerator[T]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> IEnumerator[T]:
        return enumerator
    @final
    def _GetStackItemTryAsEnumerator(self, item: IEnumerator[T]) -> IEnumerator[T]:
        return item
    @final
    def _GetStackItemAsCookie(self, item: IEnumerator[T]) -> None:
        return None
    
    @final
    def _GetFirst(self) -> None:
        return None
    @final
    def _SetFirst(self, item: T, enumerator: IEnumerator[T]) -> None:
        pass

class StackedRecursiveEnumerator[T: SystemIterable[T]](RecursiveEnumeratorBase[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

        self.__first: T|None = None
    
    @final
    def _CreateStack(self) -> Stack[DualResult[T, IEnumerator[T]]]:
        return Stack[DualResult[T, IEnumerator[T]]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> DualResult[T, IEnumerator[T]]:
        return DualResult[T, IEnumerator[T]](item, enumerator)
    @final
    def _GetStackItemTryAsEnumerator(self, item: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return item.GetValue()
    @final
    def _GetStackItemAsCookie(self, item: DualResult[T, IEnumerator[T]]) -> T:
        return item.GetKey()
    
    @final
    def _GetFirst(self) -> T:
        return self.__first
    @final
    def _SetFirst(self, item: T, enumerator: IEnumerator[T]) -> None:
        self.__first = item
    
    def _OnEnded(self) -> None:
        self.__first = None

        super()._OnEnded()