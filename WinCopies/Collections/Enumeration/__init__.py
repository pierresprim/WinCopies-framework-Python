# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable as SystemIterable, Iterator as SystemIterator, Sized
from typing import final, Any

from WinCopies import IInterface, Abstract
from WinCopies.Collections import ICountable, Countable as CountableBase
from WinCopies.Collections.Abstraction import Countable
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing import INullable, IDisposable, IEquatableValue, IEquatableItem, InvalidOperationError, GetNullable, GetNullValue, GetDisposedError
from WinCopies.Typing.Delegate import Converter, Method, Function, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class IEnumeratorBase(IInterface):
    def __init__(self) -> None:
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
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T:
        pass

    @abstractmethod
    def AsIterator(self) -> SystemIterator[T]:
        pass
class IDisposableEnumerator[T](IEnumerator[T], IDisposable):
    def __init__(self) -> None:
        super().__init__()

class IteratorBase[T](SystemIterator[T], IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __next__(self) -> T:
        if self.MoveNext():
            return self.GetCurrent()
        
        else:
            raise StopIteration
    
    @final
    def AsIterator(self) -> SystemIterator[T]:
        return self
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return self

class IEnumerableBase[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        pass
    @final
    def GetEnumerator(self) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetEnumerator())
class IEnumerable[T](IEnumerableBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsIterable(self) -> SystemIterable[T]:
        pass

class IEquatableEnumerable[T: IEquatableItem](IEnumerable[T], IEquatableValue):
    def __init__(self) -> None:
        super().__init__()
class IHashableEnumerable[T: IEquatableItem](IEnumerable[T], IEquatableItem):
    def __init__(self) -> None:
        super().__init__()

class ICountableEnumerable[T](IEnumerable[T], ICountable):
    def __init__(self) -> None:
        super().__init__()

class IReversableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IEnumerable[T]:
        pass
class IReversableCountableEnumerable[T](IReversableEnumerable[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()

def TryGetEnumerator[T](enumerable: IEnumerable[T]|None) -> IEnumerator[T]|None:
    return None if enumerable is None else enumerable.TryGetEnumerator()

class _SystemIterable[T](SystemIterable[T], IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def AsIterable(self) -> SystemIterable[T]:
        return self

class Enumerable[T](_SystemIterable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return self.GetEnumerator().AsIterator()
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return GetIterator(self._TryGetIterator())

class EquatableEnumerable[T: IEquatableItem](Enumerable[T], IEquatableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()

@final
class _CountableEnumerableUpdater[T](ValueFunctionUpdater[CountableBase]):
    def __init__(self, items: ICountableEnumerable[T], updater: Method[IFunction[CountableBase]]) -> None:
        super().__init__(updater)

        self.__items: ICountableEnumerable[T] = items
    
    def _GetValue(self) -> CountableBase:
        return Countable.Create(self.__items)

class CountableEnumerable[T](Enumerable[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        def update(func: IFunction[CountableBase]) -> None:
            self.__countable = func
        
        super().__init__()
        
        self.__countable: IFunction[CountableBase] = _CountableEnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsSized(self) -> Sized:
        return self.__countable.GetValue()

@final
class _EmptyEnumerator[T](IteratorBase[T], IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def IsStarted(self) -> bool:
        return False
    def GetCurrent(self) -> T:
        raise InvalidOperationError()
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
@final
class _EmptyEnumerable[T](_SystemIterable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return None
    
    @final
    def __iter__(self) -> SystemIterator[T]:
        return GetEmptyEnumerator().AsIterator() # pyright: ignore[reportUnknownVariableType]

__emptyEnumerator = _EmptyEnumerator[None]()
__emptyEnumerable = _EmptyEnumerable[None]()

def GetEmptyEnumerator[T]() -> IEnumerator[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerator # type: ignore
def GetEmptyEnumerable[T]() -> IEnumerable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerable # type: ignore
def GetEmptyIterable[T]() -> SystemIterable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return GetEmptyEnumerable().AsIterable() # pyright: ignore[reportUnknownVariableType]

def GetEnumerator[T](enumerator: IEnumerator[T]|None) -> IEnumerator[T]:
    return GetEmptyEnumerator() if enumerator is None else enumerator
def GetIterator[T](iterator: SystemIterator[T]|None) -> SystemIterator[T]:
    return GetEmptyEnumerator().AsIterator() if iterator is None else iterator # pyright: ignore[reportUnknownVariableType]

def GetEnumerable[T](enumerable: IEnumerable[T]|None) -> IEnumerable[T]:
    return GetEmptyEnumerable() if enumerable is None else enumerable
def GetIterable[T](iterable: SystemIterable[T]|None) -> SystemIterable[T]:
    return GetEmptyEnumerable().AsIterable() if iterable is None else iterable # pyright: ignore[reportUnknownVariableType]

class EnumeratorBase[T](IteratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveNext
        self.__isStarted: bool = False
        self.__hasProcessedItems: bool = False
    
    @final
    def __MoveNext(self) -> bool:
        def setCompletedMoveNext() -> None:
            self.__moveNextFunc = BoolFalse
            
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
    
    @abstractmethod
    def _GetCurrent(self) -> T:
        pass
    
    @final
    def IsStarted(self) -> bool:
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
    def GetCurrent(self) -> T:
        if self.IsStarted():
            return self._GetCurrent()
        
        raise InvalidOperationError()

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
            self.__moveNextFunc = BoolFalse
        
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
    def __init__(self) -> None:
        super().__init__()

        self.__current: INullable[T] = GetNullValue()
    
    def _OnEnded(self) -> None:
        self._UnsetCurrent()

        super()._OnEnded()
    
    @final
    def _GetCurrent(self) -> T:
        return self.__current.GetValue()
    
    @final
    def _SetCurrent(self, current: T) -> None:
        self.__current = GetNullable(current)
    @final
    def _UnsetCurrent(self) -> None:
        self.__current = GetNullValue()

class Iterator[T](Enumerator[T]):
    def __init__(self, iterator: SystemIterator[T]) -> None:
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
            self._UnsetCurrent()

            return False
    
    def _OnStopped(self) -> None:
        pass

    def _ResetOverride(self) -> bool:
        return False

def TryAsIterable[T](enumerable: IEnumerable[T]|None) -> SystemIterable[T]|None:
    return None if enumerable is None else enumerable.AsIterable()

def AsEnumerator[T](iterator: SystemIterator[T]) -> IEnumerator[T]:
    return iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator)
def TryAsEnumerator[T](iterator: SystemIterator[T]|None) -> IEnumerator[T]|None:
    return None if iterator is None else AsEnumerator(iterator)

def TryAsIterator[T](enumerator: IEnumerator[T]|None) -> SystemIterator[T]|None:
    return None if enumerator is None else enumerator.AsIterator()

class IterableBase[T](Enumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        pass
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(self._TryGetIterator())
class Iterable[T](IterableBase[T]):
    def __init__(self, iterable: SystemIterable[T]) -> None:
        super().__init__()

        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return iter(self._GetIterable())

class IteratorProvider[T](Enumerable[T]):
    def __init__(self, iteratorProvider: Function[SystemIterator[T]|None]) -> None:
        super().__init__()
        
        self.__iteratorProvider: Function[SystemIterator[T]|None] = iteratorProvider
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return GetIterator(self.__iteratorProvider())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(self._TryGetIterator())
class EnumeratorProvider[T](Enumerable[T]):
    def __init__(self, enumeratorProvider: Function[IEnumerator[T]|None]|None) -> None:
        super().__init__()
        
        self.__enumeratorProvider: Function[IEnumerator[T]|None]|None = enumeratorProvider
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return super()._TryGetIterator()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return None if self.__enumeratorProvider is None else self.__enumeratorProvider()

def CreateIterable[T](iterable: SystemIterable[T]) -> IEnumerable[T]:
    return iterable if isinstance(iterable, IEnumerable) else Iterable(iterable)
def TryCreateIterable[T](iterable: SystemIterable[T]|None) -> IEnumerable[T]|None:
    return None if iterable is None else CreateIterable(iterable)

def CreateIteratorProvider[T](iteratorProvider: Function[SystemIterator[T]|None]) -> IteratorProvider[T]:
    return IteratorProvider[T](iteratorProvider)
def TryCreateIteratorProvider[T](iteratorProvider: Function[SystemIterator[T]|None]|None) -> IteratorProvider[T]|None:
    return None if iteratorProvider is None else CreateIteratorProvider(iteratorProvider)

def CreateEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None]) -> EnumeratorProvider[T]:
    return EnumeratorProvider[T](enumeratorProvider)
def TryCreateEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None]|None) -> EnumeratorProvider[T]|None:
    return None if enumeratorProvider is None else CreateEnumeratorProvider(enumeratorProvider)

class AbstractEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](EnumeratorBase[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__()
        
        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetContainer(self) -> TEnumerator:
        return self.__enumerator
    
    @final
    def IsResetSupported(self) -> bool:
        return self._GetContainer().IsResetSupported()
    
    def _MoveNextOverride(self) -> bool:
        return self._GetContainer().MoveNext()
    
    def _OnStopped(self) -> None:
        self._GetContainer().Stop()
    
    def _ResetOverride(self) -> bool:
        return self._GetContainer().TryReset() is True
class Selector[TIn, TOut](AbstractEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None:
        super().__init__(enumerator)
class AbstractEnumerator[T](Selector[T, T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None:
        super().__init__(enumerator)
    
    def _GetCurrent(self) -> T:
        return self._GetContainer().GetCurrent()

class _AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](IteratorBase[TOut], IEnumerator[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveNext
    
    @abstractmethod
    def _GetContainer(self) -> TEnumerator:
        pass
    
    def _MoveNextOverride(self) -> bool:
        return self._GetContainer().MoveNext()
    
    @abstractmethod
    def _ResetOverride(self) -> bool:
        pass
    
    @final
    def __MoveNext(self) -> bool:
        if self._OnStarting():
            def moveNext() -> bool:
                if self._MoveNextOverride():
                    return True
                
                self.__moveNextFunc = BoolFalse

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

    @abstractmethod
    def _GetCurrent(self) -> TOut:
        pass
    
    @final
    def IsStarted(self) -> bool:
        return self._GetContainer().IsStarted()
    @final
    def GetCurrent(self) -> TOut:
        if self.IsStarted():
            return self._GetCurrent()
        
        raise InvalidOperationError()
    @final
    def MoveNext(self) -> bool:
        return self.__moveNextFunc()
    @final
    def Stop(self) -> None:
        self._GetContainer().Stop()

        self.__OnTerminated(False)
    
    @final
    def TryReset(self) -> bool|None:
        if self.IsStarted():
            self.Stop()
        
        result: bool|None = self._GetContainer().TryReset()

        if result is True and self._ResetOverride():
            self.__moveNextFunc = self.__MoveNext

            return True
        
        self.__moveNextFunc = BoolFalse
        
        return result
    @final
    def IsResetSupported(self) -> bool:
        return self._GetContainer().IsResetSupported()
    @final
    def HasProcessedItems(self) -> bool:
        return self._GetContainer().HasProcessedItems()

class AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](_AbstractionEnumeratorBase[TIn, TOut, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__()

        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetContainer(self) -> TEnumerator:
        return self.__enumerator
class AbstractionEnumerator[TIn, TOut](AbstractionEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None:
        super().__init__(enumerator)

class DelegateEnumerator[T](EnumeratorBase[T]):
    def __init__(self) -> None:
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

class ConverterEnumeratorBase[TIn, TOut](AbstractionEnumerator[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None:
        super().__init__(enumerator)

        self.__current: INullable[TOut] = GetNullValue()
    
    @abstractmethod
    def _Convert(self, value: TIn) -> TOut:
        pass
    
    def _MoveNextOverride(self) -> bool:
        if super()._MoveNextOverride():
            current: TIn = self._GetContainer().GetCurrent()

            self.__current = GetNullable(self._Convert(current))

            return True
        
        return False
    
    def _OnEnded(self) -> None:
        self.__current = GetNullValue()
        
        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass

    def _ResetOverride(self) -> bool:
        return True
    
    @final
    def _GetCurrent(self) -> TOut:
        return self.__current.GetValue()
class ConverterEnumerator[TIn, TOut](ConverterEnumeratorBase[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn], selector: Converter[TIn, TOut]) -> None:
        super().__init__(enumerator)

        self.__selector: Converter[TIn, TOut] = selector
    
    @final
    def _Convert(self, value: TIn) -> TOut:
        return self.__selector(value)

class IncrementalEnumerator[T](EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__i: int = self.__GetResetIndex()
    
    @final
    def __GetResetIndex(self) -> int:
        return -1
    @final
    def __Reset(self) -> None:
        self.__i = self.__GetResetIndex()
    
    @final
    def _GetValue(self) -> int:
        return self.__i
    @abstractmethod
    def _GetMaxValue(self) -> int:
        pass
    
    def IsResetSupported(self) -> bool:
        return True
    
    def _MoveNextOverride(self) -> bool:
        i: int = self.__i

        i += 1

        if i < self._GetMaxValue():
            self.__i = i

            return True
        
        self.__Reset()

        return False
    
    def _OnStopped(self) -> None:
        self.__Reset()
    
    def _ResetOverride(self) -> bool:
        self.__Reset()

        return True

@final
class _DisposedEnumerator[T](Abstract, IDisposableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def IsStarted(self) -> bool:
        return False
    
    def IsResetSupported(self) -> bool:
        return False
    
    def GetCurrent(self) -> T:
        raise GetDisposedError()
    
    def HasProcessedItems(self) -> bool:
        raise GetDisposedError()
    
    def MoveNext(self) -> bool:
        raise GetDisposedError()
    
    def TryReset(self) -> None:
        return None
    
    def Stop(self) -> None:
        pass
    
    def Dispose(self) -> None:
        pass

    def AsIterator(self) -> SystemIterator[T]:
        raise GetDisposedError()

__disposedEnumerator: _DisposedEnumerator[Any] = _DisposedEnumerator[Any]()

def _GetDisposedEnumerator[T]() -> IDisposableEnumerator[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __disposedEnumerator

@final
class _DisposableEnumerator[T](Abstract, IDisposableEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__enumerator: IEnumerator[T] = enumerator
    
    def IsStarted(self) -> bool:
        return self.__enumerator.IsStarted()
    
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
    
    def HasProcessedItems(self) -> bool:
        return self.__enumerator.HasProcessedItems()
    
    def GetCurrent(self) -> T:
        return self.__enumerator.GetCurrent()
    
    def MoveNext(self) -> bool:
        return self.__enumerator.MoveNext()
    
    def Stop(self) -> None:
        return self.__enumerator.Stop()
    
    def TryReset(self) -> bool|None:
        return self.__enumerator.TryReset()
    
    def Dispose(self) -> None:
        self.__enumerator.Stop()

        self.__enumerator = _GetDisposedEnumerator()
    
    def AsIterator(self) -> SystemIterator[T]:
        return self.__enumerator.AsIterator()

def ToDisposableEnumerator[T](enumerator: IEnumerator[T]) -> IDisposableEnumerator[T]:
    return _DisposableEnumerator[T](enumerator)