# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from typing import final

from WinCopies.Collections.Enumeration import SystemIterable, SystemIterator, IEnumerator, AbstractEnumerator, Iterator
from WinCopies.Collections.Linked.Singly import Stack
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Pairing import DualNullableValueBool

class RecursiveEnumerator[T: SystemIterable[T]](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
        
        self.__currentEnumerator: IEnumerator[T]|None = None
        self.__enumerators: Stack[IEnumerator[T]]|None = None
        self.__moveNext: Function[bool]|None = None
    
    @final
    def __MoveNext(self) -> bool:
        if super()._MoveNextOverride():
            def setCurrentEnumerator(value: IEnumerator[T]) -> None:
                self.__currentEnumerator = value
            
            def moveNext() -> bool:
                def getEnumerator() -> IEnumerator[T]:
                    iterator: SystemIterator[T] = self.GetCurrent().__iter__()

                    return iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator)
                
                enumerator: IEnumerator[T] = getEnumerator()

                if enumerator.MoveNext():
                    self.__enumerators.Push(enumerator)

                    setCurrentEnumerator(enumerator)

                    return True
                
                def moveNext(enumerator: DualNullableValueBool[IEnumerator[T]]) -> bool:
                    return enumerator.GetKey().MoveNext()
                
                result: DualNullableValueBool[IEnumerator[T]] = self.__enumerators.TryPeek()

                if result.GetValue():
                    if moveNext(result):
                        return True
                    
                    def tryPop() -> DualNullableValueBool[IEnumerator[T]]:
                        self.__enumerators.TryPop()

                        return self.__enumerators.TryPeek()
                    
                    result = tryPop()

                    while result.GetValue():
                        if moveNext(result):
                            setCurrentEnumerator(enumerator)

                            return True
                        
                        result = tryPop()

                self.__moveNext = self.__MoveNext

                return self.__moveNext()

            setCurrentEnumerator(self._GetEnumerator())

            self.__moveNext = moveNext

            return True
        
        return False
    
    @final
    def GetCurrent(self) -> T|None:
        return None if self.__currentEnumerator is None else self.__currentEnumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnStarting(self) -> bool:
        self.__enumerators = Stack[IEnumerator[T]]()
        self.__moveNext = self.__MoveNext

        return super()._OnStarting()
    
    def _OnEnded(self) -> None:
        self.__currentEnumerator = None
        self.__enumerators = None
        self.__moveNext = None

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass