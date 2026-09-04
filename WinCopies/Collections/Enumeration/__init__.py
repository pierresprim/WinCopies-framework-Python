# -*- coding: utf-8 -*-
"""
Created on Sun Feb 6 20:37:51 2022

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable as SystemIterable, Iterator as SystemIterator, Sized
from enum import Flag, auto
from typing import final, Any, Self

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstraction import CreateCountable
from WinCopies.Collections.Core import ICountable
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Generation.Registry import IInvalidationRegistrar, IManagedInvalidationRegistrar
from WinCopies.Collections.Generation.Registry.Invalidation import ManagedInvalidationRegistrar
from WinCopies.Collections.Util import _Outside # pyright: ignore[reportPrivateUsage]
from WinCopies.Delegates import NoAction, BoolTrue, BoolFalse, GetActionBoolFunc
from WinCopies.Enum import AddFlag, HasFlag
from WinCopies.Enums import ErrorMessages
from WinCopies.Typing import INullable, InvalidOperationError, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, INotHashableValue, EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Action, Method, Function, Converter, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import DiscardReason, Invalidatable
from WinCopies.Typing.Enum import IntEnum
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Monitoring import IMonitor, Monitor, DoWork, Process, ProcessData

def GetIterationInactiveError() -> InvalidOperationError:
    return InvalidOperationError("Iteration is not active.")

class IterationState(IntEnum):
    Idle = 0
    """Iteration has not yet started."""
    Started = 1
    """Iterator is in run state."""
    Ended = 2
    """Iteration has terminated."""
class IterationResult(IntEnum):
    Faulted = -5
    "Iteration terminated because an error occurred."
    Invalidated = -4
    """Iteration was invalidated because the source mutated."""
    Stopped = -3
    """Iteration was canceled."""
    Failed = -2
    """Iteration failed to start."""
    Idle = -1
    """Iteration has not yet started."""
    Running = 0
    """Iterator is in run state."""
    Completed = 1
    """Iteration was successfully completed, possibly without yielding any item. If the enumerator is empty by design, NoData should be reported."""
    NoData = 2
    """The enumerator is empty by design. An enumeration that completed without yielding any item should report Completed."""

    @final
    def HasCompleted(self) -> bool:
        return self > IterationResult.Running
    @final
    def HasTerminated(self) -> bool:
        return _Outside(IterationResult.Idle, self, IterationResult.Running, False, False)

class IterationData(Flag):
    Null = 0
    HasProcessedItems = auto()
    Faulted = auto()

class IIterationStatus(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetState(self) -> IterationState:
        ...
    @abstractmethod
    def GetResult(self) -> IterationResult:
        ...
    
    @abstractmethod
    def GetData(self) -> IterationData:
        ...
    @final
    def HasProcessedItems(self) -> bool:
        return HasFlag(self.GetData(), IterationData.HasProcessedItems)
    
    @final
    def IsStarted(self) -> bool:
        return self.GetState() == IterationState.Started

@final
class _ReadOnlyIterationStatus(Abstract, IIterationStatus):
    def __init__(self, iterationStatus: IterationStatus) -> None:
        super().__init__()

        self.__iterationStatus: IterationStatus = iterationStatus

    def GetState(self) -> IterationState: return self.__iterationStatus.GetState()
    def GetResult(self) -> IterationResult: return self.__iterationStatus.GetResult()

    def GetData(self) -> IterationData: return self.__iterationStatus.GetData()
class IterationStatus(Abstract):
    def __init__(self) -> None:
        super().__init__()

        self.__state: IterationState = IterationState.Idle
        self.__result: IterationResult = IterationResult.Idle

        self.__data: IterationData = IterationData.Null

        self.__readOnly: IIterationStatus = _ReadOnlyIterationStatus(self)

    @final
    def __AddFlag(self, value: IterationData) -> None:
        self.__data = AddFlag(self.__data, value)

    @final
    def GetState(self) -> IterationState: return self.__state
    @final
    def GetResult(self) -> IterationResult: return self.__result
    
    @final
    def GetData(self) -> IterationData: return self.__data

    @final
    def NotifyItemProcessed(self) -> None:
        self.__AddFlag(IterationData.HasProcessedItems)

    @final
    def Reset(self) -> None:
        self.__state = IterationState.Idle
        self.__result = IterationResult.Idle

        self.__data = IterationData.Null

    @final
    def Start(self) -> None:
        self.__state = IterationState.Started
        self.__result = IterationResult.Running

    @final
    def __Terminate(self, result: IterationResult) -> None:
        self.__state = IterationState.Ended
        self.__result = result

    @final
    def Complete(self) -> None:
        self.__Terminate(IterationResult.Completed)

    @final
    def Fail(self) -> None:
        self.__Terminate(IterationResult.Failed)
    
    @final
    def Stop(self) -> None:
        self.__Terminate(IterationResult.Stopped)
    @final
    def Invalidate(self) -> None:
        self.__Terminate(IterationResult.Invalidated)

    @final
    def Fault(self, running: bool) -> None:
        if running: self.__result = IterationResult.Faulted

        self.__AddFlag(IterationData.Faulted)
    @final
    def Unfault(self) -> None:
        self.__result = IterationResult.Running

    @final
    def AsReadOnly(self) -> IIterationStatus:
        return self.__readOnly

@final
class _NoData(Abstract, IIterationStatus):
    def __init__(self) -> None: super().__init__()

    def GetState(self) -> IterationState: return IterationState.Ended
    def GetResult(self) -> IterationResult: return IterationResult.NoData

    def GetData(self) -> IterationData: return IterationData.Null

__noData: IIterationStatus = _NoData()

def GetNoDataEnumerationStatus() -> IIterationStatus:
    return __noData

class IEnumeratorBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @final
    def IsStarted(self) -> bool:
        return self.GetStatus().IsStarted()
    @abstractmethod
    def IsResetSupported(self) -> bool:
        ...

    @abstractmethod
    def GetStatus(self) -> IIterationStatus:
        ...
    
    @abstractmethod
    def MoveNext(self) -> bool:
        ...
    @abstractmethod
    def Stop(self) -> None:
        ...
    @abstractmethod
    def TryReset(self) -> bool|None:
        ...
class IInvalidatableEnumeratorBase(IEnumeratorBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AddRegistrar(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable:
        ...
class IEnumerator[T](IEnumeratorBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T:
        ...

    @abstractmethod
    def AsIterator(self) -> SystemIterator[T]:
        ...
class IInvalidatableEnumerator[T](IEnumerator[T], IInvalidatableEnumeratorBase):
    def __init__(self) -> None: super().__init__()

class IteratorBase[T](SystemIterator[T], IEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __next__(self) -> T:
        if self.MoveNext(): return self.GetCurrent()
        
        raise StopIteration()
    
    @final
    def AsIterator(self) -> SystemIterator[T]: return self
    
    @final
    def __iter__(self) -> Self: return self

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
class _EmptyEnumerator[T](IteratorBase[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetCurrent(self) -> T: raise GetIterationInactiveError()
    def MoveNext(self) -> bool: return False
    def Stop(self) -> None: pass
    def TryReset(self) -> bool|None: return None
    def IsResetSupported(self) -> bool: return False
    
    def GetStatus(self) -> IIterationStatus: return GetNoDataEnumerationStatus()
@final
class _EmptyEnumerable[T](_SystemIterable[T]):
    def __init__(self) -> None: super().__init__()
    
    def TryGetEnumerator(self) -> None: return None
    
    def __iter__(self) -> SystemIterator[T]: return GetEmptyEnumerator().AsIterator() # pyright: ignore[reportUnknownVariableType]

def _Process[T](monitor: IMonitor, func: Function[T]) -> T:
    return Process(monitor, func, ErrorMessages.ReentrancyNotAllowed)
def _DoWork(monitor: IMonitor, action: Action) -> None:
    DoWork(monitor, action, ErrorMessages.ReentrancyNotAllowed)

@final
class _EnumeratorInvalidator(Invalidatable):
    def __init__(self, action: Action) -> None:
        super().__init__()

        self.__action: Action = action

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        if reason == DiscardReason.Invalidated: self.__action()

        self.__action = NoAction

class EnumeratorBase[T](IteratorBase[T], IInvalidatableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNextFunc: Function[bool] = self.__MoveFirst

        self.__status: IterationStatus = IterationStatus()
        self.__monitor: IMonitor = Monitor()

        self.__invalidationRegistrar: IManagedInvalidationRegistrar = ManagedInvalidationRegistrar(_EnumeratorInvalidator(self.__Invalidate))
    
    @final
    def __Process[U](self, func: Function[U]) -> U:
        return _Process(self.__monitor, func)

    @final
    def __TryAction(self, action: Action) -> None:
        try: action()

        except Exception:
            self.__status.Fault(False)

            raise

    @final
    def __TryFunction[U](self, func: Function[U], onError: Function[bool]) -> U:
        try: return func()

        except Exception:
            self.__status.Fault(onError())

            raise
    
    @final
    def __SetCompletedMoveNext(self, completed: bool) -> None:
        def onCompleted() -> None:
            self._OnCompleted()
            self.__OnTerminated(completed)
        
        self.__moveNextFunc = BoolFalse

        if completed:
            try: self.__Clear(True)
            finally: self.__status.Complete()
        
        else: self.__status.Fail()

        self.__TryAction(onCompleted)
    
    @final
    def __MoveFirst(self) -> bool:
        def onCompleted(completed: bool) -> bool:
            self.__SetCompletedMoveNext(completed)

            return False

        def tryAction(func: Function[bool]) -> bool:
            try: return func()
            except StopIteration: return False

        def setMoveNextFunc(func: Function[bool]) -> None:
            self.__moveNextFunc = lambda: self.__TryFunction(GetActionBoolFunc(self.__status.Unfault, func), self.IsStarted)

        def _moveFirst() -> bool:
            def moveNext() -> bool:
                if tryAction(self._MoveNextOverride): return True
                
                self.__SetCompletedMoveNext(True)

                return False

            if tryAction(self._MoveNextOverride):
                setMoveNextFunc(moveNext)
                
                self.__status.NotifyItemProcessed()
                
                return True

            return onCompleted(True)

        def onError() -> bool:
            if self.IsStarted(): setMoveNextFunc(_moveFirst)

            return True

        def moveFirst() -> bool:
            if tryAction(self._OnStarting):
                self.__status.Start()
                self.__invalidationRegistrar.Register()
                
                return _moveFirst()

            return onCompleted(False)

        return self.__TryFunction(moveFirst, onError)
    
    @final
    def __Terminate(self, action: Action) -> None:
        def cancel() -> None:
            self._OnStopped()
            self.__OnTerminated(False)

        if self.GetStatus().GetState() >= IterationState.Ended: return

        try: self.__Clear(self.IsStarted())
        finally:
            action()

            self.__moveNextFunc = BoolFalse

        self.__TryAction(cancel)
    
    @final
    def __Stop(self) -> None:
        self.__Terminate(self.__status.Stop)
    @final
    def __Invalidate(self) -> None:
        self.__Terminate(self.__status.Invalidate)
    
    @final
    def __OnTerminated(self, completed: bool) -> None:
        self._OnTerminated(completed)
        self._OnEnded()

    @abstractmethod
    def _GetCurrent(self) -> T:
        ...
    
    @abstractmethod
    def _MoveNextOverride(self) -> bool:
        ...
    @abstractmethod
    def _ResetOverride(self) -> bool:
        ...

    def _Clear(self) -> None:
        pass
    @final
    def __Clear(self, clear: bool) -> None:
        def _clear() -> None:
            self.__invalidationRegistrar.Unregister()

            if clear: self._Clear()

        self.__TryAction(_clear)

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
    def AddRegistrar(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable: return ProcessData(invalidationRegistrar, self.__monitor, self.__invalidationRegistrar.Push, ErrorMessages.ReentrancyNotAllowed)

    @final
    def GetCurrent(self) -> T:
        if self.IsStarted(): return self.__TryFunction(self._GetCurrent, BoolTrue)
        
        raise GetIterationInactiveError()

    @final
    def MoveNext(self) -> bool: return self.__Process(self.__moveNextFunc)
    
    @final
    def Stop(self) -> None: _DoWork(self.__monitor, self.__Stop)
    
    @final
    def TryReset(self) -> bool|None:
        def tryReset() -> bool|None:
            if self.IsResetSupported():
                if self.GetStatus().GetState() == IterationState.Idle: return True

                self.__Stop()
                
                if self.__TryFunction(self._ResetOverride, BoolFalse):
                    self.__moveNextFunc = self.__MoveFirst

                    self.__status.Reset()
                    
                    return True
                
                return False
            
            self.__Stop()
            
            return None

        return self.__Process(tryReset)
    
    @final
    def GetStatus(self) -> IIterationStatus: return self.__status.AsReadOnly()

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
        if not self.IsStarted(): raise GetIterationInactiveError()
        
        self._SetCurrentOverride(current)
    @final
    def _UnsetCurrent(self) -> None:
        if self.IsStarted(): self._UnsetCurrentOverride()

    def _Clear(self) -> None:
        self._UnsetCurrent()

        super()._Clear()

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
        
        except StopIteration: return False
    
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

class AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](AbstractEnumeratorBase[TIn, TOut, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None: super().__init__(enumerator)
    
    def _OnCompleting(self, enumerator: TEnumerator) -> None:
        pass
    
    def _OnStopping(self, enumerator: TEnumerator) -> None:
        pass
    @abstractmethod
    def _OnStoppedOverride(self) -> None:
        ...

    def _OnTerminating(self, enumerator: TEnumerator, completed: bool) -> None:
        pass
    def _OnEnding(self, enumerator: TEnumerator) -> None:
        pass

    @final
    def __OnTerminating(self, enumerator: TEnumerator, completed: bool) -> None:
        self._OnTerminating(enumerator, completed)
        self._OnEnding(enumerator)
    
    @final
    def _OnStopped(self) -> None:
        enumerator: TEnumerator = self._GetContainer()

        self._OnStopping(enumerator)
        self.__OnTerminating(enumerator, False)

        super()._OnStopped()

        self._OnStoppedOverride()
class AbstractionEnumerator[TIn, TOut](AbstractionEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None: super().__init__(enumerator)

class DelegateEnumerator[T](EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNext: Function[bool]|None = None
    
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
        self.__moveNext = None

        super()._OnEnded()

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
    
    def _OnStoppedOverride(self) -> None:
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

__emptyEnumerator = _EmptyEnumerator[Any]()
__emptyEnumerable = _EmptyEnumerable[Any]()

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

def AsEnumerable[T](iterable: SystemIterable[T]) -> IEnumerable[T]:
    return iterable if isinstance(iterable, IEnumerable) else Iterable[T](iterable)
def TryAsEnumerable[T](iterable: SystemIterable[T]|None) -> IEnumerable[T]|None:
    return None if iterable is None else AsEnumerable(iterable)

def CreateIteratorProvider[T](iteratorProvider: Function[SystemIterator[T]|None]) -> Enumerable[T]:
    return IteratorProvider[T](iteratorProvider)
def TryCreateIteratorProvider[T](iteratorProvider: Function[SystemIterator[T]|None]|None) -> Enumerable[T]|None:
    return None if iteratorProvider is None else CreateIteratorProvider(iteratorProvider)

def CreateEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None]) -> Enumerable[T]:
    return EnumeratorProvider[T](enumeratorProvider)
def TryCreateEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None]|None) -> Enumerable[T]|None:
    return None if enumeratorProvider is None else CreateEnumeratorProvider(enumeratorProvider)