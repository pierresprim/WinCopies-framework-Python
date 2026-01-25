from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import Generator, EnumerationOrder, ICountable, IReadOnlyCollection
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable
from WinCopies.Typing import GenericConstraint, INullable

class IReadOnlyListBase[T](IReadOnlyCollection):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryPeek(self) -> INullable[T]:
        pass
class IReadOnlyList[T](IReadOnlyListBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetOrder(self) -> EnumerationOrder:
        pass

class IListBase[T](IReadOnlyListBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Push(self, value: T) -> None:
        pass
    
    @abstractmethod
    def PushItems(self, items: Iterable[T]) -> None:
        pass
    @final
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        self.PushItems(items)

        return True
    
    @final
    def PushValues(self, *values: T) -> None:
        self.PushItems(values)
    
    @abstractmethod
    def TryPop(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def AsGenerator(self) -> Generator[T]:
        result: INullable[T] = self.TryPop()

        while result.HasValue():
            yield result.GetValue()
            
            result = self.TryPop()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        pass
class IList[T](IListBase[T], IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyEnumerableListBase[T](IReadOnlyListBase[T], IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyEnumerableList[T](IReadOnlyEnumerableListBase[T], IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()

class IEnumerableListBase[T](IListBase[T], IReadOnlyEnumerableListBase[T]):
    def __init__(self) -> None:
        super().__init__()
class IEnumerableList[T](IEnumerableListBase[T], IList[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        pass

class IReadOnlyCountableListBase[T](IReadOnlyListBase[T], ICountable):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyCountableList[T](IReadOnlyCountableListBase[T], IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()

class ICountableListBase[T](IListBase[T], IReadOnlyCountableListBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsCountableGenerator(self) -> ICountableEnumerable[T]:
        pass
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        pass
class ICountableList[T](ICountableListBase[T], IList[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyCountableEnumerableListBase[T](IReadOnlyEnumerableListBase[T], IReadOnlyCountableListBase[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyCountableEnumerableList[T](IReadOnlyCountableEnumerableListBase[T], IReadOnlyEnumerableList[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None:
        super().__init__()

class ICountableEnumerableListBase[T](IEnumerableListBase[T], ICountableListBase[T], IReadOnlyCountableEnumerableListBase[T]):
    def __init__(self) -> None:
        super().__init__()
class ICountableEnumerableList[T](ICountableEnumerableListBase[T], IEnumerableList[T], ICountableList[T], IReadOnlyCountableEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        pass

class CollectionAbstract[TItems, TList](Abstract, IListBase[TItems], GenericConstraint[TList, IList[TItems]]):
    def __init__(self, l: TList) -> None:
        super().__init__()
        
        self.__list: TList = l
    
    def _GetContainer(self) -> TList:
        return self.__list
    def _GetCollection(self) -> TList:
        return self._GetContainer()

    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    @final
    def HasItems(self) -> bool:
        return self._GetInnerContainer().HasItems()
class CollectionBase[TItems, TList](CollectionAbstract[TItems, TList], IList[TItems]):
    def __init__(self, l: TList) -> None:
        super().__init__(l)