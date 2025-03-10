# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

import collections.abc

from abc import abstractmethod
from typing import final

from WinCopies import Delegates
from WinCopies.Collections import ICountable
from WinCopies.Typing.Delegate import Converter, Function

type SystemIterable[T] = collections.abc.Iterable[T]
type SystemIterator[T] = collections.abc.Iterator[T]

class IEnumerator[T](collections.abc.Iterator[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def IsStarted(self) -> bool:
        pass
    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass
    @abstractmethod
    def MoveNext(self) -> bool:
        pass
    @abstractmethod
    def Stop(self) -> None:
        pass
    @abstractmethod
    def TryReset(self) -> bool|None:
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
    
    def IsStarted(self) -> bool:
        return False
    def GetCurrent(self) -> T|None:
        return None
    def MoveNext(self) -> bool:
        return False
    def Stop(self) -> None:
        pass
    def TryReset(self) -> bool|None:
        return None
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

class ICountableIterable[T](ICountable, IIterable[T]):
    def __init__(self):
        super().__init__()

class EnumeratorBase[T](IEnumerator[T]):
    def __init__(self):
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveNext
        self.__isStarted: bool = False
        self.__hasProcessedItems: bool = False
    
    @final
    def __MoveNext(self) -> bool:
        def setCompletedMoveNext() -> None:
            self.__moveNextFunc = Delegates.BoolFalse
            
            self.__OnCompleted()
        
        def moveNext() -> bool:
            if self._MoveNextOverride():
                return True

            setCompletedMoveNext()

            return False
        
        if self._OnStarting():
            self.__isStarted = True
            
            if self._MoveNextOverride():
                self.__moveNextFunc = moveNext
                
                self.__hasProcessedItems = True
                
                return True
        
        setCompletedMoveNext()

        return False
    
    @final
    def __OnTerminated(self, completed: bool) -> None:
        self.__isStarted = False

        self._OnTerminated(completed)
        self._OnEnded()
    
    @final
    def __OnCompleted(self) -> None:
        self.__OnTerminated(True)
        self._OnCompleted()
    
    @final
    def IsStarted(self):
        return self.__isStarted
    
    @abstractmethod
    def _MoveNextOverride(self) -> bool:
        pass
    @abstractmethod
    def _ResetOverride(self) -> bool:
        pass
    def _OnStarting(self) -> bool:
        return True
    def _OnCompleted(self) -> None:
        pass
    @abstractmethod
    def _OnStopped(self) -> None:
        pass
    def _OnTerminated(self, completed: bool) -> None:
        pass
    def _OnEnded(self) -> None:
        pass
    @final
    def MoveNext(self) -> bool:
        return self.__moveNextFunc()
    
    @final
    def Stop(self) -> None:
        self.__OnTerminated(False)
        self._OnStopped()
    
    @final
    def TryReset(self) -> bool|None:
        def onReset() -> None:
            self.__moveNextFunc = Delegates.BoolFalse
        
        if self.IsResetSupported():
            if self.IsStarted():
                self.Stop()
            
            if self._ResetOverride():
                self.__moveNextFunc = self.__MoveNext
                self.__hasProcessedItems = False
                
                return True
            
            onReset()
            
            return False
        
        onReset()
        
        return None
    
    @final
    def HasProcessedItems(self) -> bool:
        return self.__hasProcessedItems

class Enumerator[T](EnumeratorBase[T]):
    def __init__(self):
        super().__init__()

        self.__current: T|None = None
    
    def _OnEnded(self) -> None:
        self.__current = None

        super()._OnEnded()
    
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
    
    def _OnStopped(self) -> None:
        pass

    def _ResetOverride(self) -> bool:
        return False

def AsEnumerator[T](iterator: SystemIterator[T]|None) -> Iterator[T]|None:
    return None if iterator is None else (iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator))

class Iterable[T](IIterable[T]):
    def __init__(self, iterable: SystemIterable[T]):
        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return AsEnumerator(self.__iterable.__iter__())
    
    @staticmethod
    def Create(iterable: SystemIterable[T]) -> IIterable[T]:
        if iterable is None:
            raise ValueError("The iterable can not be None.")
        
        return iterable if isinstance(iterable, IIterable) else Iterable(iterable)
    @staticmethod
    def TryCreate(iterable: SystemIterable[T]) -> IIterable[T]|None:
        return None if iterable is None else (iterable if isinstance(iterable, IIterable) else Iterable(iterable))

class IteratorProvider[T](IIterable[T]):
    def __init__(self, iteratorProvider: Function[SystemIterator[T]]|None):
        self.__iteratorProvider: Function[SystemIterator[T]]|None = iteratorProvider
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return None if self.__iteratorProvider is None else self.__iteratorProvider()

class AbstractEnumeratorBase[TIn, TOut, TEnumerator: IEnumerator[TIn]](EnumeratorBase[TOut]):
    def __init__(self, enumerator: TEnumerator):
        super().__init__()
        
        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetEnumerator(self) -> TEnumerator:
        return self.__enumerator
    
    @final
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
    
    def _MoveNextOverride(self) -> bool:
        return self.__enumerator.MoveNext()
    
    def _ResetOverride(self) -> bool:
        return self.__enumerator.TryReset()
class AbstractEnumerator[T](AbstractEnumeratorBase[T, T, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def GetCurrent(self) -> T|None:
        return self.__enumerator.GetCurrent()

class AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumerator[TIn]](IEnumerator[TOut]):
    def __init__(self, enumerator: TEnumerator):
        super().__init__()

        self.__enumerator: TEnumerator = enumerator
        self.__moveNextFunc: Function[bool] = self.__MoveNext
    
    @final
    def _GetEnumerator(self) -> TEnumerator:
        return self.__enumerator
    
    def _MoveNext(self) -> bool:
        return self.__enumerator.MoveNext()
    
    @final
    def __MoveNext(self) -> bool:
        if self._OnStarting():
            def moveNext() -> bool:
                if self._MoveNext():
                    return True
                
                self.__moveNextFunc = Delegates.BoolFalse

                return False
            
            if moveNext():
                self.__moveNextFunc = moveNext

                return True
        
        self.__OnCompleted()
        
        return False
    
    @final
    def __OnTerminated(self, completed: bool) -> None:
        self._OnTerminated(completed)
        self._OnEnded()
    
    @final
    def __OnCompleted(self) -> None:
        self.__OnTerminated(True)
        self._OnCompleted()
    
    def _OnStarting(self) -> bool:
        return True
    def _OnCompleted(self) -> None:
        pass
    def _OnTerminated(self, completed: bool) -> None:
        pass
    def _OnEnded(self) -> None:
        pass
    
    @final
    def IsStarted(self) -> bool:
        return self.__enumerator.IsStarted()
    @final
    def MoveNext(self) -> bool:
        return self.__moveNextFunc()
    @final
    def Stop(self) -> None:
        self.__enumerator.Stop()

        self.__OnTerminated(False)
    
    @final
    def TryReset(self) -> bool|None:
        if self.IsStarted():
            self.Stop()
        
        result: bool|None = self.__enumerator.TryReset()

        if result is True:
            self.__moveNextFunc = self.__MoveNext

            return True
        
        self.__moveNextFunc = Delegates.BoolFalse
        
        return result
    @final
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
    @final
    def HasProcessedItems(self) -> bool:
        return self.__enumerator.HasProcessedItems()

class AbstractionEnumerator[TIn, TOut](AbstractionEnumeratorBase[TIn, TOut, IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]):
        super().__init__(enumerator)

class DelegateEnumerator[T](EnumeratorBase[T]):
    def __init__(self):
        super().__init__()

        self.__moveNext: Function[bool]|None
    
    @abstractmethod
    def _OnMoveNext(self) -> Function[bool]|None:
        pass
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            func: Function[bool]|None = self._OnMoveNext()

            if func is None:
                return False
            
            self.__moveNext = func

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__moveNext = None

class ConverterEnumerator[TIn, TOut](AbstractionEnumerator[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn], selector: Converter[TIn, TOut]):
        super().__init__(enumerator)

        self.__selector: Converter[TIn, TOut] = selector
        self.__current: TOut|None = None
    
    def _MoveNext(self) -> bool:
        if super()._MoveNext():
            self.__current = self.__selector(self._GetEnumerator().GetCurrent())

            return True
        
        return False
    
    def _OnEnded(self) -> None:
        self.__current = None
        
        super()._OnEnded()
    
    @final
    def GetCurrent(self) -> TOut|None:
        return self.__current