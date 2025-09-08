# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

import collections.abc

from abc import abstractmethod
from typing import final

from WinCopies import Delegates, IInterface
from WinCopies.Collections import ICountable
from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Delegate import Converter, Function

type SystemIterable[T] = collections.abc.Iterable[T]
type SystemIterator[T] = collections.abc.Iterator[T]

class IEnumeratorBase(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def IsStarted(self) -> bool:
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
class IEnumerator[T](collections.abc.Iterator[T], IEnumeratorBase):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass
    
    @final
    def __next__(self) -> T:
        if self.MoveNext():
            current: T|None = self.GetCurrent()

            if current is None:
                raise StopIteration
            
            return current
        
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

def AsIterator[T](iterator: SystemIterator[T]|None) -> SystemIterator[T]:
    return EmptyEnumerator[T]() if iterator is None else iterator

class IIterable[T](collections.abc.Iterable[T], IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetIterator(self) -> SystemIterator[T]|None:
        pass
    @final
    def GetIterator(self) -> SystemIterator[T]:
        return AsIterator(self.TryGetIterator())
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return self.GetIterator()

class ICountableIterable[T](IIterable[T], ICountable):
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

def __AsEnumerator[T](iterator: SystemIterator[T]) -> IEnumerator[T]:
    return iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator)

def AsEnumerator[T](iterator: SystemIterator[T]) -> IEnumerator[T]:
    if iterator is None: # type: ignore
        raise ValueError()
    
    return __AsEnumerator(iterator)
def TryAsEnumerator[T](iterator: SystemIterator[T]|None) -> IEnumerator[T]|None:
    return None if iterator is None else __AsEnumerator(iterator)

class Iterable[T](IIterable[T]):
    def __init__(self, iterable: SystemIterable[T]):
        super().__init__()

        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def TryGetIterator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(self.__iterable.__iter__())
    
    @staticmethod
    def Create(iterable: SystemIterable[T]) -> IIterable[T]:
        return iterable if isinstance(iterable, IIterable) else Iterable(iterable)
    @staticmethod
    def TryCreate(iterable: SystemIterable[T]|None) -> IIterable[T]|None:
        return None if iterable is None else (iterable if isinstance(iterable, IIterable) else Iterable(iterable))

class IteratorProvider[T](IIterable[T]):
    def __init__(self, iteratorProvider: Function[SystemIterator[T]]|None):
        super().__init__()
        
        self.__iteratorProvider: Function[SystemIterator[T]]|None = iteratorProvider
    
    @final
    def TryGetIterator(self) -> IEnumerator[T]|None:
        return None if self.__iteratorProvider is None else TryAsEnumerator(self.__iteratorProvider())

class AbstractEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](EnumeratorBase[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self, enumerator: TEnumerator):
        super().__init__()
        
        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetEnumerator(self) -> TEnumerator:
        return self.__enumerator
    @final
    def _GetContainer(self) -> TEnumerator:
        return self._GetEnumerator()
    
    @final
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
    
    def _MoveNextOverride(self) -> bool:
        return self.__enumerator.MoveNext()
    
    def _ResetOverride(self) -> bool:
        return self.__enumerator.TryReset() is True
class AbstractEnumerator[T](AbstractEnumeratorBase[T, T, IEnumerator[T]], IGenericConstraintImplementation[IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def GetCurrent(self) -> T|None:
        return self._GetEnumerator().GetCurrent()

class __AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](IEnumerator[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self):
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveNext
    
    @abstractmethod
    def _GetEnumerator(self) -> TEnumerator:
        pass
    @final
    def _GetContainer(self) -> TEnumerator:
        return self._GetEnumerator()
    
    def _MoveNext(self) -> bool:
        return self._GetEnumerator().MoveNext()
    
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
        return self._GetEnumerator().IsStarted()
    @final
    def MoveNext(self) -> bool:
        return self.__moveNextFunc()
    @final
    def Stop(self) -> None:
        self._GetEnumerator().Stop()

        self.__OnTerminated(False)
    
    @final
    def TryReset(self) -> bool|None:
        if self.IsStarted():
            self.Stop()
        
        result: bool|None = self._GetEnumerator().TryReset()

        if result is True:
            self.__moveNextFunc = self.__MoveNext

            return True
        
        self.__moveNextFunc = Delegates.BoolFalse
        
        return result
    @final
    def IsResetSupported(self) -> bool:
        return self._GetEnumerator().IsResetSupported()
    @final
    def HasProcessedItems(self) -> bool:
        return self._GetEnumerator().HasProcessedItems()

class AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](__AbstractionEnumeratorBase[TIn, TOut, TEnumerator]):
    def __init__(self, enumerator: TEnumerator):
        super().__init__()

        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetEnumerator(self) -> TEnumerator:
        return self.__enumerator
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

            return func()

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return False if self.__moveNext is None else self.__moveNext()
    
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
            current: TIn|None = self._GetEnumerator().GetCurrent()

            if current is None:
                return False

            self.__current = self.__selector(current)

            return True
        
        return False
    
    def _OnEnded(self) -> None:
        self.__current = None
        
        super()._OnEnded()
    
    @final
    def GetCurrent(self) -> TOut|None:
        return self.__current

class AccessorBase[TIn, TOut, TEnumerator: IEnumeratorBase](__AbstractionEnumeratorBase[TIn, TOut, TEnumerator]):
    def __init__(self, func: Function[TEnumerator]):
        def getEnumerator() -> TEnumerator:
            self.__enumerator = func()
            self.__func = lambda: self.__enumerator

            return self.__enumerator

        super().__init__()

        self.__func: Function[TEnumerator] = getEnumerator
        self.__enumerator: TEnumerator = None # type: ignore
    
    @final
    def _GetEnumerator(self) -> TEnumerator:
        return self.__func()
    
    @final
    def _MoveNext(self) -> bool:
        return self._GetEnumerator().MoveNext()
class Accessor[T](AccessorBase[T, T, IEnumerator[T]], IGenericConstraintImplementation[IEnumerator[T]]):
    def __init__(self, func: Function[IEnumerator[T]]):
        super().__init__(func)
    
    @final
    def GetCurrent(self) -> T|None:
        return self._GetEnumerator().GetCurrent()