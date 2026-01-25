from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface, Abstract

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, EnumeratorProvider, GetEnumerator

from WinCopies.Typing import INullable, IDisposable
from WinCopies.Typing.Delegate import Converter, Method, IFunction, ValueFunctionUpdater

class IRecursivelyEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveEnumerator(enumerationOrder, handler))

    @abstractmethod
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler))

    @final
    def GetRecursiveEnumerable(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerable[T]:
        return EnumeratorProvider[T](lambda: self.TryGetRecursiveEnumerator(enumerationOrder, handler))
    @final
    def GetRecursiveStackedEnumerable(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerable[T]:
        return EnumeratorProvider[T](lambda: self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler))
    
    @abstractmethod
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]:
        pass
    def AsRecursivelyIterable(self) -> Iterable[T]:
        return self.AsRecursivelyEnumerable().AsIterable()

class IRecursiveEnumerationHandlerBase[TItem, TCookie](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def OnStartingEnumeration(self) -> bool:
        pass
    
    @abstractmethod
    def OnEnteringEnumerationLevel(self, item: TItem) -> None:
        pass
    @abstractmethod
    def OnExitingEnumerationLevel(self, cookie: TCookie) -> None:
        pass
    
    @abstractmethod
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None:
        pass
    @abstractmethod
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool|None:
        pass
    
    @abstractmethod
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None:
        pass
    @abstractmethod
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None:
        pass
    
    @abstractmethod
    def OnStoppedEnumeration(self) -> None:
        pass

class IRecursiveEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, None]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[T]:
        pass
class IRecursiveStackedEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, T]):
    def __init__(self) -> None:
        super().__init__()

@final
class _Handler[T](Abstract, IRecursiveStackedEnumerationHandler[T]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T]) -> None:
        super().__init__()

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def OnStartingEnumeration(self) -> bool:
        return self.__handler.OnStartingEnumeration()
    
    def OnEnteringEnumerationLevel(self, item: T) -> None:
        return self.__handler.OnEnteringEnumerationLevel(item)
    def OnExitingEnumerationLevel(self, cookie: T) -> None:
        return self.__handler.OnExitingEnumerationLevel(None)
    
    def OnEnteringMainEnumerationLevel(self, item: T) -> bool|None:
        return self.__handler.OnEnteringMainEnumerationLevel(item)
    def OnExitingMainEnumerationLevel(self, cookie: T) -> bool|None:
        return self.__handler.OnExitingMainEnumerationLevel(None)
    
    def OnEnteringSubenumerationLevel(self, item: T) -> bool|None:
        return self.__handler.OnEnteringSubenumerationLevel(item)
    def OnExitingSubenumerationLevel(self, cookie: T) -> bool|None:
        return self.__handler.OnExitingSubenumerationLevel(None)
    
    def OnStoppedEnumeration(self) -> None:
        self.__handler.OnStoppedEnumeration()

class RecursiveEnumerationHandlerBase[TItem, TCookie](Abstract, IRecursiveEnumerationHandlerBase[TItem, TCookie]):
    def __init__(self) -> None:
        super().__init__()
    
    def OnStartingEnumeration(self) -> bool:
        return True
    
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None:
        return True
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool|None:
        return True
    
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None:
        return True
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None:
        return True
    
    def OnStoppedEnumeration(self) -> None:
        pass

@final
class _RecursiveEnumerationHandlerUpdater[T](ValueFunctionUpdater[IRecursiveStackedEnumerationHandler[T]]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T], updater: Method[IFunction[IRecursiveStackedEnumerationHandler[T]]]) -> None:
        super().__init__(updater)

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def _GetValue(self) -> IRecursiveStackedEnumerationHandler[T]:
        return _Handler[T](self.__handler)
class RecursiveEnumerationHandler[T](RecursiveEnumerationHandlerBase[T, None], IRecursiveEnumerationHandler[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IRecursiveStackedEnumerationHandler[T]]) -> None:
            self.__handler = func
        
        super().__init__()
    
        self.__handler: IFunction[IRecursiveStackedEnumerationHandler[T]] = _RecursiveEnumerationHandlerUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[T]:
        return self.__handler.GetValue()
class RecursiveStackedEnumerationHandler[T](RecursiveEnumerationHandlerBase[T, T], IRecursiveStackedEnumerationHandler[T]):
    def __init__(self) -> None:
        super().__init__()

@final
class _RecursiveEnumerationHandlerAbstractorUpdater[T](ValueFunctionUpdater[IRecursiveStackedEnumerationHandler[T]]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T], updater: Method[IFunction[IRecursiveStackedEnumerationHandler[T]]]) -> None:
        super().__init__(updater)

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def _GetValue(self) -> IRecursiveStackedEnumerationHandler[T]:
        return _Handler[T](self.__handler)

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
    def OnStartingEnumeration(self) -> bool:
        return self._GetHandler().OnStartingEnumeration()
    
    @final
    def OnEnteringEnumerationLevel(self, item: TIn) -> None:
        self._GetHandler().OnEnteringEnumerationLevel(self._Convert(item))
    
    @final
    def OnEnteringMainEnumerationLevel(self, item: TIn) -> bool|None:
        return self._GetHandler().OnEnteringMainEnumerationLevel(self._Convert(item))
    
    @final
    def OnEnteringSubenumerationLevel(self, item: TIn) -> bool|None:
        return self._GetHandler().OnEnteringSubenumerationLevel(self._Convert(item))
    
    @final
    def OnStoppedEnumeration(self) -> None:
        self._GetHandler().OnStoppedEnumeration()

class RecursiveEnumerationHandlerAbstractor[TIn, TOut](RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, None, None], IRecursiveEnumerationHandler[TIn]):
    def __init__(self, handler: IRecursiveEnumerationHandler[TOut]) -> None:
        def update(func: IFunction[IRecursiveStackedEnumerationHandler[TIn]]) -> None:
            self.__handler = func

        super().__init__(handler)

        self.__handler: IFunction[IRecursiveStackedEnumerationHandler[TIn]] = _RecursiveEnumerationHandlerAbstractorUpdater[TIn](self, update)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: None) -> None:
        self._GetHandler().OnExitingEnumerationLevel(cookie)
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: None) -> bool|None:
        return self._GetHandler().OnExitingMainEnumerationLevel(cookie)
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: None) -> bool|None:
        return self._GetHandler().OnExitingSubenumerationLevel(cookie)
    
    @final
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[TIn]:
        return self.__handler.GetValue()
class RecursiveStackedEnumerationHandlerAbstractor[TIn, TOut](RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, TIn, TOut], IRecursiveStackedEnumerationHandler[TIn]):
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[TOut]) -> None:
        super().__init__(handler)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: TIn) -> None:
        self._GetHandler().OnExitingEnumerationLevel(self._Convert(cookie))
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: TIn) -> bool|None:
        return self._GetHandler().OnExitingMainEnumerationLevel(self._Convert(cookie))
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: TIn) -> bool|None:
        return self._GetHandler().OnExitingSubenumerationLevel(self._Convert(cookie))

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
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)

class IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems](IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetEnumerator(self) -> IEnumerator[TEnumerationItems]:
        pass
    
    @abstractmethod
    def GetEnumerationItems(self, enumerationItems: TEnumerationItems) -> IEnumerable[TEnumerationItems]:
        pass

    @abstractmethod
    def MoveNext(self) -> bool:
        pass
    
    @abstractmethod
    def GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        pass
    @abstractmethod
    def GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    @abstractmethod
    def GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass
    
    @abstractmethod
    def Push(self, item: TStackItems) -> None:
        pass

    @abstractmethod
    def TryPeek(self) -> INullable[TStackItems]:
        pass
    
    @abstractmethod
    def TryPop(self) -> INullable[TStackItems]:
        pass
    
    @abstractmethod
    def OnEnteringSublevel(self, item: TEnumerationItems) -> bool|None:
        pass
    @abstractmethod
    def OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        pass
    
    @abstractmethod
    def OnEnteringMainLevel(self, item: TEnumerationItems) -> bool|None:
        pass
    @abstractmethod
    def OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        pass

class IRecursiveEnumerationDelegate[T](IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetOrder(self) -> EnumerationOrder:
        pass

    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass

    @abstractmethod
    def MoveNext(self) -> bool:
        pass