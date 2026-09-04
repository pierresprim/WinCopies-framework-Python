from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Any

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Core import IReadOnlyCollection
from WinCopies.Collections.Enumeration import IIterationStatus, IEnumerable, ICountableEnumerable, IEnumeratorBase, IInvalidatableEnumeratorBase, IEnumerator, IInvalidatableEnumerator, Enumerable, CountableEnumerable, IteratorBase, EnumeratorBase, EnumeratorProvider, AbstractEnumeratorBase, GetEmptyEnumerable, GetEmptyEnumerator, GetIterationInactiveError
from WinCopies.Collections.Generation import IResumable, IRemovable, INode
from WinCopies.Collections.Generation.Registry import IObjectRegistry
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable, InvalidatableObjectProviderBase
from WinCopies.Typing.Generic import IGenericConstraintImplementation

class ICookie[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SetCursor(self, value: T) -> None:
        ...

class IResumableEnumerationCursor(IResumable, IInvalidatable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        ...

class IResumableEnumeratorBase(IEnumeratorBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def SupportsMultipleCursors(self) -> bool:
        ...
    
    @abstractmethod
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        ...
    @abstractmethod
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        ...

    @abstractmethod
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        ...

    @abstractmethod
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        ...
class IResumableEnumerator[T](IEnumerator[T], IResumableEnumeratorBase):
    def __init__(self) -> None: super().__init__()

class IInvalidatableResumableEnumeratorBase(IResumableEnumeratorBase, IInvalidatableEnumeratorBase):
    def __init__(self) -> None: super().__init__()
class IInvalidatableResumableEnumerator[T](IResumableEnumerator[T], IInvalidatableEnumerator[T], IInvalidatableResumableEnumeratorBase):
    def __init__(self) -> None: super().__init__()

class IDefaultResumableEnumerator[TItem, TCursorValue](IResumableEnumerator[TItem]):
    @final
    class _Cookie[_TItem, _TCursorValue](Abstract, ICookie[_TCursorValue]):
        def __init__(self, enumerator: IDefaultResumableEnumerator[_TItem, _TCursorValue]) -> None:
            super().__init__()

            self.__enumerator: IDefaultResumableEnumerator[_TItem, _TCursorValue] = enumerator
        
        def SetCursor(self, value: _TCursorValue) -> None:
            self.__enumerator._SetCursor(value)
    
    def __init__(self) -> None: super().__init__()
    
    @staticmethod
    def _GetException(msg: str) -> InvalidOperationError:
        return InvalidOperationError(f"Cannot {msg} before the enumeration has started.")
    @staticmethod
    def _GetCursorException(msg: str) -> InvalidOperationError:
        return IDefaultResumableEnumerator._GetException(f"{msg} a cursor")
    
    @abstractmethod
    def _GetFirstCursor(self) -> IResumableEnumerationCursor:
        ...

    @abstractmethod
    def _SetCursor(self, value: TCursorValue) -> None:
        ...

    @final
    def _CreateCursorCookie(self) -> ICookie[TCursorValue]:
        return IDefaultResumableEnumerator[TItem, TCursorValue]._Cookie(self)
    
    @abstractmethod
    def _PlaceCursor(self) -> IResumableEnumerationCursor:
        ...
    
    @final
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        if self.IsStarted(): return self._PlaceCursor()
        
        raise IDefaultResumableEnumerator._GetCursorException("place")
    @final
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        cursor: IResumableEnumerationCursor = self.PlaceCursor()

        cursor.MoveToTop()

        return cursor
    
    @final
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        if self.IsStarted(): cursor.MoveToTop()
        
        else: raise IDefaultResumableEnumerator._GetCursorException("move")
    
    @final
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        if self.IsStarted(): (self._GetFirstCursor() if cursor is None else cursor).Resume()
        
        else: raise IDefaultResumableEnumerator._GetException("resume")
class IDefaultInvalidatableResumableEnumerator[TItem, TCursorValue](IDefaultResumableEnumerator[TItem, TCursorValue], IInvalidatableResumableEnumerator[TItem]):
    def __init__(self) -> None: super().__init__()

class IResumableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None:
        ...
    @final
    def GetResumableEnumerator(self) -> IResumableEnumerator[T]:
        return GetResumableEnumerator(self.TryGetResumableEnumerator())
class ResumableEnumerable[T](Enumerable[T], IResumableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

class IResumableCountableEnumerable[T](IResumableEnumerable[T], ICountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()
class ResumableCountableEnumerable[T](CountableEnumerable[T], IResumableCountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

class ResumableEnumeratorBase[T](EnumeratorBase[T], IResumableEnumerator[T]):
    def __init__(self) -> None: super().__init__()
class ResumableEnumerator[T](ResumableEnumeratorBase[T]):
    def __init__(self) -> None: super().__init__()

class IResumableEnumerationCursorRegistry[T: IResumableEnumerationCursor](IObjectRegistry[T], IReadOnlyCollection):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetFirstCursor(self) -> IResumableEnumerationCursor:
        ...
class IDefaultResumableEnumerationCursorRegistry[T: IResumableEnumerationCursor](IResumableEnumerationCursorRegistry[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _InitializeCursor(self, cursor: T, node: INode) -> None:
        ...

class AbstractResumableEnumeratorAbstract[TIn, TOut, TEnumerator: IEnumeratorBase](AbstractEnumeratorBase[TIn, TOut, TEnumerator], IResumableEnumerator[TOut]):
    def __init__(self, enumerator: TEnumerator) -> None: super().__init__(enumerator)
class AbstractResumableEnumeratorBase[TItem, TEnumerator: IEnumeratorBase](AbstractResumableEnumeratorAbstract[TItem, TItem, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None: super().__init__(enumerator)
class AbstractResumableEnumerator[T](AbstractResumableEnumeratorBase[T, IResumableEnumerator[T]], IGenericConstraintImplementation[IResumableEnumerator[T]]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None: super().__init__(enumerator)

@final
class _EmptyEnumerator[T](IteratorBase[T], IResumableEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetStatus(self) -> IIterationStatus: return GetEmptyEnumerator().GetStatus()
    
    def GetCurrent(self) -> T: return GetEmptyEnumerator().GetCurrent() # pyright: ignore[reportUnknownVariableType]
    def MoveNext(self) -> bool: return GetEmptyEnumerator().MoveNext()
    def Stop(self) -> None: GetEmptyEnumerator().Stop()
    def TryReset(self) -> bool|None: return GetEmptyEnumerator().TryReset()
    def IsResetSupported(self) -> bool: return GetEmptyEnumerator().IsResetSupported()
    def SupportsMultipleCursors(self) -> bool: return False
    def PlaceCursor(self) -> IResumableEnumerationCursor: raise GetIterationInactiveError()
    def PlaceTopCursor(self) -> IResumableEnumerationCursor: raise GetIterationInactiveError()
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None: raise GetIterationInactiveError()
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None: raise GetIterationInactiveError()
@final
class _EmptyEnumerable[T](Iterable[T], IResumableEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return GetEmptyEnumerable().TryGetEnumerator() # pyright: ignore[reportUnknownVariableType]
    def TryGetResumableEnumerator(self) -> None: return None
    
    def AsIterable(self) -> Iterable[T]: return GetEmptyEnumerable().AsIterable() # pyright: ignore[reportUnknownVariableType]
    
    def __iter__(self) -> Iterator[T]: return GetEmptyEnumerator().AsIterator() # pyright: ignore[reportUnknownVariableType]

class ResumableEnumeratorProvider[T](EnumeratorProvider[T], IResumableEnumerable[T]):
    def __init__(self, enumeratorProvider: Function[IEnumerator[T]|None]|None, resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None) -> None:
        super().__init__(enumeratorProvider)
        
        self.__resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None = resumableEnumeratorProvider
    
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return None if self.__resumableEnumeratorProvider is None else self.__resumableEnumeratorProvider()

class ICursorCookie[T](ICookie[T], IRemovable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        ...
@final
class _Cookie[T](Abstract, ICursorCookie[T]):
    def __init__(self, node: INode, cookie: ICookie[T]) -> None:
        super().__init__()
        
        self.__node: INode = node
        self.__cookie: ICookie[T] = cookie
    
    def SetCursor(self, value: T) -> None: return self.__cookie.SetCursor(value)
    
    def MoveToTop(self) -> None: self.__node.TryMoveToBottom()
    
    def Remove(self) -> None: self.__node.Remove()

class ResumableEnumerationCursorAbstract[T](InvalidatableObjectProviderBase[ICursorCookie[T]], IResumableEnumerationCursor):
    def __init__(self) -> None:
        def throw() -> ICursorCookie[T]: raise InvalidOperationError("Object not initialized.")

        super().__init__()

        self.__cookie: Function[ICursorCookie[T]] = throw

    @final
    def _InitializeCookie(self, node: INode, cookie: ICookie[T]) -> None:
        cookie = _Cookie[T](node, cookie)

        self.__cookie = lambda: cookie

    @final
    def _GetValue(self) -> ICursorCookie[T]: return self.__cookie()
    
    @final
    def MoveToTop(self) -> None:
        self._GetValue().MoveToTop()
    
    def _OnDisposing(self, reason: DiscardReason) -> None:
        super()._OnDisposing(reason)

        self._GetValue().Remove()
    def _SetValueProvider(self, func: Function[ICursorCookie[T]]) -> None:
        self.__cookie = func
class ResumableEnumerationCursorBase[T](ResumableEnumerationCursorAbstract[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetCursorValue(self) -> T:
        ...
    
    @final
    def Resume(self) -> None:
        self._GetValue().SetCursor(self._GetCursorValue())

class ResumableEnumerationCursor[T](ResumableEnumerationCursorBase[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value

    @final
    def _GetCursorValue(self) -> T:
        return self.__value
    @abstractmethod
    def _GetDefaultCursorValue(self) -> T:
        ...
    
    def _DisposeOverride(self, reason: DiscardReason) -> None:
        super()._DisposeOverride(reason)

        self.__value = self._GetDefaultCursorValue()
class NullableResumableEnumerationCursor[T](ResumableEnumerationCursorBase[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T|None = value

    @final
    def _GetCursorItem(self) -> T|None:
        return self.__value
    
    def _DisposeOverride(self, reason: DiscardReason) -> None:
        super()._DisposeOverride(reason)

        self.__value = None

__emptyEnumerator = _EmptyEnumerator[Any]()
__emptyEnumerable = _EmptyEnumerable[Any]()

def TryGetResumableEnumerator[T](enumerable: IResumableEnumerable[T]|None) -> IResumableEnumerator[T]|None:
    return None if enumerable is None else enumerable.TryGetResumableEnumerator()

def GetEmptyResumableEnumerable[T]() -> IResumableEnumerable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerable
def GetEmptyResumableEnumerator[T]() -> IResumableEnumerator[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerator

def GetResumableEnumerable[T](enumerable: IResumableEnumerable[T]|None) -> IResumableEnumerable[T]:
    return GetEmptyResumableEnumerable() if enumerable is None else enumerable
def GetResumableEnumerator[T](enumerator: IResumableEnumerator[T]|None) -> IResumableEnumerator[T]:
    return GetEmptyResumableEnumerator() if enumerator is None else enumerator

def CreateResumableEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None], resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None) -> IResumableEnumerable[T]:
    return ResumableEnumeratorProvider[T](enumeratorProvider, resumableEnumeratorProvider)
def TryCreateResumableEnumeratorProvider[T](enumeratorProvider: Function[IResumableEnumerator[T]|None]|None, resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None) -> IResumableEnumerable[T]|None:
    return None if enumeratorProvider is None else CreateResumableEnumeratorProvider(enumeratorProvider, resumableEnumeratorProvider)