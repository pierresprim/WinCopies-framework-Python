from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, EnumeratorProvider
from WinCopies.Collections.Enumeration.Recursive.Base import IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, IRecursiveEnumerationDelegate, IRecursiveEnumerationCookie, IRecursivelyEnumerable
from WinCopies.Collections.Enumeration.Recursive._Base import FIFO, LIFO
from WinCopies.Collections.Enumeration.Recursive.Generic import RecursiveEnumeratorBase
from WinCopies.Collections.Linked.Singly import Stack

from WinCopies.Typing.Delegate import Converter, Function, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import DualResult

class RecursiveEnumerator[T](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandler[T]|None = None) -> None:
        super().__init__(enumerator, FIFO[T, None, IEnumerator[T]](self._GetCookie), handler)
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> IEnumerator[T]:
        return enumerator
    @final
    def _GetStackItemAsEnumerator(self, item: IEnumerator[T]) -> IEnumerator[T]:
        return item
    @final
    def _GetStackItemAsCookie(self, item: IEnumerator[T]) -> None:
        return None
class StackedRecursiveEnumerator[T](RecursiveEnumeratorBase[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> None:
        def getDelegate(enumerationOrder: EnumerationOrder, cookieProvider: Function[IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]]) -> IRecursiveEnumerationDelegate[T]|None:
            match enumerationOrder:
                case EnumerationOrder.Null:
                    return None
                case EnumerationOrder.FIFO:
                    return FIFO[T, T, DualResult[T, IEnumerator[T]]](cookieProvider)
                case EnumerationOrder.LIFO:
                    return LIFO[T](cookieProvider)
                case _:
                    raise ValueError(enumerationOrder)
        
        super().__init__(enumerator, getDelegate(enumerationOrder, self._GetCookie), handler)
    
    @final
    def _CreateStack(self) -> Stack[DualResult[T, IEnumerator[T]]]:
        return Stack[DualResult[T, IEnumerator[T]]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> DualResult[T, IEnumerator[T]]:
        return DualResult[T, IEnumerator[T]](item, enumerator)
    @final
    def _GetStackItemAsEnumerator(self, item: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return item.GetValue()
    @final
    def _GetStackItemAsCookie(self, item: DualResult[T, IEnumerator[T]]) -> T:
        return item.GetKey()

class _IEnumerator[T](IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
        pass

class DefaultRecursiveEnumerator[T](RecursiveEnumerator[T], _IEnumerator[T]):
    def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], converter: Converter[T, IEnumerable[T]], handler: IRecursiveEnumerationHandler[T]|None = None) -> None:
        super().__init__(enumerator, handler)

        self.__enumerable: RecursivelyEnumerable[T] = enumerable
        self.__converter: Converter[T, IEnumerable[T]] = converter
    
    @final
    def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
        return self.__enumerable
    
    @final
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        return self.__converter(enumerationItems)
class DefaultRecursiveStackedEnumerator[T](StackedRecursiveEnumerator[T], _IEnumerator[T]):
    def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], converter: Converter[T, IEnumerable[T]], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> None:
        super().__init__(enumerator, enumerationOrder, handler)

        self.__enumerable: RecursivelyEnumerable[T] = enumerable
        self.__converter: Converter[T, IEnumerable[T]] = converter
    
    @final
    def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
        return self.__enumerable
    
    @final
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        return self.__converter(enumerationItems)

@final
class _RecursivelyEnumerableUpdater[T](ValueFunctionUpdater[IEnumerable[T]]):
    def __init__(self, enumerable: IRecursivelyEnumerable[T], updater: Method[IFunction[IEnumerable[T]]]) -> None:
        super().__init__(updater)

        self.__enumerable: IRecursivelyEnumerable[T] = enumerable
    
    def _GetValue(self) -> IEnumerable[T]:
        return EnumeratorProvider[T](lambda: self.__enumerable.TryGetRecursiveEnumerator())

class RecursivelyEnumerable[T](Enumerable[T], IRecursivelyEnumerable[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IEnumerable[T]]) -> None:
            self.__recursive = func
        
        super().__init__()
    
        self.__recursive: IFunction[IEnumerable[T]] = _RecursivelyEnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    @abstractmethod
    def _AsRecursivelyEnumerable(self, container: T) -> IEnumerable[T]:
        pass

    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]:
        return self.__recursive.GetValue()
    
    def _TryGetRecursiveEnumerator(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return DefaultRecursiveEnumerator[T](self, enumerator, self._AsRecursivelyEnumerable, handler)
    def _TryGetRecursiveStackedEnumerator(self, enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return None if enumerationOrder == EnumerationOrder.Null else DefaultRecursiveStackedEnumerator[T](self, enumerator, self._AsRecursivelyEnumerable, enumerationOrder, handler)

    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        if enumerationOrder == EnumerationOrder.Null:
            return None
        
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        if enumerator is None:
            return None
        
        match enumerationOrder:
            case EnumerationOrder.FIFO:
                return self._TryGetRecursiveEnumerator(enumerator, handler)
            case EnumerationOrder.LIFO:
                return self._TryGetRecursiveStackedEnumerator(enumerator, EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())
            case _:
                raise ValueError(enumerationOrder)
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        if enumerationOrder == EnumerationOrder.Null:
            return None
        
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        return None if enumerator is None else self._TryGetRecursiveStackedEnumerator(enumerator, enumerationOrder, handler)