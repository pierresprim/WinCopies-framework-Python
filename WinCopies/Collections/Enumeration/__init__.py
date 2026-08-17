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
from WinCopies.Collections.Abstraction import CreateCountable
from WinCopies.Collections.Core import ICountable
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing import INullable, InvalidOperationError, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, INotHashableValue, EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Converter, Method, Function, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable, GetDiscardedError
from WinCopies.Typing.Enum import IntEnum
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

def GetEnumeratorInactiveError() -> InvalidOperationError:
    return InvalidOperationError("The enumeration has not started or has been terminated.")

class EnumerationState(IntEnum):
    Idle = 0
    Started = 1
    Ended = 2
class EnumerationResult(IntEnum):
    Stopped = -2
    NoData = -1
    Running = 0
    Completed = 1

class IEnumeratorBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def MoveNext(self) -> bool:
        ...
    @abstractmethod
    def Stop(self) -> None:
        ...
    @abstractmethod
    def TryReset(self) -> bool|None:
        ...
    @abstractmethod
    def IsResetSupported(self) -> bool:
        ...

    @abstractmethod
    def GetState(self) -> EnumerationState:
        ...
    @abstractmethod
    def GetResult(self) -> EnumerationResult:
        ...
    
    @final
    def IsStarted(self) -> bool:
        return self.GetState() == EnumerationState.Started
    @abstractmethod
    def HasProcessedItems(self) -> bool:
        ...

    @abstractmethod
    def ToInvalidatable(self) -> IInvalidatableEnumeratorBase:
        ...
class IEnumerator[T](IEnumeratorBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T:
        ...

    @abstractmethod
    def AsIterator(self) -> SystemIterator[T]:
        ...

    def ToInvalidatable(self) -> IInvalidatableEnumerator[T]: return _InvalidatableEnumerator[T](self)

class IInvalidatableEnumeratorBase(IEnumeratorBase, IInvalidatable):
    def __init__(self) -> None: super().__init__()
class IInvalidatableEnumerator[T](IEnumerator[T], IInvalidatableEnumeratorBase):
    def __init__(self) -> None: super().__init__()

    def ToInvalidatable(self) -> IInvalidatableEnumerator[T]: return self

class IteratorBase[T](SystemIterator[T], IEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __next__(self) -> T:
        if self.MoveNext(): return self.GetCurrent()
        
        raise StopIteration
    
    @final
    def AsIterator(self) -> SystemIterator[T]: return self
    
    @final
    def __iter__(self) -> SystemIterator[T]: return self

class IEnumerableBase[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        ...
    @final
    def GetEnumerator(self) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetEnumerator())
class IEnumerable[T](IEnumerableBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsIterable(self) -> SystemIterable[T]:
        ...

class IEquatableEnumerable[T: EquatableProtocol](IEnumerable[T], IEquatableValue):
    def __init__(self) -> None: super().__init__()
class IHashableEnumerable[T: HashableProtocol](IEquatableEnumerable[T], IHashableValue):
    def __init__(self) -> None: super().__init__()

class ICountableEnumerable[T](IEnumerable[T], ICountable):
    def __init__(self) -> None: super().__init__()

class IReversableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IEnumerable[T]:
        ...
class IReversableCountableEnumerable[T](IReversableEnumerable[T], ICountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

class _SystemIterable[T](SystemIterable[T], IEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def AsIterable(self) -> SystemIterable[T]: return self

class Enumerable[T](_SystemIterable[T]):
    def __init__(self) -> None: super().__init__()
    
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        return self.GetEnumerator().AsIterator()
    
    @final
    def __iter__(self) -> SystemIterator[T]: return GetIterator(self._TryGetIterator())

class EquatableEnumerable[T: EquatableProtocol](Enumerable[T], IEquatableEnumerable[T], INotHashableValue):
    def __init__(self) -> None: super().__init__()
class HashableEnumerable[T: HashableProtocol](Enumerable[T], IHashableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

@final
class _CountableEnumerableUpdater[T](ValueFunctionUpdater[ICountable]):
    def __init__(self, items: ICountableEnumerable[T], updater: Method[IFunction[ICountable]]) -> None:
        super().__init__(updater)

        self.__items: ICountableEnumerable[T] = items
    
    def _GetValue(self) -> ICountable: return CreateCountable(self.__items)

class CountableEnumerable[T](Enumerable[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        def update(func: IFunction[ICountable]) -> None: self.__countable = func
        
        super().__init__()
        
        self.__countable: IFunction[ICountable] = _CountableEnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsSized(self) -> Sized: return self.__countable.GetValue().AsSized()

@final
class _EmptyEnumerator[T](IteratorBase[T], IEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetCurrent(self) -> T: raise GetEnumeratorInactiveError()
    def MoveNext(self) -> bool: return False
    def Stop(self) -> None: pass
    def TryReset(self) -> bool|None: return None
    def IsResetSupported(self) -> bool: return False
    
    def GetState(self) -> EnumerationState: return EnumerationState.Ended
    def GetResult(self) -> EnumerationResult: return EnumerationResult.NoData
    
    def HasProcessedItems(self) -> bool: return False
@final
class _EmptyEnumerable[T](_SystemIterable[T]):
    def __init__(self) -> None: super().__init__()
    
    def TryGetEnumerator(self) -> None: return None
    
    def __iter__(self) -> SystemIterator[T]: return GetEmptyEnumerator().AsIterator() # pyright: ignore[reportUnknownVariableType]

class EnumeratorBase[T](IteratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveFirst
        self.__status: EnumerationState = EnumerationState.Idle
        self.__result: EnumerationResult = EnumerationResult.NoData
    
    def __SetCompletedMoveNext(self) -> None:
        self.__moveNextFunc = BoolFalse
        
        self.__OnCompleted()
    
    @final
    def __MoveNext(self) -> bool:
        if self._MoveNextOverride(): return True

        self.__SetCompletedMoveNext()

        return False
    @final
    def __MoveFirst(self) -> bool:
        if self._OnStarting():
            self.__status = EnumerationState.Started
            
            if self._MoveNextOverride():
                self.__moveNextFunc = self.__MoveNext
                self.__result = EnumerationResult.Completed
                
                return True
        
        self.__SetCompletedMoveNext()

        return False
    
    @final
    def __OnTerminated(self, completed: bool) -> None:
        self.__status = EnumerationState.Ended

        self._OnTerminated(completed)
        self._OnEnded()
    
    @final
    def __OnCompleted(self) -> None:
        self.__OnTerminated(True)
        self._OnCompleted()

    @final
    def __OnStopped(self) -> None:
        pass
    
    @abstractmethod
    def _GetCurrent(self) -> T:
        ...
    
    @abstractmethod
    def _MoveNextOverride(self) -> bool:
        ...
    @abstractmethod
    def _ResetOverride(self) -> bool:
        ...
    def _OnStarting(self) -> bool:
        return True
    def _OnCompleted(self) -> None:
        pass
    @abstractmethod
    def _OnStopped(self) -> None:
        ...
    def _OnTerminated(self, completed: bool) -> None:
        pass
    def _OnEnded(self) -> None:
        pass

    @final
    def GetCurrent(self) -> T:
        if self.IsStarted(): return self._GetCurrent()
        
        raise GetEnumeratorInactiveError()

    @final
    def MoveNext(self) -> bool: return self.__moveNextFunc()
    
    @final
    def Stop(self) -> None:
        self.__moveNextFunc = BoolFalse
        self.__result = EnumerationResult.Stopped

        self.__OnTerminated(False)
        self._OnStopped()
    
    @final
    def TryReset(self) -> bool|None:
        if self.IsResetSupported():
            if self.IsStarted(): self.Stop()
            
            if self._ResetOverride():
                self.__moveNextFunc = self.__MoveFirst
                self.__status = EnumerationState.Idle
                self.__result = EnumerationResult.NoData
                
                return True
            
            return False
        
        self.__moveNextFunc = BoolFalse
        
        return None
    
    @final
    def GetState(self) -> EnumerationState: return self.__status
    @final
    def GetResult(self) -> EnumerationResult: return EnumerationResult.Running if self.GetState().value < EnumerationState.Ended.value else self.__result
    
    @final
    def HasProcessedItems(self) -> bool:
        result: EnumerationResult = self.GetResult()

        return self.__moveNextFunc == self.__MoveNext if result == EnumerationResult.Running else result != EnumerationResult.NoData

class _EnumeratorBase[T](EnumeratorBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _SetCurrentOverride(self, current: T) -> None:
        ...
    @abstractmethod
    def _UnsetCurrentOverride(self) -> None:
        ...

    @final
    def _SetCurrent(self, current: T) -> None:
        if not self.IsStarted(): raise GetEnumeratorInactiveError()
        
        self._SetCurrentOverride(current)
    @final
    def _UnsetCurrent(self) -> None:
        if self.IsStarted(): self._UnsetCurrentOverride()
    
    def _OnEnded(self) -> None:
        self._UnsetCurrent()

        super()._OnEnded()

class Enumerator[T](_EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__current: INullable[T] = GetNullValue()
    
    def _OnCurrentUpdating(self, old: INullable[T], new: T) -> None:
        ...
    def _OnCurrentReset(self, old: T) -> None:
        ...
    
    def _OnCurrentInvalidated(self, old: T) -> None:
        ...
    
    @final
    def _TryGetCurrent(self) -> INullable[T]: return self.__current
    @final
    def _GetCurrent(self) -> T: return self._TryGetCurrent().GetValue()
    
    @final
    def _SetCurrentOverride(self, current: T) -> None:
        old: INullable[T] = self._TryGetCurrent()

        self._OnCurrentUpdating(old, current)

        if old.HasValue(): self._OnCurrentInvalidated(old.GetValue())
        
        self.__current = GetNullable(current)
    @final
    def _UnsetCurrentOverride(self) -> None:
        def onCurrentReset(old: T) -> None:
            self._OnCurrentReset(old)
            self._OnCurrentInvalidated(old)
        
        old: INullable[T] = self._TryGetCurrent()
        
        if old.HasValue():
            onCurrentReset(old.GetValue())

            self.__current = GetNullValue()
class NullableEnumerator[T](_EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__current: T|None = None
    
    def _OnCurrentUpdating(self, old: T|None, new: T) -> None:
        ...
    def _OnCurrentReset(self, old: T) -> None:
        ...
    
    def _OnCurrentInvalidated(self, old: T) -> None:
        ...
    
    @final
    def _TryGetCurrent(self) -> T|None: return self.__current
    @final
    def _GetCurrent(self) -> T:
        current: T|None = self.__current

        if current is None: raise ValueError()
        return current
    
    @final
    def _SetCurrentOverride(self, current: T) -> None:
        old: T|None = self._TryGetCurrent()

        self._OnCurrentUpdating(old, current)

        if old is not None: self._OnCurrentInvalidated(old)
        
        self.__current = current
    @final
    def _UnsetCurrentOverride(self) -> None:
        old: T|None = self._TryGetCurrent()

        if old is None: return

        self._OnCurrentReset(old)
        self._OnCurrentInvalidated(old)

        self.__current = None

class Iterator[T](Enumerator[T]):
    def __init__(self, iterator: SystemIterator[T]) -> None:
        super().__init__()

        self.__iterator: SystemIterator[T] = iterator
    
    @final
    def _GetIterator(self) -> SystemIterator[T]:
        return self.__iterator
    
    @final
    def IsResetSupported(self) -> bool: return False
    
    def _MoveNextOverride(self) -> bool:
        try:
            self._SetCurrent(self.__iterator.__next__())
            
            return True
        except StopIteration:
            self._UnsetCurrent()

            return False
    
    def _OnStopped(self) -> None: pass

    def _ResetOverride(self) -> bool: return False

class IterableBase[T](Enumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _TryGetIterator(self) -> SystemIterator[T]|None:
        ...
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryAsEnumerator(self._TryGetIterator())
class Iterable[T](IterableBase[T]):
    def __init__(self, iterable: SystemIterable[T]) -> None:
        super().__init__()

        self.__iterable: SystemIterable[T] = iterable
    
    @final
    def _GetIterable(self) -> SystemIterable[T]:
        return self.__iterable
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None: return iter(self._GetIterable())

class IteratorProvider[T](Enumerable[T]):
    def __init__(self, iteratorProvider: Function[SystemIterator[T]|None]) -> None:
        super().__init__()
        
        self.__iteratorProvider: Function[SystemIterator[T]|None] = iteratorProvider
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None: return GetIterator(self.__iteratorProvider())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryAsEnumerator(self._TryGetIterator())
class EnumeratorProvider[T](Enumerable[T]):
    def __init__(self, enumeratorProvider: Function[IEnumerator[T]|None]|None) -> None:
        super().__init__()
        
        self.__enumeratorProvider: Function[IEnumerator[T]|None]|None = enumeratorProvider
    
    @final
    def _TryGetIterator(self) -> SystemIterator[T]|None: return super()._TryGetIterator()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return None if self.__enumeratorProvider is None else self.__enumeratorProvider()

class AbstractEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](EnumeratorBase[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__()
        
        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetContainer(self) -> TEnumerator: return self.__enumerator
    
    @final
    def IsResetSupported(self) -> bool: return self._GetContainer().IsResetSupported()
    
    def _MoveNextOverride(self) -> bool: return self._GetContainer().MoveNext()
    
    def _OnStopped(self) -> None: self._GetContainer().Stop()
    
    def _ResetOverride(self) -> bool: return self._GetContainer().TryReset() is True
class Selector[TIn, TOut](AbstractEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None: super().__init__(enumerator)
class AbstractEnumerator[T](Selector[T, T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None: super().__init__(enumerator)
    
    def _GetCurrent(self) -> T: return self._GetContainer().GetCurrent()

class _AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](IteratorBase[TOut], IEnumerator[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveNext
    
    @abstractmethod
    def _GetContainer(self) -> TEnumerator:
        ...
    
    def _MoveNextOverride(self) -> bool: return self._GetContainer().MoveNext()
    
    @abstractmethod
    def _ResetOverride(self) -> bool:
        ...
    
    @final
    def __MoveNext(self) -> bool:
        if self._OnStarting():
            def moveNext() -> bool:
                if self._MoveNextOverride(): return True
                
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
        ...

    @abstractmethod
    def _GetCurrent(self) -> TOut:
        ...
    
    @final
    def GetCurrent(self) -> TOut:
        if self.IsStarted(): return self._GetCurrent()
        
        raise GetEnumeratorInactiveError()
    @final
    def MoveNext(self) -> bool: return self.__moveNextFunc()
    @final
    def Stop(self) -> None:
        self._GetContainer().Stop()

        self.__OnTerminated(False)
    
    @final
    def TryReset(self) -> bool|None:
        if self.IsStarted(): self.Stop()
        
        result: bool|None = self._GetContainer().TryReset()

        if result is True and self._ResetOverride():
            self.__moveNextFunc = self.__MoveNext

            return True
        
        self.__moveNextFunc = BoolFalse
        
        return result
    @final
    def IsResetSupported(self) -> bool: return self._GetContainer().IsResetSupported()
    
    @final
    def GetState(self) -> EnumerationState: return self._GetContainer().GetState()
    @final
    def GetResult(self) -> EnumerationResult: return self._GetContainer().GetResult()
    
    @final
    def HasProcessedItems(self) -> bool: return self._GetContainer().HasProcessedItems()

class AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](_AbstractionEnumeratorBase[TIn, TOut, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__()

        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetContainer(self) -> TEnumerator: return self.__enumerator
class AbstractionEnumerator[TIn, TOut](AbstractionEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None: super().__init__(enumerator)

class DelegateEnumerator[T](EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNext: Function[bool]|None
    
    @abstractmethod
    def _OnMoveNext(self) -> Function[bool]|None:
        ...
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            func: Function[bool]|None = self._OnMoveNext()

            if func is None: return False
            
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
        ...
    
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

    def _ResetOverride(self) -> bool: return True
    
    @final
    def _GetCurrent(self) -> TOut: return self.__current.GetValue()
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
    @final
    def _SetValue(self, value: int) -> None:
        self.__i = value
    
    @abstractmethod
    def _GetMaxValue(self) -> int:
        ...
    
    def IsResetSupported(self) -> bool: return True
    
    def _MoveNextOverride(self) -> bool:
        i: int = self.__i

        i += 1

        if i < self._GetMaxValue():
            self._SetValue(i)

            return True
        
        self.__Reset()

        return False
    
    def _OnStopped(self) -> None: self.__Reset()
    
    def _ResetOverride(self) -> bool:
        self.__Reset()

        return True

@final
class _DisposedEnumerator[T](Abstract, IInvalidatableEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    def IsResetSupported(self) -> bool: return False
    
    def HasProcessedItems(self) -> bool: raise GetDiscardedError()
    
    def GetCurrent(self) -> T: raise GetDiscardedError()
    
    def GetState(self) -> EnumerationState: raise GetDiscardedError()
    def GetResult(self) -> EnumerationResult: raise GetDiscardedError()
    
    def MoveNext(self) -> bool: raise GetDiscardedError()
    
    def TryReset(self) -> None: return None
    
    def Stop(self) -> None: pass
    
    def _Dispose(self, reason: DiscardReason) -> None: pass

    def AsIterator(self) -> SystemIterator[T]: raise GetDiscardedError()

class InvalidatableEnumeratorAbstract[T](IteratorBase[T], IInvalidatableEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    @staticmethod
    def _GetDefaultDisposedEnumerator() -> IEnumerator[T]:
        return _GetDisposedEnumerator()
class InvalidatableEnumeratorBase[TItem, TEnumerator: IEnumeratorBase](InvalidatableEnumeratorAbstract[TItem], GenericConstraint[TEnumerator, IEnumerator[TItem]]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__()

        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetContainer(self) -> TEnumerator: return self.__enumerator
    
    @abstractmethod
    def _GetDisposedEnumerator(self) -> TEnumerator:
        ...
    
    @final
    def IsResetSupported(self) -> bool: return self._GetInnerContainer().IsResetSupported()
    
    @final
    def HasProcessedItems(self) -> bool: return self._GetInnerContainer().HasProcessedItems()
    
    @final
    def GetState(self) -> EnumerationState: return self._GetInnerContainer().GetState()
    @final
    def GetResult(self) -> EnumerationResult: return self._GetInnerContainer().GetResult()
    
    @final
    def GetCurrent(self) -> TItem: return self._GetInnerContainer().GetCurrent()
    
    @final
    def MoveNext(self) -> bool: return self._GetInnerContainer().MoveNext()
    
    @final
    def Stop(self) -> None: return self._GetInnerContainer().Stop()
    
    @final
    def TryReset(self) -> bool|None: return self._GetInnerContainer().TryReset()
    
    def _Dispose(self, reason: DiscardReason) -> None:
        self._GetInnerContainer().Stop()

        self.__enumerator = self._GetDisposedEnumerator()
@final
class _InvalidatableEnumerator[T](InvalidatableEnumeratorBase[T, IEnumerator[T]], IGenericConstraintImplementation[IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]) -> None: super().__init__(enumerator)
    
    def _GetDisposedEnumerator(self) -> IEnumerator[T]:
        return InvalidatableEnumeratorAbstract[T]._GetDefaultDisposedEnumerator()

__emptyEnumerator = _EmptyEnumerator[Any]()
__emptyEnumerable = _EmptyEnumerable[Any]()

__disposedEnumerator: _DisposedEnumerator[Any] = _DisposedEnumerator[Any]()

def _GetDisposedEnumerator[T]() -> IInvalidatableEnumerator[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __disposedEnumerator

def TryGetEnumerator[T](enumerable: IEnumerable[T]|None) -> IEnumerator[T]|None:
    return None if enumerable is None else enumerable.TryGetEnumerator()

def GetEmptyEnumerator[T]() -> IEnumerator[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerator
def GetEmptyEnumerable[T]() -> IEnumerable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerable
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

def TryAsIterable[T](enumerable: IEnumerable[T]|None) -> SystemIterable[T]|None:
    return None if enumerable is None else enumerable.AsIterable()

def AsEnumerator[T](iterator: SystemIterator[T]) -> IEnumerator[T]:
    return iterator if isinstance(iterator, IEnumerator) else Iterator[T](iterator)
def TryAsEnumerator[T](iterator: SystemIterator[T]|None) -> IEnumerator[T]|None:
    return None if iterator is None else AsEnumerator(iterator)

def TryAsIterator[T](enumerator: IEnumerator[T]|None) -> SystemIterator[T]|None:
    return None if enumerator is None else enumerator.AsIterator()

def CreateIterable[T](iterable: SystemIterable[T]) -> IEnumerable[T]:
    return iterable if isinstance(iterable, IEnumerable) else Iterable(iterable)
def TryCreateIterable[T](iterable: SystemIterable[T]|None) -> IEnumerable[T]|None:
    return None if iterable is None else CreateIterable(iterable)

def CreateIteratorProvider[T](iteratorProvider: Function[SystemIterator[T]|None]) -> Enumerable[T]:
    return IteratorProvider[T](iteratorProvider)
def TryCreateIteratorProvider[T](iteratorProvider: Function[SystemIterator[T]|None]|None) -> Enumerable[T]|None:
    return None if iteratorProvider is None else CreateIteratorProvider(iteratorProvider)

def CreateEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None]) -> Enumerable[T]:
    return EnumeratorProvider[T](enumeratorProvider)
def TryCreateEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None]|None) -> Enumerable[T]|None:
    return None if enumeratorProvider is None else CreateEnumeratorProvider(enumeratorProvider)