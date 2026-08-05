from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import final, overload, Self, SupportsIndex

from WinCopies import IStringable
from WinCopies.Collections.Abstract import StringableConverter, StringableTwoWayConverter
from WinCopies.Collections.Abstract.Enumeration import ResumableEnumerableAbstract
from WinCopies.Collections.Abstraction.Collection import GetTuple, GetEquatableTuple, GetHashableTuple, GetArray, GetList
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import ICollectionMonitors, ITuple, IEquatableTuple, IHashableTuple, IArray, IList, Sequence, MutableSequence
from WinCopies.Collections.Extensions.Collection import ICollectionViewMonitor, CollectionViewMonitorBase, Collection, ITupleBase, TupleAbstract, TupleCollectionBase, EquatableTupleCollection, HashableTupleCollection, ArrayList
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Action
from WinCopies.Typing.Generic import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class CollectionAbstractionViewMonitorBase[TIn, TOut](CollectionViewMonitorBase[TOut]):
    def __init__(self, source: ITuple[TIn], items: ITuple[TOut]) -> None:
        super().__init__(items)

        self.__source: ITuple[TIn] = source

    @final
    def _GetSource(self) -> ITuple[TIn]:
        return self.__source
class CollectionAbstractionViewMonitor[TIn, TOut](CollectionAbstractionViewMonitorBase[TIn, TOut]):
    def __init__(self, source: ITuple[TIn], items: ITuple[TOut]) -> None: super().__init__(source, items)

    @final
    def _CreateView(self, items: ITuple[TOut], onDisposed: Action) -> ITuple[TOut]:
        return self._GetSource().GetCollectionMonitors().GetRevocableViewMonitor().CreateRevocableView(items, onDisposed)

class TupleCollectionAbstract[TIn, TOut, TSequence: IStringable](StringableConverter[TIn, TOut, TSequence, ITuple[TIn]], Sequence[TOut], TupleAbstract[TOut], ResumableEnumerableAbstract[TIn, TOut], ITupleBase[TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _Clone(self, items: TSequence) -> Self:
        ...
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetAt(self, key: int) -> TOut:
        return self._Convert(self._GetInnerContainer().GetAt(key))
    
    @final
    def Contains(self, value: TOut|object) -> bool: return value in self.AsSequence()
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetInnerContainer().TryGetEnumerator()
    @final
    def _TryGetResumableEnumerator(self) -> IResumableEnumerator[TIn]|None:
        return self._GetInnerContainer().TryGetResumableEnumerator()
class TupleBase[TIn, TOut, TSequence: IStringable](TupleCollectionAbstract[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|SequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(int(index))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()

class Tuple[TIn, TOut](TupleCollectionBase[TOut], TupleBase[TIn, TOut, ITuple[TIn]], IGenericConstraintImplementation[ITuple[TIn]]):
    def __init__(self, items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: ITuple[TIn] = (items := GetTuple(items))
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionAbstractionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self.GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> ITuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()

    @final
    def AsReadOnly(self) -> ITuple[TOut]: return self
    
    @final
    def SliceAt(self, key: slice) -> ITuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
class EquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](TupleBase[TIn, TOut, IEquatableTuple[TIn]], EquatableTupleCollection[TOut], IGenericConstraintImplementation[IEquatableTuple[TIn]]):
    def __init__(self, items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IEquatableTuple[TIn] = GetEquatableTuple(items)
    
    @final
    def _GetContainer(self) -> IEquatableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    def Equals(self, item: object) -> bool: return self is item or self._GetContainer().Equals(item)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

    @final
    def AsImmutable(self) -> ITuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()
class HashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](TupleBase[TIn, TOut, IHashableTuple[TIn]], HashableTupleCollection[TOut], IGenericConstraintImplementation[IHashableTuple[TIn]]):
    def __init__(self, items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IHashableTuple[TIn] = GetHashableTuple(items)
    
    @final
    def _GetContainer(self) -> IHashableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    def Equals(self, item: object) -> bool: return self is item or self._GetContainer().Equals(item)
    def Hash(self) -> int: return self._GetContainer().Hash()
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

    @final
    def AsImmutable(self) -> ITuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()

class ArrayAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstract[TIn, TOut, TSequence], StringableTwoWayConverter[TIn, TOut, TSequence, ITuple[TIn]], GenericSpecializedConstraint[TSequence, ITuple[TIn], IArray[TIn]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(x, y)
    
    @final
    def _SetAt(self, key: int, value: TOut) -> None:
        self._GetSpecializedContainer().SetAt(key, self._ConvertBack(value))

    @final
    def AsImmutable(self) -> ITuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()
class ArrayBase[TIn, TOut, TSequence: IStringable](TupleBase[TIn, TOut, TSequence], ArrayAbstract[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()

class Array[TIn, TOut](ArrayBase[TIn, TOut, IArray[TIn]], ArrayList[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IArray[TIn]]):
    def __init__(self, items: IArray[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IArray[TIn] = (items := GetArray(items))
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionAbstractionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self.GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IArray[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    @final
    def Swap(self, x: int, y: int) -> None: super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class List[TIn, TOut](ArrayAbstract[TIn, TOut, IList[TIn]], Collection[TOut], MutableSequence[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IList[TIn]]):
    def __init__(self, items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IList[TIn] = GetList(items)
    
    @final
    def _GetContainer(self) -> IList[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    @final
    def Swap(self, x: int, y: int) -> None: super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
    
    @final
    def Add(self, item: TOut) -> None: self._GetContainer().Add(self._ConvertBack(item))
    
    @final
    def TryInsert(self, index: int, value: TOut) -> bool: return self._GetContainer().TryInsert(index, self._ConvertBack(value))
    @final
    def TryInsertRange(self, index: int, items: Iterable[TOut]) -> bool: return self._GetContainer().TryInsertRange(index, Select(items, lambda item: self._ConvertBack(item)))
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainer().TryRemoveAt(index)
    @final
    def _TryRemoveRange(self, index: int, count: int) -> bool: return self._GetContainer().TryRemoveRange(index, count)
    
    @final
    def Clear(self) -> None: self._GetContainer().Clear()
    
    @final
    def insert(self, index: int, value: TOut) -> None: self._GetContainer().AsMutableSequence().insert(index, self._ConvertBack(value))
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|MutableSequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(int(index))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TOut) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TOut]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TOut|Iterable[TOut]) -> None: self._GetContainer().AsMutableSequence()[index] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None: del self._GetContainer().AsMutableSequence()[index]