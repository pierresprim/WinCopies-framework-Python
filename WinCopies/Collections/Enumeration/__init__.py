# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

from abc import abstractmethod
from collections.abc import Iterable as SystemIterable, Iterator as SystemIterator
from typing import final

from WinCopies import Delegates, IInterface
from WinCopies.Collections import ICountable, Countable
from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, IEquatableItem
from WinCopies.Typing.Delegate import Converter, Function

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
class IEnumerator[T](IEnumeratorBase):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass

    @abstractmethod
    def AsIterator(self) -> SystemIterator[T]:
        pass

class IteratorBase[T](SystemIterator[T], IEnumerator[T]):
    def __init__(self):
        super().__init__()
    
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
    def AsIterator(self) -> SystemIterator[T]:
        return self
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return self

@final
class __EmptyEnumerator[T](IteratorBase[T], IEnumerator[T]):
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

__emptyEnumerator = __EmptyEnumerator[None]()

def GetEmptyEnumerator[T]() -> IEnumerator[T]: # type: ignore
    return __emptyEnumerator # type: ignore

def GetEnumerator[T](enumerator: IEnumerator[T]|None) -> IEnumerator[T]:
    return GetEmptyEnumerator() if enumerator is None else enumerator
def GetIterator[T](iterator: SystemIterator[T]|None) -> SystemIterator[T]:
    return GetEmptyEnumerator().AsIterator() if iterator is None else iterator # type: ignore

class IEnumerable[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        pass
    @final
    def GetEnumerator(self) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetEnumerator())
    
    @abstractmethod
    def AsIterable(self) -> SystemIterable[T]:
        pass

class IEquatableEnumerable[T: IEquatableItem](IEnumerable[T], IEquatableItem):
    def __init__(self):
        super().__init__()

@final
class __NullEnumerable[T](IEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    def TryGetIterator(self) -> SystemIterator[T]|None:
        return None

__nullEnumerable = __NullEnumerable[None]()

def GetNullEnumerable[T]() -> IEnumerable[T]: # type: ignore
    return __nullEnumerable # type: ignore

class ICountableEnumerable[T](IEnumerable[T], ICountable):
    def __init__(self):
        super().__init__()

def TryGetEnumerator[T](enumerable: IEnumerable[T]|None) -> IEnumerator[T]|None:
    return None if enumerable is None else enumerable.TryGetEnumerator()

class Enumerable[T](SystemIterable[T], IEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    def AsIterable(self) -> SystemIterable[T]:
        return self
    
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return self.GetEnumerator().AsIterator()
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return GetIterator(self._TryGetIterator())

class EquatableEnumerable[T: IEquatableItem](Enumerable[T], IEquatableEnumerable[T]):
    def __init__(self):
        super().__init__()
class CountableEnumerable[T](Countable, Enumerable[T], ICountableEnumerable[T]):
    def __init__(self):
        super().__init__()

class EnumeratorBase[T](IteratorBase[T], IEnumerator[T]):
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
    
    @staticmethod
    def Create(iterator: SystemIterator[T]) -> IEnumerator[T]:
        return iterator if isinstance(iterator, IEnumerator) else Iterator(iterator)
    @staticmethod
    def TryCreate(iterator: SystemIterator[T]|None) -> IEnumerator[T]|None:
        return None if iterator is None else Iterator[T].Create(iterator)

def TryAsIterable[T](enumerable: IEnumerable[T]|None) -> SystemIterable[T]|None:
    return None if enumerable is None else enumerable.AsIterable()

def __AsEnumerator[T](iterator: SystemIterator[T]) -> IEnumerator[T]:
    return iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator)

def AsEnumerator[T](iterator: SystemIterator[T]) -> IEnumerator[T]:
    if iterator is None: # type: ignore
        raise ValueError()
    
    return __AsEnumerator(iterator)
def TryAsEnumerator[T](iterator: SystemIterator[T]|None) -> IEnumerator[T]|None:
    return None if iterator is None else __AsEnumerator(iterator)

def TryAsIterator[T](enumerator: IEnumerator[T]|None) -> SystemIterator[T]|None:
    return None if enumerator is None else enumerator.AsIterator()

class IterableBase[T](Enumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        pass
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(self._TryGetIterator())
class Iterable[T](IterableBase[T]):
    def __init__(self, iterable: SystemIterable[T]):
        super().__init__()

        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return iter(self._GetIterable())
    
    @staticmethod
    def Create(iterable: SystemIterable[T]) -> IEnumerable[T]:
        return iterable if isinstance(iterable, IEnumerable) else Iterable(iterable)
    @staticmethod
    def TryCreate(iterable: SystemIterable[T]|None) -> IEnumerable[T]|None:
        return None if iterable is None else Iterable[T].Create(iterable)

class IteratorProvider[T](Enumerable[T]):
    def __init__(self, iteratorProvider: Function[SystemIterator[T]]|None):
        super().__init__()
        
        self.__iteratorProvider: Function[SystemIterator[T]]|None = iteratorProvider
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return None if self.__iteratorProvider is None else GetIterator(self.__iteratorProvider())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(self._TryGetIterator())

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
    
    def _OnStopped(self) -> None:
        self.__enumerator.Stop()
    
    def _ResetOverride(self) -> bool:
        return self.__enumerator.TryReset() is True
class Selector[TIn, TOut](AbstractEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]):
        super().__init__(enumerator)
class AbstractEnumerator[T](Selector[T, T]):
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
    
    def _MoveNextOverride(self) -> bool:
        return self._GetEnumerator().MoveNext()
    
    @abstractmethod
    def _ResetOverride(self) -> bool:
        pass
    
    @final
    def __MoveNext(self) -> bool:
        if self._OnStarting():
            def moveNext() -> bool:
                if self._MoveNextOverride():
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
    @abstractmethod
    def _OnStopped(self) -> None:
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

        if result is True and self._ResetOverride():
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
class AbstractionEnumerator[TIn, TOut](AbstractionEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
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
    
    def _MoveNextOverride(self) -> bool:
        if super()._MoveNextOverride():
            current: TIn|None = self._GetEnumerator().GetCurrent()

            if current is None:
                self.__current = None

                return False

            self.__current = self.__selector(current)

            return True
        
        return False
    
    def _OnEnded(self) -> None:
        self.__current = None
        
        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass

    def _ResetOverride(self) -> bool:
        return True
    
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
    def _MoveNextOverride(self) -> bool:
        return self._GetEnumerator().MoveNext()
    
    def _OnStopped(self) -> None:
        super()._OnStopped()
class Accessor[T](AccessorBase[T, T, IEnumerator[T]], IGenericConstraintImplementation[IEnumerator[T]]):
    def __init__(self, func: Function[IEnumerator[T]]):
        super().__init__(func)
    
    @final
    def GetCurrent(self) -> T|None:
        return self._GetEnumerator().GetCurrent()
    
    def _ResetOverride(self) -> bool:
        return True