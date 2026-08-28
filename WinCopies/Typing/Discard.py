from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IDisposableAbstract, IDisposable as IDisposableBase, Abstract
from WinCopies.Delegates import NoAction
from WinCopies.Typing import INullable, InvalidOperationError, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Action, Method, Function
from WinCopies.Typing.Enum import IntEnum

class UnusabilityReason(IntEnum):
    Null = 0
    Discarded = 1
    Broken = 2

class DiscardReason(IntEnum):
    Null = 0
    Finalized = 1
    Disposed = 2
    Invalidated = 3

    def IsExplicit(self) -> bool:
        return self > DiscardReason.Finalized

    def ToString(self) -> str:
        return '' if self == DiscardReason.Null else self.name

class UnusableError(InvalidOperationError):
    def __init__(self, message: str, *args: object) -> None: super().__init__(message, *args)

    @abstractmethod
    def GetUnusabilityReason(self) -> UnusabilityReason:
        ...

class DiscardedError(UnusableError):
    def __init__(self, message: str|None, *args: object) -> None: super().__init__(f"The current object has been {self.GetDiscardReason().ToString().lower()}." if message is None else message, *args)

    @final
    def GetUnusabilityReason(self) -> UnusabilityReason: return UnusabilityReason.Discarded

    @abstractmethod
    def GetDiscardReason(self) -> DiscardReason:
        ...

@final
class _DiscardedError(DiscardedError):
    def __init__(self) -> None: super().__init__("The object was discarded for unknown reason.")

    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Null

class DisposedError(DiscardedError):
    def __init__(self, *args: object) -> None: super().__init__(None, *args)

    @final
    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Disposed
class InvalidatedError(DiscardedError):
    def __init__(self, *args: object) -> None: super().__init__(None, *args)

    @final
    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Invalidated

class BrokenObjectError(UnusableError):
    def __init__(self, message: str, *args: object) -> None: super().__init__(message, *args)

    @final
    def GetUnusabilityReason(self) -> UnusabilityReason: return UnusabilityReason.Broken

def TryGetDiscardedError(discardReason: DiscardReason = DiscardReason.Disposed) -> DiscardedError|None:
    match discardReason:
        case DiscardReason.Disposed: return DisposedError()
        case DiscardReason.Invalidated: return InvalidatedError()

        case _: return None

def GetDiscardedError(discardReason: DiscardReason = DiscardReason.Disposed) -> DiscardedError:
    e: DiscardedError|None = TryGetDiscardedError(discardReason)

    return _DiscardedError() if e is None else e

def ThrowInvalidatedError() -> None:
    raise InvalidatedError()
def ThrowDisposedError() -> None:
    raise DisposedError()
def ThrowDiscardedError(discardReason: DiscardReason = DiscardReason.Disposed) -> None:
    raise GetDiscardedError(discardReason)

class IDisposable(IDisposableBase):
    def __init__(self) -> None: super().__init__()

    @final
    def _Throw(self) -> None: raise GetDiscardedError()

class _IDiscardable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetDiscardReason(self) -> DiscardReason:
        ...

class _IDisposableInfoBase(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def IsDisposed(self) -> bool:
        ...
class IDisposableInfo(_IDisposableInfoBase, IDisposable):
    def __init__(self) -> None: super().__init__()

class IDiscardableInfoBase(_IDisposableInfoBase, _IDiscardable, IDisposableAbstract):
    def __init__(self) -> None: super().__init__()

    @final
    def IsDisposed(self) -> bool: return self.GetDiscardReason() > DiscardReason.Null
class IDiscardableInfo(IDiscardableInfoBase, IDisposableBase):
    def __init__(self) -> None: super().__init__()

class IDiscardableItem(IDiscardableInfo, IDisposableInfo):
    def __init__(self) -> None: super().__init__()

class IInvalidatable(IDisposableBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _Dispose(self, reason: DiscardReason) -> None:
        ...

    @final
    def Dispose(self) -> None: self._Dispose(DiscardReason.Disposed)

    @final
    def Invalidate(self) -> None: self._Dispose(DiscardReason.Invalidated)
class IInvalidatableInfo(IInvalidatable, IDiscardableItem):
    def __init__(self) -> None: super().__init__()

class _IDisposableCookie(_IDiscardable):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Dispose(self, reason: DiscardReason) -> None:
        ...
class IDisposableCookie(_IDisposableCookie):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Initialize(self) -> None:
        ...

class DiscardableAbstract(IDiscardableItem):
    @final
    class _DisposableCookie(Abstract, IDisposableCookie):
        @final
        class _DisposedCookie(Abstract, IDisposableCookie):
            def __init__(self, reason: DiscardReason) -> None:
                super().__init__()

                self.__reason: DiscardReason = reason

            def GetDiscardReason(self) -> DiscardReason: return self.__reason

            def Initialize(self) -> None: pass

            def Dispose(self, reason: DiscardReason) -> None: pass
        
        def __init__(self, obj: DiscardableAbstract, updater: Method[IDisposableCookie]) -> None:
            def initialize() -> None:
                self.__initialize = NoAction

                self.__obj._Initialize()

            super().__init__()

            self.__obj: DiscardableAbstract = obj
            self.__updater: Method[IDisposableCookie] = updater

            self.__initialize: Action = initialize # type: ignore[no-redef]

        def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Null

        def Initialize(self) -> None: self.__initialize()

        def Dispose(self, reason: DiscardReason) -> None:
            if reason == DiscardReason.Null: return

            obj: DiscardableAbstract = self.__obj

            obj._OnDisposing(reason)

            if reason.IsExplicit(): obj._DisposeOverride(reason)

            obj._Finalize()

            self.__updater(DiscardableAbstract._DisposableCookie._DisposedCookie(reason))
    
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateDisposableCookie(self, updater: Method[IDisposableCookie]) -> IDisposableCookie:
        return DiscardableAbstract._DisposableCookie(self, updater)
    @abstractmethod
    def _GetDisposableCookie(self) -> IDisposableCookie:
        ...

    def _Initialize(self) -> None:
        ...
    @final
    def Initialize(self) -> None: return self._GetDisposableCookie().Initialize()

    def _OnDisposing(self, reason: DiscardReason) -> None:
        pass

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        pass
    
    def _Finalize(self) -> None:
        pass

    @final
    def _Dispose(self, reason: DiscardReason) -> None:
        self._GetDisposableCookie().Dispose(reason)

    @final
    def GetDiscardReason(self) -> DiscardReason: return self._GetDisposableCookie().GetDiscardReason()
class DisposableAbstract(DiscardableAbstract):
    def __init__(self) -> None: super().__init__()

    @final
    def Dispose(self) -> None: self._Dispose(DiscardReason.Disposed)

class DisposableBase(Abstract, DiscardableAbstract):
    def __init__(self) -> None:
        def update(cookie: IDisposableCookie) -> None: self.__disposableCookie = cookie

        super().__init__()

        self.__disposableCookie: IDisposableCookie = self._CreateDisposableCookie(update) # type: ignore[no-redef]

    @final
    def _GetDisposableCookie(self) -> IDisposableCookie: return self.__disposableCookie
class Disposable(DisposableBase):
    def __init__(self) -> None: super().__init__()

    @final
    def Dispose(self) -> None: self._Dispose(DiscardReason.Disposed)
class Invalidatable(DisposableBase, IInvalidatableInfo):
    def __init__(self) -> None: super().__init__()

class InvalidatableObjectProviderBase[T](Invalidatable):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetValue(self) -> T:
        ...

    @abstractmethod
    def _SetValueProvider(self, func: Function[T]) -> None:
        ...
class InvalidatableObjectProvider[T](InvalidatableObjectProviderBase[T]):
    def __init__(self, func: Function[T]) -> None:
        super().__init__()

        self.__func: Function[T] = func

    @final
    def _GetValue(self) -> T: return self.__func()

    @final
    def _SetValueProvider(self, func: Function[T]) -> None: self.__func = func

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        # A new error instance is built on each raise: re-raising a captured one would
        # chain a new traceback onto it every time, growing without bound and keeping
        # every frame — and its locals — alive. The object is typically held for the
        # lifetime of its consumer, so this would be a leak, not just noise.
        def throw(reason: DiscardReason) -> T: raise GetDiscardedError(reason)

        super()._DisposeOverride(reason)

        self._SetValueProvider(lambda: throw(reason))

class _IDisposableProviderItem[T: IDisposableInfo](_IDisposableInfoBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetItem(self) -> T:
        ...

    @abstractmethod
    def Dispose(self) -> _IDisposableProviderItem[T]:
        ...
@final
class _DisposedItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetItem(self) -> T: raise GetDiscardedError()

    def IsDisposed(self) -> bool: return True

    def Dispose(self) -> _IDisposableProviderItem[T]: return self

_disposedItem = _DisposedItem() # type: ignore

@final
class _DisposableProviderItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: T = item
    
    def GetItem(self) -> T: return self.__item

    def IsDisposed(self) -> bool: return self.__item.IsDisposed()
    
    def Dispose(self) -> _IDisposableProviderItem[T]:
        self.__item.Dispose()
        
        return _disposedItem # pyright: ignore[reportUnknownVariableType]

class IDisposableProvider[T: IDisposableInfo](IDisposableInfo):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetItem(self) -> T:
        ...
    
    @final
    def GetItem(self) -> T:
        if self.IsDisposed(): raise GetDiscardedError()
        
        return self._GetItem()
    @final
    def TryGetItem(self) -> INullable[T]:
        return GetNullValue() if self.IsDisposed() else GetNullable(self._GetItem())
class DisposableProvider[T: IDisposableInfo](Abstract, IDisposableProvider[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: _IDisposableProviderItem[T] = _DisposableProviderItem[T](item)
    
    @final
    def _GetItem(self) -> T:
        return self.__item.GetItem()
    
    @final
    def IsDisposed(self) -> bool: return self.__item.IsDisposed()
    
    @final
    def Dispose(self) -> None: self.__item = self.__item.Dispose()