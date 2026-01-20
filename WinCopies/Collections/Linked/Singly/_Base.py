from collections.abc import Iterable, Iterator
from typing import final

from WinCopies.Collections import Generator, Countable as CountableCollectionBase
from WinCopies.Collections.Enumeration import ICountableEnumerable, IterableBase
from WinCopies.Collections.Linked.Singly.Base import IList, ICountableListBase, CollectionAbstract
from WinCopies.Typing import GenericConstraint, INullable
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater

@final
class _EnumerableUpdaterEnumerable[T](IterableBase[T], CountableCollectionBase, ICountableEnumerable[T]):
    def __init__(self, items: ICountableListBase[T]) -> None:
        super().__init__()

        self.__items: ICountableListBase[T] = items
    
    def _TryGetIterator(self) -> Iterator[T]|None:
        return self.__items.AsGenerator()
    
    def GetCount(self) -> int:
        return self.__items.GetCount()
@final
class _EnumerableUpdater[T](ValueFunctionUpdater[ICountableEnumerable[T]]):
    def __init__(self, items: ICountableListBase[T], updater: Method[IFunction[ICountableEnumerable[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableListBase[T] = items
    
    def _GetValue(self) -> ICountableEnumerable[T]:
        return _EnumerableUpdaterEnumerable[T](self.__items)

class _CountableCollectionAbstract[TItems, TList](CollectionAbstract[TItems, TList], CountableCollectionBase, ICountableListBase[TItems], GenericConstraint[TList, IList[TItems]]):
    def __init__(self, l: TList) -> None:
        def update(func: IFunction[ICountableEnumerable[TItems]]) -> None:
            self.__generator = func
        
        super().__init__(l)

        self.__count: int = 0
        self.__generator: IFunction[ICountableEnumerable[TItems]] = _EnumerableUpdater[TItems](self, update) # type: ignore[no-redef]
    
    @final
    def AsCountableGenerator(self) -> ICountableEnumerable[TItems]:
        return self.__generator.GetValue()
    
    @final
    def GetCount(self) -> int:
        return self.__count
    
    @final
    def __Increment(self) -> None:
        self.__count += 1
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().Push(value)

        self.__Increment()
    
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        def loop() -> Generator[TItems]:
            for item in items:
                yield item
                
                self.__Increment()
        
        self._GetInnerContainer().PushItems(loop())
    
    @final
    def TryPeek(self) -> INullable[TItems]:
        return self._GetInnerContainer().TryPeek()
    
    @final
    def TryPop(self) ->  INullable[TItems]:
        result: INullable[TItems] = self._GetInnerContainer().TryPop()

        if result.HasValue():
            self.__count -= 1
        
        return result
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

        self.__count = 0

class CountableCollectionAbstract[TItem, TList](_CountableCollectionAbstract[TItem, TList]):
    def __init__(self, l: TList) -> None:
        super().__init__(l)