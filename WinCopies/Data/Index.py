from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from enum import Enum
from typing import final

from WinCopies import IStringable, Abstract
from WinCopies.Collections.Abstraction.Collection import CreateHashableTuple
from WinCopies.Collections.Abstraction.Mapping.Extensions import OrderedSet
from WinCopies.Collections.Enumeration import IEnumerable, IHashableEnumerable, IEnumerator, IterableBase
from WinCopies.Collections.Extensions import IReadOnlyCollection, IHashableTuple, IOrderedSet, ReadOnlyCollection
from WinCopies.Collections.Iteration import AppendIterableValues, PrependItem
from WinCopies.Collections.Linked.Singly import ICountableEnumerableList, CountableEnumerableQueue
from WinCopies.Typing.Comparison import IHashableItem
from WinCopies.Typing.Pairing import DualResult

class IndexType(Enum):
    Null = 0
    Normal = 1
    Unique = 2
    Key = 3

class KeyType(Enum):
    Null = 0
    Primary = 1
    Foreign = 2

class IndexKind(Enum):
    Null = 0
    Normal = 1
    Unique = 2
    PrimaryKey = 3
    ForeignKey = 4

class IIndex(IStringable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetType(self) -> IndexType:
        ...
    
    @abstractmethod
    def GetName(self) -> str:
        ...

class ISingleColumnIndex(IIndex):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> str:
        ...
class IMultiColumnIndex(IIndex):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> IHashableTuple[str]:
        ...

class IKey(IIndex):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetType(self) -> IndexType: return IndexType.Key
    
    @abstractmethod
    def GetKeyType(self) -> KeyType:
        ...

class ISingleColumnKey(IKey, ISingleColumnIndex):
    def __init__(self) -> None: super().__init__()
class IMultiColumnKey(IKey, IMultiColumnIndex):
    def __init__(self) -> None: super().__init__()

class IForeignKey(ISingleColumnKey):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetForeignKey(self) -> DualResult[str, str]:
        ...

class Index(Abstract, IIndex):
    def __init__(self, name: str) -> None:
        super().__init__()
        
        self.__name: str = name
    
    @final
    def GetName(self) -> str: return self.__name

class SingleColumnIndex(Index, ISingleColumnIndex):
    def __init__(self, name: str, columns: str) -> None:
        super().__init__(name)

        self.__columns: str = columns
    
    @final
    def GetColumn(self) -> str: return self.__columns
class MultiColumnIndex(Index, IMultiColumnIndex):
    def __init__(self, name: str, columns: IHashableTuple[str]|Iterable[str]) -> None:
        super().__init__(name)

        self.__columns: IHashableTuple[str] = columns if isinstance(columns, IHashableTuple) else CreateHashableTuple(columns)
    
    @final
    def GetColumns(self) -> IHashableTuple[str]: return self.__columns

class NormalIndex(SingleColumnIndex):
    def __init__(self, name: str, column: str) -> None: super().__init__(name, column)

    @final
    def GetType(self) -> IndexType: return IndexType.Normal
class UnicityIndex(MultiColumnIndex):
    def __init__(self, name: str, columns: IHashableTuple[str]|Iterable[str]) -> None: super().__init__(name, columns)
    
    @final
    def GetType(self) -> IndexType: return IndexType.Unique

class PrimaryKey(MultiColumnIndex, IMultiColumnKey):
    def __init__(self, name: str, columns: IHashableTuple[str]|Iterable[str]) -> None: super().__init__(name, columns)
    
    @final
    def GetKeyType(self) -> KeyType: return KeyType.Primary
class ForeignKey(SingleColumnIndex, IForeignKey):
    def __init__(self, name: str, column: str, foreignKey: DualResult[str, str]) -> None:
        super().__init__(name, column)

        self.__foreignKey: DualResult[str, str] = foreignKey
    
    @final
    def GetKeyType(self) -> KeyType: return KeyType.Foreign
    
    @final
    def GetForeignKey(self) -> DualResult[str, str]: return self.__foreignKey

class IIndexList[T: IIndex](IReadOnlyCollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Append(self, index: T) -> None:
        ...

class IIndexCollection(IEnumerable[IIndex]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetPrimaryKey(self) -> IMultiColumnKey:
        ...
    @abstractmethod
    def GetForeignKeys(self) -> IIndexList[IForeignKey]:
        ...
    @abstractmethod
    def GetNormalIndices(self) -> IIndexList[ISingleColumnIndex]:
        ...
    @abstractmethod
    def GetUnicityIndices(self) -> IIndexList[IMultiColumnIndex]:
        ...

@final
class _Indices(Abstract):
    class _IByName(IHashableItem[IIndex]):
        def __init__(self) -> None: super().__init__()
        
        @abstractmethod
        def GetName(self) -> str:
            ...
        
        def Equals(self, item: IIndex|object) -> bool:
            return isinstance(item, IIndex) and self.GetName() == item.GetName()
        def Hash(self) -> int:
            return hash(self.GetName())
    @final
    class _ByName(Abstract, _IByName):
        def __init__(self, index: IIndex) -> None:
            super().__init__()

            self.__index: IIndex = index
        
        def GetName(self) -> str: return self.__index.GetName()
    @final
    class _ByField(Abstract, _IByName):
        def __init__(self, index: ISingleColumnIndex) -> None:
            super().__init__()

            self.__index: ISingleColumnIndex = index
        
        def GetName(self) -> str: return self.__index.GetColumn()
    @final
    class _ByFields(Abstract, IHashableItem[IMultiColumnIndex]):
        def __init__(self, index: IMultiColumnIndex) -> None:
            super().__init__()

            self.__index: IMultiColumnIndex = index
        
        def GetColumns(self) -> IHashableEnumerable[str]: return self.__index.GetColumns()
        
        def Equals(self, item: IMultiColumnIndex|object) -> bool: return isinstance(item, IMultiColumnIndex) and self.GetColumns().Equals(item.GetColumns())
        def Hash(self) -> int: return self.GetColumns().Hash()
    
    def __init__(self) -> None:
        super().__init__()

        self.__byName: IOrderedSet[_Indices._ByName] = OrderedSet[_Indices._ByName]()
        self.__byField: IOrderedSet[_Indices._ByField] = OrderedSet[_Indices._ByField]()
        self.__byFields: IOrderedSet[_Indices._ByFields] = OrderedSet[_Indices._ByFields]()
    
    def __TryAddIndex(self, index: IIndex) -> bool:
        return self.__byName.TryAdd(_Indices._ByName(index))
    
    def TryAddSingleColumnIndex(self, index: ISingleColumnIndex) -> bool:
        return self.__TryAddIndex(index) and self.__byField.TryAdd(_Indices._ByField(index))
    def TryAddMultiColumnIndex(self, index: IMultiColumnIndex) -> bool:
        return self.__TryAddIndex(index) and self.__byFields.TryAdd(_Indices._ByFields(index))

class _Collection[T: IIndex](ReadOnlyCollection[T], IIndexList[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__indices: ICountableEnumerableList[T] = CountableEnumerableQueue[T]()
    
    @final
    def _GetIndices(self) -> ICountableEnumerableList[T]:
        return self.__indices
    
    @abstractmethod
    def _Validate(self, index: T) -> bool:
        ...
    
    @final
    def IsEmpty(self) -> bool: return self.__indices.IsEmpty()
    
    @final
    def GetCount(self) -> int: return self.__indices.GetCount()
    
    @final
    def Append(self, index: T) -> None:
        if self._Validate(index): self._GetIndices().Push(index)
        else: raise KeyError()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__indices.TryGetEnumerator()

@final
class _SingleColumnIndexCollection[T: ISingleColumnIndex](_Collection[T]):
    def __init__(self, collection: _Indices) -> None:
        super().__init__()
        
        self.__collection: _Indices = collection
    
    @final
    def _Validate(self, index: ISingleColumnIndex) -> bool:
        return self.__collection.TryAddSingleColumnIndex(index)
    
    @final
    def Contains(self, value: T|object) -> bool: return isinstance(value, ISingleColumnIndex) and value in self._GetIndices().AsIterable() # type: ignore
@final
class _MultiColumnIndexCollection(_Collection[IMultiColumnIndex]):
    def __init__(self, collection: _Indices) -> None:
        super().__init__()
        
        self.__collection: _Indices = collection
    
    @final
    def _Validate(self, index: IMultiColumnIndex) -> bool:
        return self.__collection.TryAddMultiColumnIndex(index)
    
    @final
    def Contains(self, value: IMultiColumnIndex|object) -> bool: return isinstance(value, IMultiColumnIndex) and value in self._GetIndices().AsIterable()

class IndexCollection(IterableBase[IIndex], IIndexCollection):
    def __init__(self, primaryKey: IMultiColumnKey) -> None:
        super().__init__()

        indices: _Indices = _Indices()
        
        self.__normalIndices: _SingleColumnIndexCollection[ISingleColumnIndex] = _SingleColumnIndexCollection[ISingleColumnIndex](indices)
        self.__foreignKeys: _SingleColumnIndexCollection[IForeignKey] = _SingleColumnIndexCollection[IForeignKey](indices)
        self.__unicityIndices: _MultiColumnIndexCollection = _MultiColumnIndexCollection(indices)

        self.__primaryKey: IMultiColumnKey = primaryKey
    
    @final
    def GetPrimaryKey(self) -> IMultiColumnKey: return self.__primaryKey
    @final
    def GetForeignKeys(self) -> IIndexList[IForeignKey]: return self.__foreignKeys
    @final
    def GetNormalIndices(self) -> IIndexList[ISingleColumnIndex]: return self.__normalIndices
    @final
    def GetUnicityIndices(self) -> IIndexList[IMultiColumnIndex]: return self.__unicityIndices
    
    @final
    def _TryGetIterator(self) -> Iterator[IIndex]|None: return PrependItem(AppendIterableValues(self.GetUnicityIndices().AsIterable(), self.GetForeignKeys().AsIterable(), self.GetNormalIndices().AsIterable()), self.GetPrimaryKey())