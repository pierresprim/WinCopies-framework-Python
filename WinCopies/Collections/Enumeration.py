# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

from abc import ABC, abstractmethod
import collections.abc
from typing import final, Callable

from WinCopies import Delegates
from WinCopies.Collections.Linked.Singly import Stack
from WinCopies.Typing.Pairing import DualNullableValueBool

type SystemIterable[T] = collections.abc.Iterable[T]
type SystemIterator[T] = collections.abc.Iterator[T]

class IEnumerator[T](ABC, collections.abc.Iterator[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass
    @abstractmethod
    def MoveNext(self) -> bool:
        pass
    @abstractmethod
    def Reset(self) -> bool:
        pass
    @abstractmethod
    def IsResetSupported(self) -> bool:
        pass
    @abstractmethod
    def HasProcessedItems(self) -> bool:
        pass
    
    @final
    def __next__(self) -> T|None:
        if self.MoveNext():
            return self.GetCurrent()
        
        else:
            raise StopIteration
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return self

@final
class EmptyEnumerator[T](IEnumerator[T]):
    def __init__(self):
        super().__init__()
    
    def GetCurrent(self) -> T|None:
        return None
    def MoveNext(self) -> bool:
        return False
    def Reset(self) -> bool:
        return False
    def IsResetSupported(self) -> bool:
        return False
    def HasProcessedItems(self) -> bool:
        return False

class IIterable[T](collections.abc.Iterable[T]):
    @abstractmethod
    def TryGetIterator(self) -> SystemIterator[T]|None:
        pass
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        enumerator: SystemIterator[T]|None = self.TryGetIterator()

        return EmptyEnumerator[T]() if enumerator is None else enumerator

class EnumeratorBase[T](IEnumerator[T]):
    def __init__(self):
        self.__moveNext: Callable[[], bool] = self.__GetMoveNext()
        self.__hasProcessedItems: bool = False
    
    @final
    def __GetMoveNext(self) -> Callable[[], bool]:
        def moveNext() -> bool:
            def setCompletedMoveNext() -> None:
                self.__moveNext = Delegates.BoolFalse
            
            def moveNext() -> bool:
                if self._MoveNextOverride():
                    return True
                
                self._OnCompleted()

                setCompletedMoveNext()

                return False
            
            if self._OnStarting() and self._MoveNextOverride():
                self.__moveNext = moveNext

                self.__hasProcessedItems = True

                return True
            
            setCompletedMoveNext()

            return False
        
        return moveNext
    #@protected
    @abstractmethod
    def _MoveNextOverride(self) -> bool:
        pass
    #@protected
    @abstractmethod
    def _ResetOverride(self) -> bool:
        pass
    @abstractmethod
    def GetCurrent(self):
        pass
    @abstractmethod
    def IsResetSupported(self) -> bool:
        pass
    #@protected
    def _OnStarting(self) -> bool:
        return True
    #@protected
    def _OnCompleted(self) -> None:
        pass
    @final
    def MoveNext(self) -> bool:
        return self.__moveNext()
    
    @final
    def Reset(self) -> bool:
        if self.IsResetSupported() and self._ResetOverride():
            self.__moveNext = self.__GetMoveNext()
            self.__hasProcessedItems = False

            return True
        
        return False
    
    @final
    def HasProcessedItems(self) -> bool:
        return self.__hasProcessedItems

class Enumerator[T](EnumeratorBase[T]):
    def __init__(self):
        super().__init__()
        self.__current: T|None = None
    
    def _OnCompleted(self) -> None:
        self.__current = None
    
    def _ResetOverride(self) -> bool:
        return True
    
    @final
    def GetCurrent(self) -> T|None:
        return self.__current
    
    @final
    def _SetCurrent(self, current: T|None) -> None:
        self.__current = current

class Iterator[T](Enumerator[T]):
    def __init__(self, iterator: SystemIterator[T]):
        super().__init__()

        self.__iterator: SystemIterator[T] = iterator
    
    @final
    def _GetIterator(self) -> SystemIterator[T]:
        return self.__iterator
    
    @final
    def IsResetSupported(self) -> bool:
        return False
    
    def _MoveNextOverride(self) -> bool:
        try:
            self._SetCurrent(self.__iterator.__next__())
            
            return True
        except StopIteration:
            self._SetCurrent(None)

            return False

def FromIterator[T](iterator: SystemIterator[T]|None) -> Iterator[T]|None:
    return None if iterator is None else Iterator[T](iterator)

class Iterable[T](IIterable[T]):
    def __init__(self, iterable: SystemIterable[T]):
        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return FromIterator(self.__iterable.__iter__())

class AbstractEnumeratorBase[TItems, TEnumerator: IEnumerator[TItems]](EnumeratorBase[TItems]):
    def __init__(self, enumerator: TEnumerator):
        super().__init__()
        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetEnumerator(self) -> TEnumerator:
        return self.__enumerator
    
    @final
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
    
    def GetCurrent(self) -> TItems|None:
        return self.__enumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__enumerator.MoveNext()
    
    def _ResetOverride(self) -> bool:
        return True
class AbstractEnumerator[T](AbstractEnumeratorBase[T, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

class RecursiveEnumerator[T: SystemIterable[T]](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
        
        self.__currentEnumerator: IEnumerator[T]|None = None
        self.__enumerators: Stack[IEnumerator[T]]|None = None
        self.__moveNext: Callable[[], bool]|None = None
    
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
        return self.__currentEnumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnStarting(self) -> bool:
        self.__enumerators = Stack[IEnumerator[T]]()
        self.__moveNext = self.__MoveNext

        return super()._OnStarting()
    def _OnCompleted(self) -> None:
        self.__currentEnumerator = None
        self.__enumerators = None
        self.__moveNext = None