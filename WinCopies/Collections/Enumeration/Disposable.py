from abc import abstractmethod
from collections.abc import Iterator as _SystemIterator
from typing import final, Any

from WinCopies import IInterface, IDisposableAbstract, Abstract
from WinCopies.Collections.Enumeration import IIterationStatus, IEnumeratorBase, IEnumerator, IteratorBase as _IteratorBase, Iterator as _Iterator, ConverterEnumeratorBase, GetIterationInactiveError, GetNoDataEnumerationStatus
from WinCopies.Typing import INullable
from WinCopies.Typing.Discard import DiscardReason, IDisposableCookie, IDisposable, DisposableAbstract

class ICursorBase(IEnumeratorBase, IDisposable):
    def __init__(self) -> None: super().__init__()
class ICursor[T](IEnumerator[T], ICursorBase):
    def __init__(self) -> None: super().__init__()

@final
class _EmptyCursor[T](_IteratorBase[T], ICursor[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetCurrent(self) -> T: raise GetIterationInactiveError()
    def MoveNext(self) -> bool: return False
    def Stop(self) -> None: pass
    def TryReset(self) -> bool|None: return None
    def IsResetSupported(self) -> bool: return False
    
    def GetStatus(self) -> IIterationStatus: return GetNoDataEnumerationStatus()

    def Dispose(self) -> None: pass

__emptyCursor = _EmptyCursor[Any]()

def GetEmptyCursor[T]() -> ICursor[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyCursor

class IScannable[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryGetCursor(self) -> ICursor[T]|None:
        ...
    @final
    def GetCursor(self) -> ICursor[T]:
        cursor: ICursor[T]|None = self.TryGetCursor()

        return GetEmptyCursor() if cursor is None else cursor
class Scannable[T](Abstract, IScannable[T]):
    def __init__(self) -> None: super().__init__()

class Cursor[TRoot, THandle, TItem](ConverterEnumeratorBase[THandle, TItem], DisposableAbstract, ICursor[TItem]):
    def __init__(self, root: TRoot) -> None:
        def enumerate() -> _SystemIterator[THandle]:
            handle: INullable[THandle] = self._GetFirstHandle(root)

            def setNext() -> None:
                nonlocal handle

                handle = self._GetNextHandle(value)

            if self._OnRootHandleProcessed(root) and handle.HasValue():
                value: THandle = handle.GetValue()

                def setCurrent() -> bool:
                    nonlocal value

                    return self._OnHandleProcessing(value := handle.GetValue())

                if self._OnHandleProcessing(value):
                    yield value

                    setNext()

                    while self._OnHandleProcessed(value) and handle.HasValue() and setCurrent():
                        yield value

                        setNext()

        def updateCookie(cookie: IDisposableCookie) -> None: self.__disposableCookie = cookie
        
        super().__init__(_Iterator[THandle](enumerate()))

        self.__disposableCookie: IDisposableCookie = self._CreateDisposableCookie(updateCookie) # type: ignore[no-redef]

    @final
    def _GetDisposableCookie(self) -> IDisposableCookie: return self.__disposableCookie

    @abstractmethod
    def _GetFirstHandle(self, handle: TRoot) -> INullable[THandle]:
        ...
    @abstractmethod
    def _GetNextHandle(self, handle: THandle) -> INullable[THandle]:
        ...

    def _OnRootHandleProcessed(self, handle: TRoot) -> bool:
        return True
    
    def _OnHandleProcessing(self, handle: THandle) -> bool:
        return True
    def _OnHandleProcessed(self, handle: THandle) -> bool:
        return True

    def _OnStopping(self, enumerator: IEnumerator[THandle]) -> None:
        self._DisposeHandle(enumerator.GetCurrent())

        super()._OnStopping(enumerator)

    @abstractmethod
    def _DisposeHandle(self, handle: THandle) -> None:
        ...

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        self.Stop()

        super()._DisposeOverride(reason)

    def _Finalize(self) -> None:
        enumerator: IEnumerator[THandle] = self._GetContainer()

        if enumerator.IsStarted(): self._DisposeHandle(enumerator.GetCurrent())
        
        super()._Finalize()
class DisposableCursor[TRoot: IDisposableAbstract, THandle: IDisposableAbstract, TItem](Cursor[TRoot, THandle, TItem]):
    def __init__(self, root: TRoot) -> None: super().__init__(root)

    def _DisposeHandle(self, handle: TRoot|THandle) -> None:
        handle.Dispose()
    
    def _DisposeProcessedHandle(self, handle: TRoot|THandle) -> bool:
        self._DisposeHandle(handle)
        
        return True

    def _OnRootHandleProcessed(self, handle: TRoot) -> bool:
        return self._DisposeProcessedHandle(handle)
    def _OnHandleProcessed(self, handle: THandle) -> bool:
        return self._DisposeProcessedHandle(handle)