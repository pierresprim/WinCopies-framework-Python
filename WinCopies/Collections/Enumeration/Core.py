
from abc import abstractmethod
from collections.abc import Iterable as SystemIterable, Iterator as SystemIterator, Sized
from typing import final, Any, Self

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstraction import CreateCountable
from WinCopies.Collections.Core import ICountable
from WinCopies.Collections.Enumeration import IterationState, EnumerationAbortReason, IIterationStatus, IterationStatus, GetIterationInactiveError, GetNoDataEnumerationStatus
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Generation.Registry import IInvalidationRegistrar, IManagedInvalidationRegistrar
from WinCopies.Collections.Generation.Registry.Invalidation import ManagedInvalidationRegistrar
from WinCopies.Delegates import NoAction, BoolFalse, Self as SameValue
from WinCopies.Enums import ErrorMessages
from WinCopies.Typing import INullable, GetNullable, GetNullValue, GetUnexpectedError
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, INotHashableValue, EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Action, Method, Function, Selector as SelectorDelegate, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable
from WinCopies.Typing.Monitoring import IMonitor, Monitor, DoWork, Process, ProcessData

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
    def TryMoveNext(self) -> bool:
        ...
    @final
    def MoveNext(self, raiseOnCompletion: bool = False) -> bool:
        if self.TryMoveNext(): return True

        self.GetStatus().ThrowIfErrored()

        if raiseOnCompletion: raise StopIteration()

        return False
    
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

    @final
    def __GetCurrent(self, succeeded: bool) -> INullable[T]:
        return GetNullable(self.GetCurrent()) if succeeded else GetNullValue()
    
    @abstractmethod
    def GetCurrent(self) -> T:
        ...
    @final
    def TryGetCurrent(self) -> INullable[T]:
        return self.__GetCurrent(self.IsStarted())

    @final
    def TryGetNext(self) -> INullable[T]:
        return self.__GetCurrent(self.TryMoveNext())
    @final
    def GetNext(self) -> T:
        self.MoveNext(True)
        
        return self.GetCurrent()

    @abstractmethod
    def AsIterator(self) -> SystemIterator[T]:
        ...
class IInvalidatableEnumerator[T](IEnumerator[T], IInvalidatableEnumeratorBase):
    def __init__(self) -> None: super().__init__()

class IteratorBase[T](SystemIterator[T], IEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __next__(self) -> T:
        return self.GetNext()
    
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
    def TryMoveNext(self) -> bool: return False
    def Stop(self) -> None: pass
    def TryReset(self) -> bool|None: return None
    def IsResetSupported(self) -> bool: return False
    
    def GetStatus(self) -> IIterationStatus: return GetNoDataEnumerationStatus()
@final
class _EmptyEnumerable[T](_SystemIterable[T]):
    def __init__(self) -> None: super().__init__()
    
    def TryGetEnumerator(self) -> None: return None
    
    def __iter__(self) -> SystemIterator[T]: return GetEmptyEnumerator().AsIterator() # pyright: ignore[reportUnknownVariableType]

@final
class _EnumeratorInvalidator(Abstract, IInvalidatable):
    def __init__(self, action: Action) -> None:
        super().__init__()

        self.__action: Action = action
        self.__processor: Action = NoAction

    def Initialize(self) -> None: self.__processor = self.__action

    def _Dispose(self, reason: DiscardReason) -> None:
        if reason == DiscardReason.Invalidated: self.__processor()

        self.__processor = NoAction

def _GetCurrent[T](*_: T) -> T:
    raise GetIterationInactiveError()
def _GetCurrentValue() -> Any:
    raise GetIterationInactiveError()

class EnumeratorBase[T](IteratorBase[T], IInvalidatableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__getCurrentFunc: Function[T] = _GetCurrentValue
        self.__getCurrent: SelectorDelegate[T] = SameValue

        self.__moveNextFunc: Function[bool] = self.__MoveFirst
        self.__moveNext: SelectorDelegate[bool] = SameValue

        self.__status: IterationStatus = IterationStatus()
        self.__monitor: IMonitor = Monitor()

        self.__invalidationRegistrar: IManagedInvalidationRegistrar = ManagedInvalidationRegistrar(_EnumeratorInvalidator(self.__Invalidate))
    
    @final
    def __Process[U](self, func: Function[U]) -> U:
        return Process(self.__monitor, func, ErrorMessages.ReentrancyNotAllowed)
    @final
    def __DoWork(self, action: Action) -> None:
        DoWork(self.__monitor, action, ErrorMessages.ReentrancyNotAllowed)

    @final
    def __TryAction(self, action: Action, notify: bool = True) -> None:
        try: action()

        except Exception:
            self.__status.Fault(notify)

            raise

    @final
    def __TryFunction[U](self, func: Function[U]) -> U:
        try: return func()

        except Exception:
            self.__status.Fault()

            raise
    
    @final
    def __SetCompletedMoveNext(self, completed: bool) -> None:
        def onCompleted() -> None:
            self._OnCompleted()
            self.__OnTerminated(completed)
        
        self.__SetMoveNext()

        if completed:
            try: self.__Clear(True)
            finally: self.__status.Complete()
        
        else: self.__status.Fail()

        self.__TryAction(onCompleted)

    @final
    def __UpdateMoveNext(self, func: Function[bool]) -> None:
        self.__getCurrent = _GetCurrent
        self.__getCurrentFunc = _GetCurrentValue

        self.__moveNextFunc = func
    
    @final
    def __SetMoveNext(self) -> None:
        self.__UpdateMoveNext(BoolFalse)
    @final
    def __ResetMoveNext(self) -> None:
        self.__UpdateMoveNext(self.__MoveFirst)

    @final
    def __GetCurrentValue(self, result: T) -> T: # Indirection needed to resolve calls in the right order.
        return self.__getCurrent(result)

    @final
    def __MoveNext(self, result: bool) -> bool: # Indirection needed to resolve calls in the right order.
        return self.__moveNext(result)
    @final
    def __MoveFirst(self) -> bool:
        def onCompleted(completed: bool) -> bool:
            self.__SetCompletedMoveNext(completed)

            return False

        def tryAction(func: Function[bool]) -> bool:
            try: return func()
            except StopIteration: return False

        def tryMove(func: Function[bool]) -> bool:
            try: return func()

            except Exception:
                self.__Terminate(EnumerationAbortReason.Errored)

                raise
        
        def setMoveNextFunc(func: Function[bool]) -> None:
            self.__moveNextFunc = lambda: tryMove(func)

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

        def moveFirst() -> bool:
            if tryAction(self._OnStarting):
                self.__status.Start()
                self.__invalidationRegistrar.Register()

                self.__getCurrentFunc = lambda: self.__TryFunction(self._GetCurrent)
                self.__getCurrent = SameValue
                
                return _moveFirst()

            return onCompleted(False)

        return tryMove(moveFirst)
    
    @final
    def __Terminate(self, reason: EnumerationAbortReason) -> None:
        def cancel() -> None:
            action: Action|None = delegates[1]

            if action is not None: action()

            self._OnAborted()
            self.__OnTerminated(False)

        if self.GetStatus().GetState() >= IterationState.Ended: return

        def getDelegates() -> tuple[Action, Action|None]:
            match reason:
                case EnumerationAbortReason.Stopped: return self.__status.Stop, self._OnStopped
                case EnumerationAbortReason.Invalidated: return self.__status.Invalidate, None
                case EnumerationAbortReason.Errored: return self.__status.Abort, self._OnErrored

                case _: raise GetUnexpectedError()

        delegates: tuple[Action, Action|None] = getDelegates()

        try: self.__Clear(self.IsStarted())
        finally:
            delegates[0]()

            self.__SetMoveNext()

        self.__TryAction(cancel)
    
    @final
    def __Stop(self) -> None:
        self.__Terminate(EnumerationAbortReason.Stopped)
    @final
    def __Invalidate(self) -> None:
        def invalidate(_: bool) -> bool:
            self.__moveNext = SameValue

            self.__Invalidate()

            return False

        if self.__monitor.IsBusy(): self.__moveNext = invalidate

        else: self.__DoWork(lambda: self.__Terminate(EnumerationAbortReason.Invalidated))
    
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
            
            self._Clear()

        if clear: self.__TryAction(_clear, False)

    def _OnStarting(self) -> bool:
        return True
    def _OnCompleted(self) -> None:
        pass
    def _OnAborted(self) -> None:
        pass
    def _OnErrored(self) -> None:
        pass
    def _OnStopped(self) -> None:
        pass
    def _OnTerminated(self, completed: bool) -> None:
        pass
    def _OnEnded(self) -> None:
        pass

    @final
    def AddRegistrar(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable: return ProcessData(invalidationRegistrar, self.__monitor, self.__invalidationRegistrar.Push, ErrorMessages.ReentrancyNotAllowed)
    
    @final
    def GetStatus(self) -> IIterationStatus: return self.__status.AsReadOnly()

    @final
    def GetCurrent(self) -> T:
        return self.__GetCurrentValue(self.__getCurrentFunc())

    @final
    def TryMoveNext(self) -> bool:
        def moveNext() -> bool:
            try: return self.__Process(self.__moveNextFunc)

            except Exception:
                self.__moveNext(False)

                raise
        
        return self.__MoveNext(moveNext())
    
    @final
    def Stop(self) -> None: self.__DoWork(self.__Stop)
    
    @final
    def TryReset(self) -> bool|None:
        def tryReset() -> bool|None:
            if self.IsResetSupported():
                if self.GetStatus().GetState() == IterationState.Idle: return True

                self.__Stop()
                
                if self.__TryFunction(self._ResetOverride):
                    self.__ResetMoveNext()

                    self.__status.Reset()
                    
                    return True
                
                return False
            
            self.__Stop()
            
            return None

        return self.__Process(tryReset)

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
    
    def _OnAborted(self) -> None: self.__Reset()
    
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