from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface, Abstract

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerableBase, IEnumerable, IEnumerator, EnumeratorProvider, GetEnumerator

from WinCopies.Typing.Delegate import Converter, Method, IFunction, ValueFunctionUpdater

class IRecursiveEnumerationHandlerBase[TItem, TCookie](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def OnStartingEnumeration(self) -> bool:
        ...
    
    @abstractmethod
    def OnEnteringEnumerationLevel(self, item: TItem) -> None:
        ...
    @abstractmethod
    def OnExitingEnumerationLevel(self, cookie: TCookie) -> None:
        ...
    
    @abstractmethod
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None:
        ...
    @abstractmethod
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool:
        ...
    
    @abstractmethod
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None:
        ...
    @abstractmethod
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None:
        ...
    
    @abstractmethod
    def OnStoppedEnumeration(self) -> None:
        ...

class IRecursiveStackedEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, T]):
    def __init__(self) -> None: super().__init__()
class IRecursiveEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, None]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[T]:
        ...

def TryAsStackHandler[T](delegate: IRecursiveEnumerationHandler[T]|None) -> IRecursiveStackedEnumerationHandler[T]|None:
    return None if delegate is None else delegate.AsStackHandler()

class IRecursivelyScannableBase[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        ...
    @final
    def GetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]: return GetEnumerator(self.TryGetRecursiveEnumerator(enumerationOrder, handler))
class IRecursivelyScannable[T](IRecursivelyScannableBase[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        ...
    @final
    def GetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]: return GetEnumerator(self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler))

    @final
    def GetRecursiveEnumerable(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerable[T]: return EnumeratorProvider[T](lambda: self.TryGetRecursiveEnumerator(enumerationOrder, handler))
    @final
    def GetRecursiveStackedEnumerable(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerable[T]: return EnumeratorProvider[T](lambda: self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler))
    
    @abstractmethod
    def AsRecursivelyIterable(self) -> Iterable[T]:
        ...

class IRecursivelyEnumerableBase[T](IRecursivelyScannableBase[T], IEnumerableBase[T]):
    def __init__(self) -> None: super().__init__()
class IRecursivelyEnumerable[T](IRecursivelyEnumerableBase[T], IRecursivelyScannable[T], IEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]:
        ...
    def AsRecursivelyIterable(self) -> Iterable[T]: return self.AsRecursivelyEnumerable().AsIterable()

@final
class _Handler[T](Abstract, IRecursiveStackedEnumerationHandler[T]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T]) -> None:
        super().__init__()

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def OnStartingEnumeration(self) -> bool: return self.__handler.OnStartingEnumeration()
    
    def OnEnteringEnumerationLevel(self, item: T) -> None: return self.__handler.OnEnteringEnumerationLevel(item)
    def OnExitingEnumerationLevel(self, cookie: T) -> None: return self.__handler.OnExitingEnumerationLevel(None)
    
    def OnEnteringMainEnumerationLevel(self, item: T) -> bool|None: return self.__handler.OnEnteringMainEnumerationLevel(item)
    def OnExitingMainEnumerationLevel(self, cookie: T) -> bool: return self.__handler.OnExitingMainEnumerationLevel(None)
    
    def OnEnteringSubenumerationLevel(self, item: T) -> bool|None: return self.__handler.OnEnteringSubenumerationLevel(item)
    def OnExitingSubenumerationLevel(self, cookie: T) -> bool|None: return self.__handler.OnExitingSubenumerationLevel(None)
    
    def OnStoppedEnumeration(self) -> None: self.__handler.OnStoppedEnumeration()

class RecursiveEnumerationHandlerBase[TItem, TCookie](Abstract, IRecursiveEnumerationHandlerBase[TItem, TCookie]):
    def __init__(self) -> None: super().__init__()
    
    def OnStartingEnumeration(self) -> bool: return True
    
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None: return True
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool: return True
    
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None: return True
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None: return True
    
    def OnStoppedEnumeration(self) -> None: pass

@final
class _RecursiveEnumerationHandlerUpdater[T](ValueFunctionUpdater[IRecursiveStackedEnumerationHandler[T]]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T], updater: Method[IFunction[IRecursiveStackedEnumerationHandler[T]]]) -> None:
        super().__init__(updater)

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def _GetValue(self) -> IRecursiveStackedEnumerationHandler[T]: return _Handler[T](self.__handler)
class RecursiveEnumerationHandler[T](RecursiveEnumerationHandlerBase[T, None], IRecursiveEnumerationHandler[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IRecursiveStackedEnumerationHandler[T]]) -> None: self.__handler = func
        
        super().__init__()
    
        self.__handler: IFunction[IRecursiveStackedEnumerationHandler[T]] = _RecursiveEnumerationHandlerUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[T]: return self.__handler.GetValue()
class RecursiveStackedEnumerationHandler[T](RecursiveEnumerationHandlerBase[T, T], IRecursiveStackedEnumerationHandler[T]):
    def __init__(self) -> None: super().__init__()

@final
class _RecursiveEnumerationHandlerAbstractorUpdater[T](ValueFunctionUpdater[IRecursiveStackedEnumerationHandler[T]]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T], updater: Method[IFunction[IRecursiveStackedEnumerationHandler[T]]]) -> None:
        super().__init__(updater)

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def _GetValue(self) -> IRecursiveStackedEnumerationHandler[T]: return _Handler[T](self.__handler)

class RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, TCookieIn, TCookieOut](Abstract, IRecursiveEnumerationHandlerBase[TIn, TCookieIn]):
    def __init__(self, handler: IRecursiveEnumerationHandlerBase[TOut, TCookieOut]) -> None:
        super().__init__()

        self.__handler: IRecursiveEnumerationHandlerBase[TOut, TCookieOut] = handler
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        pass
    
    @final
    def _GetHandler(self) -> IRecursiveEnumerationHandlerBase[TOut, TCookieOut]:
        return self.__handler

    @final
    def OnStartingEnumeration(self) -> bool: return self._GetHandler().OnStartingEnumeration()
    
    @final
    def OnEnteringEnumerationLevel(self, item: TIn) -> None: self._GetHandler().OnEnteringEnumerationLevel(self._Convert(item))
    
    @final
    def OnEnteringMainEnumerationLevel(self, item: TIn) -> bool|None: return self._GetHandler().OnEnteringMainEnumerationLevel(self._Convert(item))
    
    @final
    def OnEnteringSubenumerationLevel(self, item: TIn) -> bool|None: return self._GetHandler().OnEnteringSubenumerationLevel(self._Convert(item))
    
    @final
    def OnStoppedEnumeration(self) -> None: self._GetHandler().OnStoppedEnumeration()

class RecursiveEnumerationHandlerAbstractor[TIn, TOut](RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, None, None], IRecursiveEnumerationHandler[TIn]):
    def __init__(self, handler: IRecursiveEnumerationHandler[TOut]) -> None:
        def update(func: IFunction[IRecursiveStackedEnumerationHandler[TIn]]) -> None: self.__handler = func

        super().__init__(handler)

        self.__handler: IFunction[IRecursiveStackedEnumerationHandler[TIn]] = _RecursiveEnumerationHandlerAbstractorUpdater[TIn](self, update)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: None) -> None: self._GetHandler().OnExitingEnumerationLevel(cookie)
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: None) -> bool: return self._GetHandler().OnExitingMainEnumerationLevel(cookie)
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: None) -> bool|None: return self._GetHandler().OnExitingSubenumerationLevel(cookie)
    
    @final
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[TIn]: return self.__handler.GetValue()
class RecursiveStackedEnumerationHandlerAbstractor[TIn, TOut](RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, TIn, TOut], IRecursiveStackedEnumerationHandler[TIn]):
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[TOut]) -> None: super().__init__(handler)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: TIn) -> None: self._GetHandler().OnExitingEnumerationLevel(self._Convert(cookie))
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: TIn) -> bool: return self._GetHandler().OnExitingMainEnumerationLevel(self._Convert(cookie))
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: TIn) -> bool|None: return self._GetHandler().OnExitingSubenumerationLevel(self._Convert(cookie))

class RecursiveEnumerationHandlerConverter[TIn, TOut](RecursiveEnumerationHandlerAbstractor[TIn, TOut]):
    def __init__(self, handler: IRecursiveEnumerationHandler[TOut], converter: Converter[TIn, TOut]) -> None:
        super().__init__(handler)

        self.__converter: Converter[TIn, TOut] = converter
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
class RecursiveStackedEnumerationHandlerConverter[TIn, TOut](RecursiveStackedEnumerationHandlerAbstractor[TIn, TOut]):
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[TOut], converter: Converter[TIn, TOut]) -> None:
        super().__init__(handler)

        self.__converter: Converter[TIn, TOut] = converter
    
    @final
    def _Convert(self, item: TIn) -> TOut: return self.__converter(item)

@final
class __RecursiveUpdater[T](ValueFunctionUpdater[IEnumerable[T]]):
    def __init__(self, enumerable: IRecursivelyScannableBase[T], updater: Method[IFunction[IEnumerable[T]]]) -> None:
        super().__init__(updater)

        self.__enumerable: IRecursivelyScannableBase[T] = enumerable
    
    def _GetValue(self) -> IEnumerable[T]: return EnumeratorProvider[T](lambda: self.__enumerable.TryGetRecursiveEnumerator())
@final
class __IterableUpdater[T](ValueFunctionUpdater[Iterable[T]]):
    def __init__(self, enumerable: IRecursivelyEnumerableBase[T], updater: Method[IFunction[Iterable[T]]]) -> None:
        super().__init__(updater)

        self.__enumerable: IRecursivelyEnumerableBase[T] = enumerable
    
    def _GetValue(self) -> Iterable[T]: return EnumeratorProvider[T](lambda: self.__enumerable.TryGetEnumerator())

class RecursivelyScannableProvider[T](Abstract):
    def __init__(self, enumerable: IRecursivelyScannableBase[T]) -> None:
        def updateRecursive(func: IFunction[IEnumerable[T]]) -> None: self.__recursive = func
        
        super().__init__()

        self.__recursive: IFunction[IEnumerable[T]] = __RecursiveUpdater[T](enumerable, updateRecursive) # type: ignore[no-redef]
    
    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]: return self.__recursive.GetValue()
class RecursivelyIterableProvider[T](RecursivelyScannableProvider[T]):
    def __init__(self, enumerable: IRecursivelyEnumerableBase[T]) -> None:
        def updateIterable(func: IFunction[Iterable[T]]) -> None: self.__iterable = func
        
        super().__init__(enumerable)

        self.__iterable: IFunction[Iterable[T]] = __IterableUpdater[T](enumerable, updateIterable) # type: ignore[no-redef]
    
    @final
    def AsIterable(self) -> Iterable[T]: return self.__iterable.GetValue()

def CreateRecursivelyScannableProvider[T](enumerable: IRecursivelyScannableBase[T]) -> RecursivelyScannableProvider[T]:
    return RecursivelyScannableProvider[T](enumerable)
def CreateRecursivelyIterableProvider[T](enumerable: IRecursivelyEnumerableBase[T]) -> RecursivelyIterableProvider[T]:
    return RecursivelyIterableProvider[T](enumerable)