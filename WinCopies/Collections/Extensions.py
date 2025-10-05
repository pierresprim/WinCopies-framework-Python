from __future__ import annotations

import collections.abc

from abc import abstractmethod
from collections.abc import Sized, Container, Iterable
from typing import final

from WinCopies import Collections, IStringable
from WinCopies.Collections import Enumeration, ICountableCollection, IReadOnlyCountableList, ICountableList as ICountableListBase
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEquatableEnumerable, IEnumerator, CountableEnumerable, GetIterator, TryAsIterator
from WinCopies.Typing import INullable, IEquatableItem, GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import IKeyValuePair

class IReadOnlyCollection[T](IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsCollection(self) -> collections.abc.Collection[T]:
        pass
    
    def AsSized(self) -> Sized:
        return self.AsCollection()
    def AsContainer(self) -> Container[T]:
        return self.AsCollection()
    def AsIterable(self) -> Iterable[T]:
        return self.AsCollection()

class IEnumerableCollection[T](IReadOnlyCollection[T], ICountableCollection[T]):
    def __init__(self):
        super().__init__()

class ICollection[T](IEnumerableCollection[T], ICountableListBase[T]):
    def __init__(self):
        super().__init__()

class ISequence[T](IReadOnlyCollection[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsSequence(self) -> collections.abc.Sequence[T]:
        pass

    def AsSized(self) -> Sized:
        return self.AsSequence()
    def AsContainer(self) -> Container[T]:
        return self.AsSequence()
    def AsIterable(self) -> Iterable[T]:
        return self.AsSequence()
    def AsCollection(self) -> collections.abc.Collection[T]:
        return self.AsSequence()
class IMutableSequence[T](ISequence[T], ICollection[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsMutableSequence(self) -> collections.abc.MutableSequence[T]:
        pass

    def AsSized(self) -> Sized:
        return self.AsMutableSequence()
    def AsContainer(self) -> Container[T]:
        return self.AsMutableSequence()
    def AsIterable(self) -> Iterable[T]:
        return self.AsMutableSequence()
    def AsCollection(self) -> collections.abc.Collection[T]:
        return self.AsMutableSequence()
    def AsSequence(self) -> collections.abc.Sequence[T]:
        return self.AsMutableSequence()

class ReadOnlyCollection[T](collections.abc.Collection[T], IReadOnlyCollection[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def __len__(self) -> int:
        return self.GetCount()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)
    
    def _TryGetIterator(self) -> collections.abc.Iterator[T]|None:
        return TryAsIterator(self.TryGetEnumerator())
    
    @final
    def __iter__(self) -> collections.abc.Iterator[T]:
        return GetIterator(self._TryGetIterator())
    
    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> collections.abc.Collection[T]:
        return self

class Sequence[T](collections.abc.Sequence[T], ReadOnlyCollection[T], ISequence[T]):
    def __init__(self):
        super().__init__()
    
    def AsSequence(self) -> collections.abc.Sequence[T]:
        return self

    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> collections.abc.Collection[T]:
        return self
class MutableSequence[T](collections.abc.MutableSequence[T], Sequence[T], IMutableSequence[T]):
    def __init__(self):
        super().__init__()
    
    def AsMutableSequence(self) -> collections.abc.MutableSequence[T]:
        return self

    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> collections.abc.Collection[T]:
        return self
    def AsSequence(self) -> collections.abc.Sequence[T]:
        return self

class ITuple[T](Collections.ITuple[T], ISequence[T], IStringable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        pass
class IEquatableTuple[T: IEquatableItem](Collections.IEquatableTuple[T], ITuple[T], IEquatableEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass
class IArray[T](Collections.IArray[T], ITuple[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        pass
class IList[T](Collections.IList[T], IArray[T], IMutableSequence[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        pass

# TODO: Should implement a Mapping abstractor provider.
class IReadOnlyDictionary[TKey: IEquatableItem, TValue](Collections.IReadOnlyDictionary[TKey, TValue], ICountableEnumerable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        pass
    @abstractmethod
    def GetValues(self) -> ICountableEnumerable[TValue]:
        pass
# TODO: Should implement a MutableMapping abstractor provider.
class IDictionary[TKey: IEquatableItem, TValue](Collections.IDictionary[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        pass

class IReadOnlySet[T: IEquatableItem](Collections.IReadOnlySet, ICountableEnumerable[T], IStringable):
    def __init__(self):
        super().__init__()
class ISet[T: IEquatableItem](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        pass

class ArrayBase[T](Collections.Tuple[T], ITuple[T]):
    class EnumeratorBase[TItem, TList](Enumeration.EnumeratorBase[TItem], GenericConstraint[TList, ITuple[TItem]]):
        def __init__(self, items: TList):
            super().__init__()

            self.__list: TList = items
            self.__i: int = -1
        
        def _GetContainer(self) -> TList:
            return self.__list
        
        def IsResetSupported(self) -> bool:
            return True
        
        def _MoveNextOverride(self) -> bool:
            self.__i += 1
            
            return self.__i < self._GetInnerContainer().GetCount()
        
        def GetCurrent(self) -> TItem:
            return self._GetInnerContainer().GetAt(self.__i)
        
        def _OnStopped(self) -> None:
            pass
        
        def _ResetOverride(self) -> bool:
            self.__i = -1

            return True
    class Enumerator(EnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
        def __init__(self, items: ITuple[T]):
            super().__init__(items)
    
    def __init__(self):
        super().__init__()
    
    # Not final to allow customization for the enumerator.
    def TryGetEnumerator(self) -> IEnumerator[T]:
        return ArrayBase[T].Enumerator(self)

class Tuple[T](ArrayBase[T]):
    def __init__(self):
        super().__init__()
class EquatableTuple[T: IEquatableItem](Tuple[T], IEquatableTuple[T]):
    def __init__(self):
        super().__init__()
class Array[T](Collections.Array[T], Tuple[T], IArray[T]):
    class _ReadOnlyTuple(ITuple[T], IStringable):
        def __init__(self, items: IArray[T]):
            super().__init__()

            self.__items: IArray[T] = items
        
        @final
        def _GetItems(self) -> IArray[T]:
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
    
    @final
    class __Updater(ValueFunctionUpdater[ITuple[T]]):
        def __init__(self, array: Array[T], updater: Method[IFunction[ITuple[T]]]):
            super().__init__(updater)

            self.__array: Array[T] = array
        
        def _GetValue(self) -> ITuple[T]:
            return self.__array._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[ITuple[T]]) -> None:
            self.__readOnly = func

        super().__init__()

        self.__readOnly: IFunction[ITuple[T]] = Array[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> ITuple[T]:
        return Array[T]._ReadOnlyTuple(self)
    @final
    def AsReadOnly(self) -> ITuple[T]:
        return self.__readOnly.GetValue()
class List[T](Collections.List[T], Array[T], IList[T]):
    def __init__(self):
        super().__init__()

class Set[T: IEquatableItem](CountableEnumerable[T], ISet[T]):
    class _ReadOnlySet(IReadOnlySet[T]):
        def __init__(self, items: IReadOnlySet[T]):
            super().__init__()

            self.__set: IReadOnlySet[T] = items
        
        @final
        def _GetItems(self) -> IReadOnlySet[T]:
            return self.__set
        
        @final
        def GetCount(self) -> int:
            return self._GetItems().GetCount()
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return Enumerator[T].TryCreate(self._GetItems().TryGetEnumerator())
        
        def ToString(self) -> str:
            return self._GetItems().ToString()
    
    @final
    class __Updater(ValueFunctionUpdater[IReadOnlySet[T]]):
        def __init__(self, items: Set[T], updater: Method[IFunction[IReadOnlySet[T]]]):
            super().__init__(updater)

            self.__items: Set[T] = items
        
        def _GetValue(self) -> IReadOnlySet[T]:
            return self.__items._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[IReadOnlySet[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlySet[T]] = Set[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlySet[T]:
        return Set[T]._ReadOnlySet(self)
    @final
    def AsReadOnly(self) -> IReadOnlySet[T]:
        return self.__readOnly.GetValue()

class Dictionary[TKey: IEquatableItem, TValue](CountableEnumerable[IKeyValuePair[TKey, TValue]], IDictionary[TKey, TValue]):
    # TODO: Should inherit from Mapping
    class _ReadOnlyDictionary(IReadOnlyDictionary[TKey, TValue]):
        def __init__(self, dictionary: Dictionary[TKey, TValue]):
            super().__init__()

            self.__dictionary: Dictionary[TKey, TValue] = dictionary
        
        @final
        def _GetDictionary(self) -> Dictionary[TKey, TValue]:
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
    
    @final
    class __Updater(ValueFunctionUpdater[IReadOnlyDictionary[TKey, TValue]]):
        def __init__(self, dictionary: Dictionary[TKey, TValue], updater: Method[IFunction[IReadOnlyDictionary[TKey, TValue]]]):
            super().__init__(updater)

            self.__dictionary: Dictionary[TKey, TValue] = dictionary
        
        def _GetValue(self) -> IReadOnlyDictionary[TKey, TValue]:
            return self.__dictionary._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyDictionary[TKey, TValue]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyDictionary[TKey, TValue]] = Dictionary[TKey, TValue].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        return Dictionary[TKey, TValue]._ReadOnlyDictionary(self)
    @final
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        return self.__readOnly.GetValue()