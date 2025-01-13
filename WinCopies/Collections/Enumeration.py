# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

from abc import ABC, abstractmethod
import collections.abc
from typing import final, Callable

from WinCopies import Delegates

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
    
    def GetCurrent(self) -> T|None:
        return self.__current
    
    @final
    def _SetCurrent(self, current: T) -> None:
        self.__current = current

class Iterator[T](Enumerator[T]):
    def __init__(self, iterator: SystemIterator[T]):
        super().__init__()

        self.__iterator: SystemIterator[T] = iterator
    
    @final
    def _GetIterator(self) -> SystemIterator[T]:
        return self.__iterator
    
    def IsResetSupported(self) -> bool:
        return False
    
    def _MoveNextOverride(self) -> bool:
        try:
            self._SetCurrent(self.__iterator.__next__())
            
            return True
        except StopIteration:
            return False

def FromIterator[T](iterator: SystemIterator[T]|None) -> Iterator[T]|None:
    return None if iterator is None else Iterator[T](iterator)

class Iterable[T](SystemIterable[T]):
    def __init__(self, iterable: SystemIterable[T]):
        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def __iter__(self) -> Iterator[T]:
        return Iterator[T](self.__iterable.__iter__())