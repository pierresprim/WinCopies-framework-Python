from typing import final

from WinCopies import IStringable
from WinCopies.Collections import Extensions
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator
from WinCopies.Collections.Extensions import ITuple
from WinCopies.Collections.Linked import Singly, Doubly
from WinCopies.Typing import INullable, IEquatableItem, GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Pairing import IKeyValuePair

class Tuple[T](ITuple[T], IStringable):
    def __init__(self, items: ITuple[T]):
        super().__init__()

        self.__items: ITuple[T] = items
    
    @final
    def _GetItems(self) -> ITuple[T]:
        return self.__items
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def GetAt(self, key: int) -> T:
        return self._GetItems().GetAt(key)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetItems().TryGetEnumerator())
    
    def ToString(self) -> str:
        return self._GetItems().ToString()

class ReadOnlyDictionary[TKey: IEquatableItem, TValue](Extensions.IReadOnlyDictionary[TKey, TValue]):
    def __init__(self, dictionary: Extensions.IReadOnlyDictionary[TKey, TValue]):
        super().__init__()

        self.__dictionary: Extensions.IReadOnlyDictionary[TKey, TValue] = dictionary
    
    @final
    def _GetDictionary(self) -> Extensions.IReadOnlyDictionary[TKey, TValue]:
        return self.__dictionary
    
    @final
    def GetCount(self) -> int:
        return self._GetDictionary().GetCount()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return self._GetDictionary().ContainsKey(key)
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        return self._GetDictionary().TryGetValue(key)
    
    @final
    def GetAt(self, key: TKey) -> TValue:
        return self._GetDictionary().GetAt(key)
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> TValue|TDefault:
        return self._GetDictionary().TryGetAt(key, defaultValue)
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        return self._GetDictionary().GetKeys()
    @final
    def GetValues(self) -> ICountableEnumerable[TValue]:
        return self._GetDictionary().GetValues()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]|None:
        return Enumerator[IKeyValuePair[TKey, TValue]].TryCreate(self._GetDictionary().TryGetEnumerator())
    
    def ToString(self) -> str:
        return self._GetDictionary().ToString()

class ReadOnlySet[T: IEquatableItem](Extensions.IReadOnlySet[T]):
    def __init__(self, items: Extensions.IReadOnlySet[T]):
        super().__init__()

        self.__set: Extensions.IReadOnlySet[T] = items
    
    @final
    def _GetItems(self) -> Extensions.IReadOnlySet[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetItems().TryGetEnumerator())
    
    def ToString(self) -> str:
        return self._GetItems().ToString()

class ReadOnlySinglyLinkedListBase[TItem, TList](Singly.IReadOnlyList[TItem], GenericConstraint[TList, Singly.IReadOnlyList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def TryPeek(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryPeek()
class ReadOnlySinglyLinkedList[T](ReadOnlySinglyLinkedListBase[T, Singly.IReadOnlyList[T]], IGenericConstraintImplementation[Singly.IReadOnlyList[T]]):
    def __init__(self, items: Singly.IReadOnlyList[T]):
        super().__init__(items)

class ReadOnlyIterableSinglyLinkedList[T](ReadOnlySinglyLinkedListBase[T, Singly.IReadOnlyIterableList[T]], Singly.IReadOnlyIterableList[T], IGenericConstraintImplementation[Singly.IReadOnlyIterableList[T]]):
    def __init__(self, items: Singly.IReadOnlyIterableList[T]):
        super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
class ReadOnlyCountableList[T](ReadOnlySinglyLinkedListBase[T, Singly.IReadOnlyCountableList[T]], Singly.IReadOnlyCountableList[T], IGenericConstraintImplementation[Singly.IReadOnlyCountableList[T]]):
    def __init__(self, items: Singly.IReadOnlyCountableList[T]):
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

class ReadOnlyCountableIterableList[T](ReadOnlySinglyLinkedListBase[T, Singly.IReadOnlyCountableIterableList[T]], Singly.IReadOnlyCountableIterableList[T], IGenericConstraintImplementation[Singly.IReadOnlyCountableIterableList[T]]):
    def __init__(self, items: Singly.IReadOnlyCountableIterableList[T]):
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())

class ReadOnlyDoublyLinkedListBase[TItem, TList](Doubly.IReadOnlyList[TItem], GenericConstraint[TList, Doubly.IReadOnlyList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def TryGetFirst(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetFirst()
    @final
    def TryGetLast(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetLast()

class ReadOnlyDoublyLinkedList[T](ReadOnlyDoublyLinkedListBase[T, Doubly.IReadOnlyList[T]], IGenericConstraintImplementation[Doubly.IReadOnlyList[T]]):
    def __init__(self, items: Doubly.IReadOnlyList[T]):
        super().__init__(items)

class ReadOnlyIterableDoublyLinkedList[T](ReadOnlyDoublyLinkedListBase[T, Doubly.IReadOnlyIterableList[T]], Doubly.IReadOnlyIterableList[T], IGenericConstraintImplementation[Doubly.IReadOnlyIterableList[T]]):
    def __init__(self, items: Doubly.IReadOnlyIterableList[T]):
        super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())