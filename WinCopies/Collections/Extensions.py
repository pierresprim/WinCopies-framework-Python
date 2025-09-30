from __future__ import annotations

import collections.abc

from abc import abstractmethod
from collections.abc import Sized, Container, Iterable
from typing import final

from WinCopies import Collections, IStringable
from WinCopies.Collections import Enumeration, ICountableCollection, ICountableList as ICountableListBase
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEquatableEnumerable, IEnumerator, GetIterator, TryAsIterator
from WinCopies.Typing import IEquatableItem, GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Pairing import IKeyValuePair

class IReadOnlyCollection[T](ICountableCollection[T], ICountableEnumerable[T]):
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
class IMutableSequence[T](ISequence[T]):
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
class IEquatableTuple[T: IEquatableItem](ITuple[T], IEquatableEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass
class IArray[T](Collections.IArray[T], ITuple[T]):
    def __init__(self):
        super().__init__()
class IList[T](Collections.IList[T], IArray[T], IMutableSequence[T]):
    def __init__(self):
        super().__init__()

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

class IReadOnlySet[T: IEquatableItem](Collections.IReadOnlySet, ICountableEnumerable[T], IStringable):
    def __init__(self):
        super().__init__()
class ISet[T: IEquatableItem](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self):
        super().__init__()

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
class Array[T](Collections.Array[T], ArrayBase[T], IArray[T]):
    def __init__(self):
        super().__init__()
class List[T](Collections.List[T], ArrayBase[T], IList[T]):
    def __init__(self):
        super().__init__()