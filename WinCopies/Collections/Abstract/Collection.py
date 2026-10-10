from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import final, overload, Self, SupportsIndex

from WinCopies import IStringable
from WinCopies.Collections.Abstract.Enumeration import ResumableEnumerableAbstract
from WinCopies.Collections.Abstract.Monitor import CollectionViewMonitor, EquatableCollectionViewMonitor
from WinCopies.Collections.Abstract.Selection import StringableConverter, StringableTwoWayConverter
from WinCopies.Collections.Abstraction.Collection import GetTuple, GetEquatableTuple, GetHashableTuple, GetArray, GetList
from WinCopies.Collections.Abstraction.Selection.Enumeration import CreateCountableEnumerable
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import (ICollectionViewMonitor, IEquatableCollectionViewMonitor,
                                              ICollectionMonitors,
                                              ITuple, IEquatableTuple, IHashableTuple,
                                              IArray, IList,
                                              Sequence, MutableSequence)
from WinCopies.Collections.Extensions.Collection import CollectionBase, ITupleBase, TupleAbstract as _TupleAbstract, TupleCollectionBase, EquatableTupleCollectionBase, HashableTupleCollectionBase, ArrayList
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Generic import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class TupleCollectionAbstractBase[TIn, TOut, TSequence: IStringable](StringableConverter[TIn, TOut, TSequence, ITuple[TIn]], Sequence[TOut], _TupleAbstract[TOut], ResumableEnumerableAbstract[TIn, TOut]):
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
class TupleCollectionAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstractBase[TIn, TOut, TSequence], ITupleBase[TOut]):
    def __init__(self) -> None: super().__init__()

class TupleAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstractBase[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|SequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(int(index))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class TupleBase[TIn, TOut, TSequence: IStringable](TupleAbstract[TIn, TOut, TSequence], ITupleBase[TOut]):
    def __init__(self) -> None: super().__init__()

class Tuple[TIn, TOut](TupleCollectionBase[TOut], TupleBase[TIn, TOut, ITuple[TIn]], IGenericConstraintImplementation[ITuple[TIn]]):
    def __init__(self, items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: ITuple[TIn] = (items := GetTuple(items))
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> ITuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.GetSourceMutability()

    @final
    def AsReadOnly(self) -> ITuple[TOut]: return self
    
    @final
    def SliceAt(self, key: slice) -> ITuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
class EquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](EquatableTupleCollectionBase[TOut], TupleBase[TIn, TOut, IEquatableTuple[TIn]], IGenericConstraintImplementation[IEquatableTuple[TIn]]):
    def __init__(self, items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IEquatableTuple[TIn] = (items := GetEquatableTuple(items))
        self.__monitor: IEquatableCollectionViewMonitor[TOut] = EquatableCollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCollectionViewMonitor(self) -> IEquatableCollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IEquatableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.GetSourceMutability()
    
    def Equals(self, item: object) -> bool: return self is item or self._GetContainer().Equals(item)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

    @final
    def AsImmutable(self) -> IEquatableTuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()
class HashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](HashableTupleCollectionBase[TOut], TupleAbstract[TIn, TOut, IHashableTuple[TIn]], IGenericConstraintImplementation[IHashableTuple[TIn]]):
    def __init__(self, items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IHashableTuple[TIn] = (items := GetHashableTuple(items))

    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IHashableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.GetSourceMutability()
    
    def Equals(self, item: object) -> bool: return self is item or self._GetContainer().Equals(item)
    def Hash(self) -> int: return self._GetContainer().Hash()
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class ArrayAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstract[TIn, TOut, TSequence], StringableTwoWayConverter[TIn, TOut, TSequence, ITuple[TIn]], GenericSpecializedConstraint[TSequence, ITuple[TIn], IArray[TIn]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(x, y)
    @final
    def _Swap(self, x: int, y: int) -> None: self._GetSpecializedContainer().Swap(x, y)
    
    @final
    def _SetAt(self, key: int, value: TOut) -> bool:
        return self._GetSpecializedContainer().TrySetAt(key, self._ConvertBack(value))

    @final
    def AsImmutable(self) -> ITuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()
class ArrayBase[TIn, TOut, TSequence: IStringable](TupleBase[TIn, TOut, TSequence], ArrayAbstract[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()

class Array[TIn, TOut](ArrayBase[TIn, TOut, IArray[TIn]], ArrayList[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IArray[TIn]]):
    def __init__(self, items: IArray[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IArray[TIn] = (items := GetArray(items))
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IArray[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.GetSourceMutability()
    
    @final
    def SliceAt(self, key: slice) -> IArray[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class List[TIn, TOut](ArrayAbstract[TIn, TOut, IList[TIn]], CollectionBase[TOut], MutableSequence[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IList[TIn]]):
    def __init__(self, items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn]) -> None:
        super().__init__()

        self.__items: IList[TIn] = (items := GetList(items))
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionViewMonitor[TIn, TOut](items, self)

    @final
    def __Select(self, items: Iterable[TOut]|None) -> Iterable[TIn]:
        return Select(items, self._ConvertBack)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IList[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.GetSourceMutability()
    
    @final
    def SliceAt(self, key: slice) -> IList[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
    
    @final
    def _TryInsert(self, index: int, value: TOut) -> bool: return self._GetContainer().TryInsert(index, self._ConvertBack(value))
    @final
    def _Insert(self, index: int, value: TOut) -> None: self._GetContainer().Insert(index, self._ConvertBack(value))
    @final
    def _TryInsertRange(self, index: int, items: Iterable[TOut]) -> bool: return self._GetContainer().TryInsertRange(index, self.__Select(items)) is True
    @final
    def _InsertRange(self, index: int, items: Iterable[TOut]) -> None: self._GetContainer().InsertRange(index, self.__Select(items))
    
    # Converted into a tuple rather than handed over as a projection: the container's answer
    # reads the items and its write reads them again, and a lazy Select would reach the first
    # reader only. The conversion is this layer's whole contribution -- whether the span may
    # be written is the inner container's to say, in its own vocabulary.
    @final
    def CanSetRange(self, indices: range, items: ICountableEnumerable[TOut]) -> bool:
        return self._GetContainer().CanSetRange(indices, CreateCountableEnumerable(items, self._ConvertBack))
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainer().TryRemoveAt(index)
    @final
    def _RemoveRange(self, index: int, count: int) -> None: return self._GetContainer().RemoveRange(index, count)
    
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