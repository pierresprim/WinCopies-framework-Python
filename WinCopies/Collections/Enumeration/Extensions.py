# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from typing import final

from WinCopies import NullableBoolean, ToNullableBoolean
from WinCopies.Collections.Enumeration import SystemIterable, SystemIterator, IEnumerator, AbstractEnumerator, Iterator
from WinCopies.Collections.Linked.Singly import Stack
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Pairing import DualResult, DualNullableValueBool

class RecursiveEnumerator[T: SystemIterable[T]](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
        
        self.__currentEnumerator: IEnumerator[T]|None = None
        self.__enumerators: Stack[IEnumerator[T]]|None = None
        self.__moveNext: Function[bool]|None = None
    
    def _OnEnteringLevel(self, item: T, enumerator: IEnumerator[T]) -> None:
        pass
    def _OnExitingLevel(self) -> None:
        pass
    
    def _OnEnteringSublevel(self, item: T, enumerator: IEnumerator[T]) -> bool|None:
        return True
    def _OnExitingSublevel(self) -> bool|None:
        return True
    
    def _OnEnteringMainLevel(self, item: T, enumerator: IEnumerator[T]) -> bool|None:
        return True
    def _OnExitingMainLevel(self) -> bool|None:
        return True
    
    def __OnEnteringSublevel(self, item: T, enumerator: IEnumerator[T]) -> bool|None:
        if self._OnEnteringSublevel(item, enumerator):
            self._OnEnteringLevel(item, enumerator)

            return True
        
        return False
    def __OnExitingSublevel(self) -> bool|None:
        if self._OnExitingSublevel():
            self._OnExitingLevel()

            return True
        
        return False
    
    def __OnEnteringMainLevel(self, item: T, enumerator: IEnumerator[T]) -> bool|None:
        if self._OnEnteringMainLevel(item, enumerator):
            self._OnEnteringLevel(item, enumerator)

            return True
        
        return False
    def __OnExitingMainLevel(self) -> bool|None:
        if self._OnExitingMainLevel():
            self._OnExitingLevel()

            return True
        
        return False
    
    @final
    def __MoveNext(self) -> bool:
        while super()._MoveNextOverride():
            def setCurrentEnumerator(value: IEnumerator[T]) -> None:
                self.__currentEnumerator = value
            
            def moveNext() -> bool:
                def getEnumerator() -> DualResult[T, IEnumerator[T]]:
                    iterator: SystemIterator[T] = self.__currentEnumerator.GetCurrent().__iter__()

                    return DualResult[T, IEnumerator[T]](iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator))
                
                def moveNext(enumerator: IEnumerator[T]) -> bool:
                    return enumerator.MoveNext()
                    
                def tryPop() -> DualNullableValueBool[IEnumerator[T]]:
                    self.__enumerators.TryPop()

                    return self.__enumerators.TryPeek()
                
                def tryEnterLevel() -> NullableBoolean:
                    def processEnumerator(currentItem: T, enumerator: IEnumerator[T]) -> NullableBoolean:
                        while enumerator.MoveNext():
                            result: bool|None = self.__OnEnteringSublevel(currentItem, enumerator)
                            
                            if result is None:
                                return NullableBoolean.Null
                            
                            if result is True:
                                self.__enumerators.Push(enumerator)

                                setCurrentEnumerator(enumerator)
                                
                                return NullableBoolean.BoolTrue
                        
                        return NullableBoolean.BoolFalse
                    
                    result: DualResult[T, IEnumerator[T]] = getEnumerator()
                    
                    return processEnumerator(result.GetKey(), result.GetValue())

                match tryEnterLevel():
                    case NullableBoolean.BoolTrue:
                        return True
                    case NullableBoolean.Null:
                        return False
                
                result: DualNullableValueBool[IEnumerator[T]] = self.__enumerators.TryPeek()

                if result.GetValue():
                    if moveNext(result.GetKey()):
                        return True
                    
                    enumerator: IEnumerator[T]|None = None
                    result = tryPop()

                    while result.GetValue():
                        match ToNullableBoolean(self.__OnExitingSublevel()):
                            case NullableBoolean.BoolTrue:
                                if moveNext(enumerator := result.GetKey()):
                                    setCurrentEnumerator(enumerator)

                                    return True
                            
                            case NullableBoolean.Null:
                                return False
                        
                        result = tryPop()

                self.__moveNext = self.__MoveNext

                return self.__moveNext()

            setCurrentEnumerator(self._GetEnumerator())

            match ToNullableBoolean(self.__OnEnteringMainLevel(self.__currentEnumerator.GetCurrent(), self.__currentEnumerator)):
                case NullableBoolean.BoolTrue:
                    self.__moveNext = moveNext

                    return True
                
                case NullableBoolean.Null:
                    return False
        
        self.__OnExitingMainLevel()
        
        return False
    
    @final
    def GetCurrent(self) -> T|None:
        return None if self.__currentEnumerator is None else self.__currentEnumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__enumerators = Stack[IEnumerator[T]]()
            self.__moveNext = self.__MoveNext

            return True
        
        return False
    
    def _OnEnded(self) -> None:
        self.__currentEnumerator = None

        self.__enumerators.Clear()
        self.__enumerators = None

        self.__moveNext = None

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass