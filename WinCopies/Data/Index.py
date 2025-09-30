from __future__ import annotations

from abc import abstractmethod, ABC
from collections.abc import Iterable, Iterator
from enum import Enum
from typing import final

from WinCopies import IInterface, IStringable
from WinCopies.Collections.Abstraction.Collection import EquatableTuple, Set
from WinCopies.Collections.Enumeration import IEnumerable, IEquatableEnumerable, IEnumerator, IterableBase
from WinCopies.Collections.Extensions import IReadOnlyCollection, IEquatableTuple, ISet, ReadOnlyCollection
from WinCopies.Collections.Iteration import AppendIterableValues, PrependItem
from WinCopies.Collections.Linked.Singly import ICountableIterableList, CountableIterableQueue
from WinCopies.Typing import IEquatableObject, IString
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
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetType(self) -> IndexType:
        pass
    
    @abstractmethod
    def GetName(self) -> str:
        pass

class ISingleColumnIndex(IIndex):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> str:
        pass
class IMultiColumnIndex(IIndex):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> IEquatableTuple[IString]:
        pass

class IKey(IIndex):
    def __init__(self):
        super().__init__()
    
    @final
    def GetType(self) -> IndexType:
        return IndexType.Key
    
    @abstractmethod
    def GetKeyType(self) -> KeyType:
        pass

class ISingleColumnKey(IKey, ISingleColumnIndex):
    def __init__(self):
        super().__init__()
class IMultiColumnKey(IKey, IMultiColumnIndex):
    def __init__(self):
        super().__init__()

class IForeignKey(ISingleColumnKey):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetForeignKey(self) -> DualResult[str, str]:
        pass

class Index(ABC, IIndex):
    def __init__(self, name: str):
        super().__init__()
        
        self.__name: str = name
    
    @final
    def GetName(self) -> str:
        return self.__name

class SingleColumnIndex(Index, ISingleColumnIndex):
    def __init__(self, name: str, columns: str):
        super().__init__(name)

        self.__columns: str = columns
    
    @final
    def GetColumn(self) -> str:
        return self.__columns
class MultiColumnIndex(Index, IMultiColumnIndex):
    def __init__(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]):
        super().__init__(name)

        self.__columns: IEquatableTuple[IString] = columns if isinstance(columns, IEquatableTuple) else EquatableTuple[IString](columns)
    
    @final
    def GetColumns(self) -> IEquatableTuple[IString]:
        return self.__columns

class NormalIndex(SingleColumnIndex):
    def __init__(self, name: str, column: str):
        super().__init__(name, column)

    @final
    def GetType(self) -> IndexType:
        return IndexType.Normal
class UnicityIndex(MultiColumnIndex):
    def __init__(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]):
        super().__init__(name, columns)
    
    @final
    def GetType(self) -> IndexType:
        return IndexType.Unique

class PrimaryKey(MultiColumnIndex, IMultiColumnKey):
    def __init__(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]):
        super().__init__(name, columns)
    
    @final
    def GetKeyType(self) -> KeyType:
        return KeyType.Primary
class ForeignKey(SingleColumnIndex, IForeignKey):
    def __init__(self, name: str, column: str, foreignKey: DualResult[str, str]):
        super().__init__(name, column)

        self.__foreignKey: DualResult[str, str] = foreignKey
    
    @final
    def GetKeyType(self) -> KeyType:
        return KeyType.Foreign
    
    @final
    def GetForeignKey(self) -> DualResult[str, str]:
        return self.__foreignKey

class IIndexList[T: IIndex](IReadOnlyCollection[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Append(self, index: T) -> None:
        pass

class IIndexCollection(IEnumerable[IIndex]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetPrimaryKey(self) -> IMultiColumnKey:
        pass
    @abstractmethod
    def GetForeignKeys(self) -> IIndexList[IForeignKey]:
        pass
    @abstractmethod
    def GetNormalIndices(self) -> IIndexList[ISingleColumnIndex]:
        pass
    @abstractmethod
    def GetUnicityIndices(self) -> IIndexList[IMultiColumnIndex]:
        pass
class IndexCollection(IterableBase[IIndex], IIndexCollection):
    @final
    class __Indices(IInterface):
        class __IByName(IEquatableObject[IIndex]):
            def __init__(self):
                super().__init__()
            
            @abstractmethod
            def GetName(self) -> str:
                pass
            
            def Hash(self) -> int:
                return hash(self.GetName())
            
            def Equals(self, item: IIndex|object) -> bool:
                return isinstance(item, IIndex) and self.GetName() == item.GetName()
        @final
        class __ByName(__IByName):
            def __init__(self, index: IIndex):
                super().__init__()

                self.__index: IIndex = index
            
            def GetName(self) -> str:
                return self.__index.GetName()
        @final
        class __ByField(__IByName):
            def __init__(self, index: ISingleColumnIndex):
                super().__init__()

                self.__index: ISingleColumnIndex = index
            
            def GetName(self) -> str:
                return self.__index.GetColumn()
        @final
        class __ByFields(IEquatableObject[IMultiColumnIndex]):
            def __init__(self, index: IMultiColumnIndex):
                super().__init__()

                self.__index: IMultiColumnIndex = index
            
            def GetColumns(self) -> IEquatableEnumerable[IString]:
                return self.__index.GetColumns()
            
            def Hash(self) -> int:
                return self.GetColumns().Hash()
            
            def Equals(self, item: IMultiColumnIndex|object) -> bool:
                return isinstance(item, IMultiColumnIndex) and self.GetColumns().Equals(item.GetColumns())
        
        def __init__(self):
            super().__init__()

            self.__byName: ISet[IndexCollection.__Indices.__ByName] = Set[IndexCollection.__Indices.__ByName]()
            self.__byField: ISet[IndexCollection.__Indices.__ByField] = Set[IndexCollection.__Indices.__ByField]()
            self.__byFields: ISet[IndexCollection.__Indices.__ByFields] = Set[IndexCollection.__Indices.__ByFields]()
        
        def __TryAddIndex(self, index: IIndex) -> bool:
            return self.__byName.TryAdd(IndexCollection.__Indices.__ByName(index))
        
        def TryAddSingleColumnIndex(self, index: ISingleColumnIndex) -> bool:
            return self.__TryAddIndex(index) and self.__byField.TryAdd(IndexCollection.__Indices.__ByField(index))
        def TryAddMultiColumnIndex(self, index: IMultiColumnIndex) -> bool:
            return self.__TryAddIndex(index) and self.__byFields.TryAdd(IndexCollection.__Indices.__ByFields(index))
    
    class _Collection[T: IIndex](ReadOnlyCollection[T], IIndexList[T]):
        def __init__(self):
            super().__init__()

            self.__indices: ICountableIterableList[T] = CountableIterableQueue[T]()
        
        @final
        def _GetIndices(self) -> ICountableIterableList[T]:
            return self.__indices
        
        @abstractmethod
        def _Validate(self, index: T) -> bool:
            pass
        
        @final
        def IsEmpty(self) -> bool:
            return self.__indices.IsEmpty()
        
        @final
        def GetCount(self) -> int:
            return self.__indices.GetCount()
        
        @final
        def Append(self, index: T) -> None:
            if self._Validate(index):
                self._GetIndices().Push(index)
            
            else: raise KeyError()
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return self.__indices.TryGetEnumerator()
    
    @final
    class __SingleColumnIndexCollection[T: ISingleColumnIndex](_Collection[T]):
        def __init__(self, collection: IndexCollection.__Indices):
            super().__init__()
            
            self.__collection: IndexCollection.__Indices = collection
        
        @final
        def _Validate(self, index: ISingleColumnIndex) -> bool:
            return self.__collection.TryAddSingleColumnIndex(index)
        
        @final
        def Contains(self, value: T|object) -> bool:
            return isinstance(value, ISingleColumnIndex) and value in self._GetIndices().AsIterable() # type: ignore
    @final
    class __MultiColumnIndexCollection(_Collection[IMultiColumnIndex]):
        def __init__(self, collection: IndexCollection.__Indices):
            super().__init__()
            
            self.__collection: IndexCollection.__Indices = collection
        
        @final
        def _Validate(self, index: IMultiColumnIndex) -> bool:
            return self.__collection.TryAddMultiColumnIndex(index)
        
        @final
        def Contains(self, value: IMultiColumnIndex|object) -> bool:
            return isinstance(value, IMultiColumnIndex) and value in self._GetIndices().AsIterable()
    
    def __init__(self, primaryKey: IMultiColumnKey):
        super().__init__()

        indices: IndexCollection.__Indices = IndexCollection.__Indices()
        
        self.__normalIndices: IndexCollection.__SingleColumnIndexCollection[ISingleColumnIndex] = IndexCollection.__SingleColumnIndexCollection[ISingleColumnIndex](indices)
        self.__foreignKeys: IndexCollection.__SingleColumnIndexCollection[IForeignKey] = IndexCollection.__SingleColumnIndexCollection[IForeignKey](indices)
        self.__unicityIndices: IndexCollection.__MultiColumnIndexCollection = IndexCollection.__MultiColumnIndexCollection(indices)

        self.__primaryKey: IMultiColumnKey = primaryKey
    
    @final
    def GetPrimaryKey(self) -> IMultiColumnKey:
        return self.__primaryKey
    @final
    def GetForeignKeys(self) -> IIndexList[IForeignKey]:
        return self.__foreignKeys
    @final
    def GetNormalIndices(self) -> IIndexList[ISingleColumnIndex]:
        return self.__normalIndices
    @final
    def GetUnicityIndices(self) -> IIndexList[IMultiColumnIndex]:
        return self.__unicityIndices
    
    @final
    def _TryGetIterator(self) -> Iterator[IIndex]|None:
        return PrependItem(AppendIterableValues(self.GetUnicityIndices().AsIterable(), self.GetForeignKeys().AsIterable(), self.GetNormalIndices().AsIterable()), self.GetPrimaryKey())