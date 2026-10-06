from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase
from typing import overload, final, Callable, SupportsIndex



from WinCopies import IInterface, Abstract

from WinCopies.Collections.Abstraction.Enumeration import TryCreateEnumerator, TryCreateResumableEnumerator
from WinCopies.Collections.Core import Mutability, IIndexableCollectionBase, IGetter, ISetter, ISwappable, Tuple as _Tuple, Array as _Array, List as _List, SortedList as _SortedList
from WinCopies.Collections.Enumeration.Core import IInvalidatableEnumeratorBase, IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import (ICollectionViewMonitor, IEquatableCollectionViewMonitor, IHashableCollectionViewMonitor,
                                              ICollectionMonitors, IResumableEnumeratorMonitor, IRevocableViewMonitor, ICollection,
                                              ITupleBase as ITupleAbstract, ITuple, ISortedTuple, IEquatableTuple, IHashableTuple,
                                              IArray,
                                              IListBase, IList, ISortedList,
                                              CollectionViewMonitor, EquatableCollectionViewMonitor,
                                              SequenceAbstract, MutableSequenceAbstract, Sequence, MutableSequence)
from WinCopies.Collections.Extensions.Enumeration import IResumableEnumeratorRegistry, ResumableEnumeratorRegistry, TupleEnumerator, ResumableTupleEnumerator
from WinCopies.Collections.Extensions.Revocable import IRevocableViewRegistry, RevocableViewRegistry
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Registry import IObjectMonitor, ICollectionRegistry
from WinCopies.Collections.Registry.Core import CollectionRegistry
from WinCopies.Collections.Iteration.Extensions import Reverse
from WinCopies.Collections.ObjectModel import ReadOnlyCollection, SortedCollection as SortedCollectionBase, FixedSizeCollection
from WinCopies.Collections.Util import FindIndex, ReverseIndexFromLast

from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import INotHashableValue, EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Method, Function, Converter, EqualityComparison, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraint, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Pairing import DualValueBool
from WinCopies.Typing.Protocols import SupportsEqualityAndRichComparison

class _IReversed[T](ITuple[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[T]:
        ...

    @final
    def AsImmutable(self) -> ITuple[T]: return self._GetCollectionViewMonitor().GetImmutableView()

class _ReversedAbstract[TItem, TCollectionIn, TCollectionOut](SequenceBase[TItem], ITuple[TItem], GenericConstraint[TCollectionIn, ITuple[TItem]]):
    def __init__(self, items: TCollectionIn) -> None:
        super().__init__()

        self.__items: TCollectionIn = items
    
    @final
    def _GetContainer(self) -> TCollectionIn: return self.__items
    
    @abstractmethod
    def _SliceAt(self, key: slice) -> TCollectionOut:
        ...

    @final
    def ToSlicedAt(self, key: slice) -> TCollectionOut:
        return self._SliceAt(self.ReverseKey(key))
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def TryGetValue(self, key: int) -> INullable[TItem]: return self._GetInnerContainer().TryGetValue(self.ReverseIndex(key))
    
    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindLastIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindFirstIndex(item, predicate)
    
    @final
    def ToString(self) -> str: return self._GetInnerContainer().ToString()
class _ReversedBase[TItem, TCollectionIn, TCollectionOut](_ReversedAbstract[TItem, TCollectionIn, TCollectionOut]):
    def __init__(self, items: TCollectionIn) -> None: super().__init__(items)
    
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetInnerContainer().GetCollectionMonitors()
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().GetSourceMutability()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]: return self.GetCollectionMonitors().GetEnumeratorMonitor().CreateEnumerator(self)
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]: return self.GetCollectionMonitors().GetEnumeratorMonitor().CreateResumableEnumerator(self)

class _Reversed[TItem, TCollection](_ReversedBase[TItem, TCollection, TCollection]):
    def __init__(self, items: TCollection) -> None: super().__init__(items)

@final
class _RevocableTupleProviderUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, items: ITuple[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__monitor: ICollectionViewMonitor[T] = CollectionViewMonitor[T](items)

    def _GetValue(self) -> ITuple[T]: return self.__monitor.GetImmutableView()
@final
class _RevocableTupleProvider[T](Abstract, IFunction[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__items = func
        
        super().__init__()

        self.__items: IFunction[ITuple[T]] = _RevocableTupleProviderUpdater[T](items, update) # type: ignore[no-redef]

    def GetValue(self) -> ITuple[T]: return self.__items.GetValue()

@final
class _RevocableEquatableTupleProviderUpdater[T](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__monitor: IEquatableCollectionViewMonitor[T] = EquatableCollectionViewMonitor[T](items)

    def _GetValue(self) -> IEquatableTuple[T]: return self.__monitor.GetImmutableView()
@final
class _RevocableEquatableTupleProvider[T](Abstract, IFunction[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None: self.__items = func
        
        super().__init__()

        self.__items: IFunction[IEquatableTuple[T]] = _RevocableEquatableTupleProviderUpdater[T](items, update) # type: ignore[no-redef]

    def GetValue(self) -> IEquatableTuple[T]: return self.__items.GetValue()

@final
class _ReversedTuple[T](_Reversed[T, ITuple[T]], SequenceAbstract[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)

        self.__func: Function[ITuple[T]] = (lambda: self) if items.IsImmutable() else _RevocableTupleProvider[T](self)
    
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    def _SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> ITuple[T]: return self._GetContainer()

    def AsImmutable(self) -> ITuple[T]: return self.__func()
    def AsReadOnly(self) -> ITuple[T]: return self
@final
class _ReversedTupleUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: ITuple[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ITuple[T] = array
    
    def _GetValue(self) -> ITuple[T]: return _ReversedTuple[T](self.__array)

@final
class _ReversedSortedTuple[T: SupportsEqualityAndRichComparison](_Reversed[T, ISortedTuple[T]], SequenceAbstract[T], ISortedTuple[T], IGenericConstraintImplementation[ISortedTuple[T]]):
    def __init__(self, items: ISortedTuple[T]) -> None:
        super().__init__(items)

        self.__monitor: ICollectionViewMonitor[T] = CollectionViewMonitor[T](items)
    
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    def TryBisect(self, item: T, right: bool = False) -> DualValueBool[int]: return self._GetContainer().TryBisect(item, right)
    def TryBisectWithKey[_T: SupportsEqualityAndRichComparison](self, item: _T, converter: Converter[T, _T], right: bool = False) -> DualValueBool[int]: return self._GetContainer().TryBisectWithKey(item, converter, right)
    
    def _SliceAt(self, key: slice) -> ISortedTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> ISortedTuple[T]: return self._GetContainer()

    def AsImmutable(self) -> ITuple[T]: return self.__monitor.GetImmutableView()
    def AsReadOnly(self) -> ITuple[T]: return self
@final
class _ReversedSortedTupleUpdater[T: SupportsEqualityAndRichComparison](ValueFunctionUpdater[ISortedTuple[T]]):
    def __init__(self, array: ISortedTuple[T], updater: Method[IFunction[ISortedTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ISortedTuple[T] = array
    
    def _GetValue(self) -> ISortedTuple[T]: return _ReversedSortedTuple[T](self.__array)

class _IReadOnlyTuple[TItem, TList](ITuple[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetInnerContainer().GetCollectionMonitors()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().GetSourceMutability()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return TryCreateEnumerator(self._GetInnerContainer().TryGetEnumerator())
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]|None: return TryCreateResumableEnumerator(self._GetInnerContainer().TryGetResumableEnumerator())

    @final
    def AsImmutable(self) -> ITuple[TItem]: return self._GetInnerContainer().AsImmutable()

class _ReadOnlyTuple[T](ReadOnlyCollection[T], _IReadOnlyTuple[T, ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[ITuple[T]] = _ReversedTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> ITuple[T]: return self.__reversed.GetValue()
    
    @final
    def AsReadOnly(self) -> ITuple[T]: return self
class _ReadOnlySortedTuple[T: SupportsEqualityAndRichComparison](SortedCollectionBase[T], _IReadOnlyTuple[T, ISortedTuple[T]]):
    def __init__(self, items: ISortedList[T]) -> None:
        def update(func: IFunction[ISortedTuple[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[ISortedTuple[T]] = _ReversedSortedTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    def TryBisect(self, item: T, right: bool = False) -> DualValueBool[int]: return self._GetContainer().TryBisect(item, right)
    def TryBisectWithKey[_T: SupportsEqualityAndRichComparison](self, item: _T, converter: Converter[T, _T], right: bool = False) -> DualValueBool[int]: return self._GetContainer().TryBisectWithKey(item, converter, right)
    
    @final
    def AsReversed(self) -> ISortedTuple[T]: return self.__reversed.GetValue()
    
    @final
    def AsReadOnly(self) -> ITuple[T]: return self

class GetterBase[TKey, TValue](Abstract, IGetter[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetAt(self, key: TKey) -> TValue:
        pass
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]: return GetNullable(self._GetAt(key)) if self.ContainsKey(key) else GetNullValue()
class SetterBase[TKey, TValue](Abstract, ISetter[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _SetAt(self, key: TKey, value: TValue) -> None:
        ...
    
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if self.ContainsKey(key):
            self._SetAt(key, value)

            return True
        
        return False

class KeyableBase[TKey, TValue](GetterBase[TKey, TValue], SetterBase[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

class TupleAbstractBase[T](GetterBase[int, T], _Tuple[T], ITuple[T]):
    def __init__(self) -> None: super().__init__()
class TupleAbstract[T](TupleAbstractBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return FindIndex(self.AsSequence(), item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return FindIndex(self.AsReversed().AsSequence(), item, predicate)

class IViewProvider(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _InvalidateViews(self) -> None:
        ...
class ITupleBase[T](ITupleAbstract[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[T]:
        ...
class IManagedCollection[T](ITupleBase[T], IViewProvider):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetCollectionRegistries(self) -> ICollectionRegistries:
        ...
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors:
        return self._GetCollectionRegistries().AsMonitors()

    @final
    def _InvalidateViews(self) -> None: self._GetCollectionRegistries().InvalidateObjects()

class _TupleBase[T](TupleAbstractBase[T], IManagedCollection[T]):
    def __init__(self) -> None: super().__init__()

    def __RegisterEnumerator[U: IInvalidatableEnumeratorBase](self, enumerator: U) -> U:
        self._GetEnumeratorRegistry().RegisterEnumerator(enumerator)

        return enumerator

    def _GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry:
        return self._GetCollectionRegistries().GetEnumeratorRegistry()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]: return self.__RegisterEnumerator(TupleEnumerator[T](self))
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]: return self.__RegisterEnumerator(ResumableTupleEnumerator[T](self))
class TupleBase[T](_TupleBase[T], TupleAbstract[T]):
    def __init__(self) -> None: super().__init__()

@final
class _ReversedEquatableTuple[T: EquatableProtocol](_Reversed[T, IEquatableTuple[T]], SequenceAbstract[T], IEquatableTuple[T], INotHashableValue, IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None:
        super().__init__(items)

        self.__func: Function[IEquatableTuple[T]] = (lambda: self) if items.IsImmutable() else _RevocableEquatableTupleProvider[T](self)

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    def _SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self.ToSlicedAt(key)
    
    def Equals(self, item: object) -> bool: return self._GetContainer().Equals(item)

    def AsReversed(self) -> IEquatableTuple[T]: return self._GetContainer()

    def AsImmutable(self) -> IEquatableTuple[T]: return self.__func()
    def AsReadOnly(self) -> IEquatableTuple[T]: return self
@final
class _ReversedHashableTuple[T: HashableProtocol](_Reversed[T, IHashableTuple[T]], SequenceAbstract[T], IHashableTuple[T], IGenericConstraintImplementation[IHashableTuple[T]]):
    def __init__(self, items: IHashableTuple[T]) -> None: super().__init__(items)
    
    def _SliceAt(self, key: slice) -> IHashableTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        return self.ToSlicedAt(key)
    
    def Equals(self, item: object) -> bool: return self._GetContainer().Equals(item)
    def Hash(self) -> int: return self._GetContainer().Hash()

    def AsReversed(self) -> IHashableTuple[T]: return self._GetContainer()

    def AsReadOnly(self) -> IHashableTuple[T]: return self
@final
class _ReversedEquatableTupleUpdater[T: EquatableProtocol](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, array: IEquatableTuple[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IEquatableTuple[T] = array
    
    def _GetValue(self) -> IEquatableTuple[T]: return _ReversedEquatableTuple[T](self.__array)
@final
class _ReversedHashableTupleUpdater[T: HashableProtocol](ValueFunctionUpdater[IHashableTuple[T]]):
    def __init__(self, array: IHashableTuple[T], updater: Method[IFunction[IHashableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IHashableTuple[T] = array
    
    def _GetValue(self) -> IHashableTuple[T]: return _ReversedHashableTuple[T](self.__array)

class ICollectionRegistries(ICollectionRegistry[IObjectMonitor]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitors(self) -> ICollectionMonitors:
        ...

    @abstractmethod
    def GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry:
        ...
    
    @abstractmethod
    def GetRevocableViewRegistry(self) -> IRevocableViewRegistry:
        ...

@final
class _Monitors(Abstract, ICollectionMonitors):
    def __init__(self, registries: ICollectionRegistries) -> None:
        super().__init__()

        self.__registries: ICollectionRegistries = registries

    def RegisterMonitor(self, item: IObjectMonitor) -> IRemovable: return self.__registries.RegisterMonitor(item)
    def RegisterObject(self, item: IObjectMonitor) -> None: self.RegisterMonitor(item)

    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor: return self.__registries.GetEnumeratorRegistry().AsMonitor()
    
    def GetRevocableViewMonitor(self) -> IRevocableViewMonitor: return self.__registries.GetRevocableViewRegistry().AsMonitor()
class CollectionRegistries(CollectionRegistry[IObjectMonitor], ICollectionRegistries):
    def __init__(self) -> None:
        def createRegistry[U: IObjectMonitor](registry: U) -> U:
            self.RegisterObject(registry)

            return registry
        
        super().__init__()

        self.__monitors: ICollectionMonitors = _Monitors(self)

        self.__registry: IResumableEnumeratorRegistry = createRegistry(ResumableEnumeratorRegistry())
        self.__view: IRevocableViewRegistry = createRegistry(RevocableViewRegistry())

    @final
    def AsMonitors(self) -> ICollectionMonitors: return self.__monitors

    @final
    def GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry: return self.__registry
    
    @final
    def GetRevocableViewRegistry(self) -> IRevocableViewRegistry: return self.__view

class ICollectionRegistryProviderBase[TItem, TMonitor](IGenericConstraint[TMonitor, ICollectionViewMonitor[TItem]]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetRegistries(self) -> ICollectionRegistries:
        ...
    @abstractmethod
    def GetMonitor(self) -> TMonitor:
        ...

class ICollectionRegistryProvider[T](ICollectionRegistryProviderBase[T, ICollectionViewMonitor[T]], IGenericConstraintImplementation[ICollectionViewMonitor[T]]):
    def __init__(self) -> None: super().__init__()

class IEquatableCollectionRegistryProvider[T](ICollectionRegistryProviderBase[T, IEquatableCollectionViewMonitor[T]], IGenericConstraintImplementation[IEquatableCollectionViewMonitor[T]]):
    def __init__(self) -> None: super().__init__()
class IHashableCollectionRegistryProvider[T](ICollectionRegistryProviderBase[T, IHashableCollectionViewMonitor[T]], IGenericConstraintImplementation[IHashableCollectionViewMonitor[T]]):
    def __init__(self) -> None: super().__init__()

class CollectionRegistryProviderAbstract[TItem, TMonitor](Abstract, ICollectionRegistryProviderBase[TItem, TMonitor]):
    def __init__(self, monitor: TMonitor) -> None:
        super().__init__()

        self.__registries: ICollectionRegistries = CollectionRegistries()
        self.__monitor: TMonitor = monitor

    @final
    def GetRegistries(self) -> ICollectionRegistries: return self.__registries
    @final
    def GetMonitor(self) -> TMonitor: return self.__monitor

class CollectionRegistryProviderBase[T](CollectionRegistryProviderAbstract[T, ICollectionViewMonitor[T]], ICollectionRegistryProvider[T]):
    def __init__(self, monitor: ICollectionViewMonitor[T]) -> None: super().__init__(monitor)
class CollectionRegistryProvider[T](CollectionRegistryProviderBase[T]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(CollectionViewMonitor[T](items))

class EquatableCollectionRegistryProviderBase[T](CollectionRegistryProviderAbstract[T, IEquatableCollectionViewMonitor[T]], IEquatableCollectionRegistryProvider[T]):
    def __init__(self, monitor: IEquatableCollectionViewMonitor[T]) -> None: super().__init__(monitor)
class EquatableCollectionRegistryProvider[T](EquatableCollectionRegistryProviderBase[T]):
    def __init__(self, items: IEquatableTuple[T]) -> None: super().__init__(EquatableCollectionViewMonitor[T](items))

class HashableCollectionRegistryProviderBase[T](CollectionRegistryProviderAbstract[T, IHashableCollectionViewMonitor[T]], IHashableCollectionRegistryProvider[T]):
    def __init__(self, monitor: IHashableCollectionViewMonitor[T]) -> None: super().__init__(monitor)

class IGenericManagedCollection[TItem, TRegistryProvider, TMonitor](IManagedCollection[TItem]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _AsRegistries(self, registryProvider: TRegistryProvider) -> ICollectionRegistries:
        ...
    
    @abstractmethod
    def _AsCollectionViewMonitor(self, registryProvider: TRegistryProvider) -> TMonitor:
        ...
    @abstractmethod
    def _AsMonitor(self, monitor: TMonitor) -> ICollectionViewMonitor[TItem]:
        ...

class GenericManagedCollectionBase[TItem, TRegistryProvider, TMonitor](ITuple[TItem], IGenericManagedCollection[TItem, TRegistryProvider, TMonitor]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _CreateRegistryProvider(self) -> TRegistryProvider:
        ...
class GenericManagedCollection[TItem, TRegistryProvider, TMonitor](Abstract, GenericManagedCollectionBase[TItem, TRegistryProvider, TMonitor]):
    def __init__(self) -> None: super().__init__()

class IDefaultGenericManagedCollectionBase[T](IGenericManagedCollection[T, ICollectionRegistryProvider[T], ICollectionViewMonitor[T]]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsRegistries(self, registryProvider: ICollectionRegistryProvider[T]) -> ICollectionRegistries: return registryProvider.GetRegistries()
    
    @final
    def _AsCollectionViewMonitor(self, registryProvider: ICollectionRegistryProvider[T]) -> ICollectionViewMonitor[T]: return registryProvider.GetMonitor()
    @final
    def _AsMonitor(self, monitor: ICollectionViewMonitor[T]) -> ICollectionViewMonitor[T]: return monitor
class IDefaultGenericManagedCollection[T](GenericManagedCollectionBase[T, ICollectionRegistryProvider[T], ICollectionViewMonitor[T]], IDefaultGenericManagedCollectionBase[T]):
    def __init__(self) -> None: super().__init__()

class DefaultGenericManagedCollection[T](IDefaultGenericManagedCollection[T], GenericManagedCollectionBase[T, ICollectionRegistryProvider[T], ICollectionViewMonitor[T]]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateRegistryProvider(self) -> ICollectionRegistryProvider[T]: return CollectionRegistryProvider[T](self)

class ManagedCollectionBase[TItem, TRegistryProvider, TMonitor](GenericManagedCollection[TItem, TRegistryProvider, TMonitor]):
    def __init__(self) -> None:
        super().__init__()

        self.__registryProvider: TRegistryProvider = self._CreateRegistryProvider()

    @final
    def _GetCollectionRegistries(self) -> ICollectionRegistries: return self._AsRegistries(self.__registryProvider)
    
    @final
    def _GetInnerCollectionViewMonitor(self) -> TMonitor: return self._AsCollectionViewMonitor(self.__registryProvider)
    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TItem]: return self._AsMonitor(self._GetInnerCollectionViewMonitor())
class ManagedCollection[T](ManagedCollectionBase[T, ICollectionRegistryProvider[T], ICollectionViewMonitor[T]], DefaultGenericManagedCollection[T]):
    def __init__(self) -> None: super().__init__()

class _TupleCollectionBase[T](TupleAbstract[T], ITupleBase[T]):
    def __init__(self) -> None: super().__init__()
class _TupleCollection[TItem, TRegistryProvider, TMonitor](ManagedCollectionBase[TItem, TRegistryProvider, TMonitor], _TupleCollectionBase[TItem]):
    def __init__(self) -> None: super().__init__()

class TupleCollectionBase[T](_TupleCollectionBase[T]):
    def __init__(self) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[ITuple[T]] = _ReversedTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> ITuple[T]: return self.__reversed.GetValue()

    @final
    def AsImmutable(self) -> ITuple[T]: return self._GetCollectionViewMonitor().GetImmutableView()
class EquatableTupleCollectionBase[T: EquatableProtocol](_TupleCollectionBase[T], IEquatableTuple[T], INotHashableValue):
    def __init__(self) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IEquatableTuple[T]] = _ReversedEquatableTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> IEquatableTuple[T]: return self.__reversed.GetValue()

    @final
    def AsReadOnly(self) -> IEquatableTuple[T]: return self
class HashableTupleCollectionBase[T: HashableProtocol](TupleAbstract[T], IHashableTuple[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IHashableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IHashableTuple[T]] = _ReversedHashableTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> IHashableTuple[T]: return self.__reversed.GetValue()

    @final
    def AsReadOnly(self) -> IHashableTuple[T]: return self

class TupleCollection[T](_TupleCollection[T, ICollectionRegistryProvider[T], ICollectionViewMonitor[T]], DefaultGenericManagedCollection[T]):
    def __init__(self) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[ITuple[T]] = _ReversedTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> ITuple[T]: return self.__reversed.GetValue()
class Tuple[T](TupleCollection[T], TupleBase[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def AsImmutable(self) -> ITuple[T]: return self._GetCollectionViewMonitor().GetImmutableView()
    @final
    def AsReadOnly(self) -> ITuple[T]: return self

class EquatableTupleCollection[T: EquatableProtocol](_TupleCollection[T, IEquatableCollectionRegistryProvider[T], IEquatableCollectionViewMonitor[T]], GenericManagedCollectionBase[T, IEquatableCollectionRegistryProvider[T], IEquatableCollectionViewMonitor[T]], IEquatableTuple[T], INotHashableValue):
    def __init__(self) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IEquatableTuple[T]] = _ReversedEquatableTupleUpdater[T](self, update) # type: ignore[no-redef]

    @final
    def _AsRegistries(self, registryProvider: IEquatableCollectionRegistryProvider[T]) -> ICollectionRegistries: return registryProvider.GetRegistries()
    
    @final
    def _AsCollectionViewMonitor(self, registryProvider: IEquatableCollectionRegistryProvider[T]) -> IEquatableCollectionViewMonitor[T]: return registryProvider.GetMonitor()
    @final
    def _AsMonitor(self, monitor: ICollectionViewMonitor[T]) -> ICollectionViewMonitor[T]: return monitor

    @final
    def _CreateRegistryProvider(self) -> IEquatableCollectionRegistryProvider[T]: return EquatableCollectionRegistryProvider[T](self)
    
    @final
    def AsReversed(self) -> IEquatableTuple[T]: return self.__reversed.GetValue()

    @final
    def AsReadOnly(self) -> IEquatableTuple[T]: return self
class EquatableTuple[T: EquatableProtocol](EquatableTupleCollection[T], TupleBase[T], IEquatableTuple[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def AsImmutable(self) -> IEquatableTuple[T]: return self._GetInnerCollectionViewMonitor().GetImmutableView()

class HashableTupleCollection[T: HashableProtocol](_TupleCollection[T, ICollectionRegistryProvider[T], ICollectionViewMonitor[T]], IHashableTuple[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IHashableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IHashableTuple[T]] = _ReversedHashableTupleUpdater[T](self, update) # type: ignore[no-redef]

    @final
    def _AsRegistries(self, registryProvider: ICollectionRegistryProvider[T]) -> ICollectionRegistries: return registryProvider.GetRegistries()
    
    @final
    def _AsCollectionViewMonitor(self, registryProvider: ICollectionRegistryProvider[T]) -> ICollectionViewMonitor[T]: return registryProvider.GetMonitor()
    @final
    def _AsMonitor(self, monitor: ICollectionViewMonitor[T]) -> ICollectionViewMonitor[T]: return monitor

    @final
    def _CreateRegistryProvider(self) -> ICollectionRegistryProvider[T]: return CollectionRegistryProvider[T](self)
    
    @final
    def AsReversed(self) -> IHashableTuple[T]: return self.__reversed.GetValue()

    @final
    def AsReadOnly(self) -> IHashableTuple[T]: return self
class HashableTuple[T: HashableProtocol](HashableTupleCollection[T], TupleBase[T], IHashableTuple[T]):
    def __init__(self) -> None: super().__init__()

@final
class _ReadOnlyReversedArrayUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: ITuple[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ITuple[T] = array
    
    def _GetValue(self) -> ITuple[T]: return _ReadOnlyTuple[T](self.__array)
@final
class _ReadOnlyReversedSortedArrayUpdater[T: SupportsEqualityAndRichComparison](ValueFunctionUpdater[ISortedTuple[T]]):
    def __init__(self, array: ISortedList[T], updater: Method[IFunction[ISortedTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ISortedList[T] = array
    
    def _GetValue(self) -> ISortedTuple[T]: return _ReadOnlySortedTuple[T](self.__array)

class ReversedArrayAbstract[TItem, TCollectionIn, TCollectionOut](_ReversedBase[TItem, TCollectionIn, TCollectionOut], _IReversed[TItem]):
    def __init__(self, items: TCollectionIn) -> None:
        super().__init__(items)

        self.__monitor: ICollectionViewMonitor[TItem] = CollectionViewMonitor[TItem](self)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TItem]: return self.__monitor
class ReversedArrayBase[TItem, TCollectionIn, TCollectionOut](ReversedArrayAbstract[TItem, TCollectionIn, TCollectionOut], IArray[TItem], GenericSpecializedConstraint[TCollectionIn, ITuple[TItem], IArray[TItem]]):
    def __init__(self, items: TCollectionIn) -> None:
        def update(func: IFunction[ITuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__(items)
        
        self.__readOnly: IFunction[ITuple[TItem]] = _ReadOnlyReversedArrayUpdater[TItem](self, update) # type: ignore[no-redef]
    
    @final
    def TrySetAt(self, key: int, value: TItem) -> bool: return self._GetSpecializedContainer().TrySetAt(self.ReverseIndex(key), value)
    
    @final
    def _Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(self.ReverseIndex(x), self.ReverseIndex(y))
    # Delegated for the same reason as the reversal: the exchange goes to the source as
    # one operation, with its indices transposed, instead of two positional writes that
    # a constrained source may refuse one at a time.
    @final
    def _Swap(self, x: int, y: int) -> None: self._GetSpecializedContainer().Swap(self.ReverseIndex(x), self.ReverseIndex(y))
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]: return self.__readOnly.GetValue()
class ReversedArray[TItem, TCollection](ReversedArrayBase[TItem, TCollection, TCollection]):
    def __init__(self, items: TCollection) -> None: super().__init__(items)

class IArrayAbstract[TItem, TCollection](ITuple[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetReversedUpdater(self, func: Method[IFunction[TCollection]]) -> IFunction[TCollection]:
        ...
class ArrayAbstractBase[TItem, TCollection](TupleAbstractBase[TItem], GetterBase[int, TItem], IArrayAbstract[TItem, TCollection]):
    def __init__(self) -> None: super().__init__()

class ArrayListBase[TItem, TCollection](ArrayAbstractBase[TItem, TCollection], KeyableBase[int, TItem], TupleAbstract[TItem], IArray[TItem], ITupleBase[TItem]):
    def __init__(self) -> None: super().__init__()
class ArrayAbstract[TItem, TCollection](ArrayListBase[TItem, TCollection], IManagedCollection[TItem]):
    def __init__(self) -> None: super().__init__()

class _ArrayCollectionAbstractBase[TItem, TCollection](ArrayAbstractBase[TItem, TCollection], ITupleBase[TItem]):
    def __init__(self) -> None: super().__init__()

class _ArrayListAbstract[TItem, TCollection](_ArrayCollectionAbstractBase[TItem, TCollection]):
    def __init__(self) -> None:
        def updateReversed(func: IFunction[TCollection]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[TCollection] = self._GetReversedUpdater(updateReversed) # type: ignore[no-redef]
    
    @final
    def _AsReversed(self) -> TCollection:
        return self.__reversed.GetValue()
class _ArrayListBase[TItem, TCollection](_ArrayListAbstract[TItem, TCollection]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[ITuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[ITuple[TItem]] = _ReadOnlyReversedArrayUpdater[TItem](self, updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]: return self.__readOnly.GetValue()

class _ArrayCollectionAbstract[TItem, TCollection](ManagedCollection[TItem], _ArrayCollectionAbstractBase[TItem, TCollection], IManagedCollection[TItem]):
    def __init__(self) -> None:
        def updateReversed(func: IFunction[TCollection]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[TCollection] = self._GetReversedUpdater(updateReversed) # type: ignore[no-redef]
    
    @final
    def _AsReversed(self) -> TCollection:
        return self.__reversed.GetValue()
class _ArrayCollectionBase[TItem, TCollection](_ArrayCollectionAbstract[TItem, TCollection]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[ITuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[ITuple[TItem]] = _ReadOnlyReversedArrayUpdater[TItem](self, updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]: return self.__readOnly.GetValue()

class ArrayCollectionAbstract[TItem, TCollection](_ArrayListBase[TItem, TCollection], ArrayListBase[TItem, TCollection]):
    def __init__(self) -> None: super().__init__()
class ArrayCollectionBase[TItem, TCollection](_ArrayCollectionBase[TItem, TCollection], ArrayAbstract[TItem, TCollection]):
    def __init__(self) -> None: super().__init__()

class _ArrayAbstract[TItem, TCollection](_ArrayCollectionAbstract[TItem, TCollection], _TupleBase[TItem]):
    def __init__(self) -> None: super().__init__()
class _ArrayBase[TItem, TCollection](_ArrayCollectionBase[TItem, TCollection], _TupleBase[TItem]):
    def __init__(self) -> None: super().__init__()
class ArrayBase[TItem, TCollection](_ArrayBase[TItem, TCollection], ArrayCollectionBase[TItem, TCollection], TupleBase[TItem]):
    def __init__(self) -> None: super().__init__()

    @final
    def AsImmutable(self) -> ITuple[TItem]: return self._GetCollectionViewMonitor().GetImmutableView()

@final
class _ReversedArray[T](ReversedArray[T, IArray[T]], SequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T]) -> None: super().__init__(items)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def AsReversed(self) -> IArray[T]: return self._GetSpecializedContainer()
    
    @final
    def _SliceAt(self, key: slice) -> IArray[T]:
        return self._GetSpecializedContainer().SliceAt(key)
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._AsSpecialized(self.ToSlicedAt(key))
@final
class _ReversedArrayUpdater[T](ValueFunctionUpdater[IArray[T]]):
    def __init__(self, array: IArray[T], updater: Method[IFunction[IArray[T]]]) -> None:
        super().__init__(updater)

        self.__array: IArray[T] = array
    
    def _GetValue(self) -> IArray[T]: return _ReversedArray[T](self.__array)

class ArrayList[T](_Array[T], ArrayCollectionAbstract[T, IArray[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]: return _ReversedArrayUpdater[T](self, func)
    
    @final
    def AsReversed(self) -> IArray[T]: return self._AsReversed()
class ArrayCollection[T](_Array[T], ArrayCollectionBase[T, IArray[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]: return _ReversedArrayUpdater[T](self, func)
    
    @final
    def AsReversed(self) -> IArray[T]: return self._AsReversed()
class Array[T](ArrayBase[T, IArray[T]], ArrayCollection[T]):
    def __init__(self) -> None: super().__init__()

class _IIndexableCollectionAbstract[T](IIndexableCollectionBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetContainerAsList(self) -> IListBase[T]:
        ...
class _IReversedCollectionAbstract[T](_IIndexableCollectionAbstract[T], ICollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainerAsList().TryRemoveAt(self.ReverseIndex(index))
    
    @final
    def Clear(self) -> None: self._GetContainerAsList().Clear()

class ReversedCollectionAbstract[TItem, TList](ReversedArrayAbstract[TItem, TList, TList], _IReversedCollectionAbstract[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IListBase[TItem]:
        ...

    def AsReversed(self) -> IListBase[TItem]: return self._GetContainerAsList()
class ReversedCollectionBase[TItem, TListIn, TListOut](ReversedArrayBase[TItem, TListIn, TListOut], _IReversedCollectionAbstract[TItem]):
    def __init__(self, items: TListIn) -> None: super().__init__(items)

    @abstractmethod
    def _GetContainerAsList(self) -> IList[TItem]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[TItem]:
        ...

    def AsReversed(self) -> IList[TItem]: return self._GetContainerAsList()
class ReversedCollection[TItem, TList](ReversedArray[TItem, TList], _IReversedCollectionAbstract[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)

@final
class _FixedSizeArray[T](FixedSizeCollection[T], IArray[T], ISwappable[int, T]):
    def __init__(self, items: IList[T]) -> None:
        def update(func: IFunction[IArray[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[IArray[T]] = _ReversedArrayUpdater[T](self, update) # type: ignore[no-redef]
    
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetContainer().GetSourceMutability()
    
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryCreateEnumerator(self._GetContainer().TryGetEnumerator())
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return TryCreateResumableEnumerator(self._GetContainer().TryGetResumableEnumerator())
    
    def AsReversed(self) -> IArray[T]: return self.__reversed.GetValue()

    def AsImmutable(self) -> ITuple[T]: return self._GetContainer().AsImmutable()
@final
class _FixedSizeArrayUpdater[T](ValueFunctionUpdater[IArray[T]]):
    def __init__(self, items: IList[T], updater: Method[IFunction[IArray[T]]]) -> None:
        super().__init__(updater)

        self.__items: IList[T] = items
    
    def _GetValue(self) -> IArray[T]: return _FixedSizeArray[T](self.__items)

class MutableList[T](MutableSequence[T], IList[T]):
    def __init__(self, ) -> None: super().__init__()

    @final
    def _GetFixedSizeUpdater(self, updater: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]:
        return _FixedSizeArrayUpdater[T](self, updater)

class ReversedListAbstract[TItem, TListIn, TListOut](ReversedCollectionBase[TItem, TListIn, TListOut], MutableList[TItem]):
    def __init__(self, items: TListIn) -> None:
        def update(func: IFunction[IArray[TItem]]) -> None: self.__fixedSize = func
        
        super().__init__(items)

        self.__fixedSize: IFunction[IArray[TItem]] = self._GetFixedSizeUpdater(update) # type: ignore[no-redef]
    
    @abstractmethod
    def _GetInnerContainerAsList(self, container: TListIn) -> IList[TItem]:
        ...

    @final
    def _GetContainerAsList(self) -> IList[TItem]:
        return self._GetInnerContainerAsList(self._GetContainer())
    
    # Reversing a reversed view is reversing its source, so this goes to the source whole
    # rather than through 2n positional writes. That also keeps it out of reach of a source
    # whose positional write is constrained -- an ordered set refuses a momentary duplicate,
    # which the inherited pairwise implementation produces at every step.
    @final
    def _Reverse(self) -> None: self._GetContainerAsList().AsMutableSequence().reverse()

    @final
    def AsFixedSize(self) -> IArray[TItem]: return self.__fixedSize.GetValue()
    @final
    def AsReversed(self) -> IList[TItem]: return self._GetContainerAsList()
    
    @final
    def Add(self, item: TItem) -> None:
        items: IList[TItem] = self._GetContainerAsList()

        if self.GetCount() > 0: items.Insert(0, item)
        else: items.Add(item)
    @final
    def AddRange(self, items: Iterable[TItem]) -> None:
        self._GetContainerAsList().InsertRange(0, Reverse(items))
    
    # ReverseIndexFromLast maps k to count - k, hence count at the reversed head and 0 at its tail, both of which the permissive source insertion accepts. No bound needs a special case, and staying on the Try* members keeps the refusal a returned value rather than an exception.
    @final
    def __TryInsert[T, U](self, index: int, value: T, default: U, inserter: Converter[IList[TItem], Callable[[int, T], U]]) -> U:
        return inserter(self._GetContainerAsList())(ReverseIndexFromLast(index, self.GetCount()), value) if self.ValidateIndex(index, True) else default

    @final
    def TryInsert(self, index: int, value: TItem) -> bool: return self.__TryInsert(index, value, False, lambda items: items.TryInsert)
    @final
    def TryInsertRange(self, index: int, items: Iterable[TItem]) -> bool|None: return self.__TryInsert(index, Reverse(items), None, lambda items: items.TryInsertRange)
    
    @final
    def _RemoveRange(self, index: int, count: int) -> None: self._GetContainerAsList().RemoveRange(self.ReverseRangeStartIndex(index, count), count)
    
    @final
    def insert(self, index: int, value: TItem) -> None: self.TryInsert(index, value)

    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None: self._GetContainerAsList().AsMutableSequence()[self.ReverseIndex(int(index)) if isinstance(index, SupportsIndex) else self.ReverseKey(index)] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None: del self._GetContainerAsList().AsMutableSequence()[self.ReverseIndex(index) if isinstance(index, int) else self.ReverseKey(index)]
class ReversedListBase[TItem, TList](ReversedListAbstract[TItem, TList, TList]):
    def __init__(self, items: TList) -> None: super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> IList[TItem]: return self._GetInnerContainerAsList(self.ToSlicedAt(key))

class ReversedSortedListAbstract[TItem: SupportsEqualityAndRichComparison, TList](ReversedCollectionAbstract[TItem, TList], Sequence[TItem], ISortedList[TItem]):
    def __init__(self, items: TList) -> None:
        def update(func: IFunction[ISortedTuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__(items)
        
        self.__readOnly: IFunction[ISortedTuple[TItem]] = _ReadOnlyReversedSortedArrayUpdater[TItem](self, update) # type: ignore[no-redef]
    
    @abstractmethod
    def _GetInnerContainerAsList(self, container: TList) -> ISortedList[TItem]:
        ...
    @abstractmethod
    def _GetSpecializedContainerAsList(self, container: TList) -> ISortedList[TItem]:
        ...

    @final
    def _GetContainerAsList(self) -> ISortedList[TItem]:
        return self._GetInnerContainerAsList(self._GetContainer())
    
    @final
    def AddLeft(self, item: TItem) -> None: self._GetContainerAsList().Add(item)
    @final
    def Add(self, item: TItem) -> None: self._GetContainerAsList().AddLeft(item)
    
    @final
    def _RemoveRange(self, index: int, count: int) -> None: self._GetContainerAsList().RemoveRange(self.ReverseRangeStartIndex(index, count), count)
    
    @final
    def SliceAt(self, key: slice) -> ISortedList[TItem]: return self._GetSpecializedContainerAsList(self.ToSlicedAt(key))

    @final
    def AsReversed(self) -> ISortedList[TItem]: return self._GetContainerAsList()
    
    @final
    def AsReadOnly(self) -> ISortedTuple[TItem]: return self.__readOnly.GetValue()

@final
class _ReversedList[T](ReversedListBase[T, IList[T]], MutableSequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T]) -> None: super().__init__(items)
    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    
    def _GetInnerContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    def _GetSpecializedContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    
    def _SliceAt(self, key: slice) -> IList[T]:
        return self._GetContainerAsList().SliceAt(key)
@final
class _ReversedListUpdater[T](ValueFunctionUpdater[IList[T]]):
    def __init__(self, array: IList[T], updater: Method[IFunction[IList[T]]]) -> None:
        super().__init__(updater)

        self.__array: IList[T] = array
    
    def _GetValue(self) -> IList[T]: return _ReversedList[T](self.__array)

@final
class _ReversedSortedList[T: SupportsEqualityAndRichComparison](ReversedSortedListAbstract[T, ISortedList[T]], SequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], ISortedList[T]]):
    def __init__(self, items: ISortedList[T]) -> None: super().__init__(items)
    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    
    def TryBisect(self, item: T, right: bool = False) -> DualValueBool[int]: return self._GetContainer().TryBisect(item, right)
    def TryBisectWithKey[_T: SupportsEqualityAndRichComparison](self, item: _T, converter: Converter[T, _T], right: bool = False) -> DualValueBool[int]: return self._GetContainer().TryBisectWithKey(item, converter, right)
    
    def _GetInnerContainerAsList(self, container: ISortedList[T]) -> ISortedList[T]:
        return container
    def _GetSpecializedContainerAsList(self, container: ISortedList[T]) -> ISortedList[T]:
        return container
    
    def _SliceAt(self, key: slice) -> ISortedList[T]:
        return self._GetContainerAsList().SliceAt(key)
@final
class _ReversedSortedListUpdater[T: SupportsEqualityAndRichComparison](ValueFunctionUpdater[ISortedList[T]]):
    def __init__(self, array: ISortedList[T], updater: Method[IFunction[ISortedList[T]]]) -> None:
        super().__init__(updater)

        self.__array: ISortedList[T] = array
    
    def _GetValue(self) -> ISortedList[T]: return _ReversedSortedList[T](self.__array)

class CollectionAbstract[T](IArrayAbstract[T, IList[T]], IList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[IList[T]]]) -> IFunction[IList[T]]: return _ReversedListUpdater[T](self, func)

class _CollectionBase[T](_List[T], CollectionAbstract[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IArray[T]]) -> None: self.__fixedSize = func
        
        super().__init__()

        self.__fixedSize: IFunction[IArray[T]] = _FixedSizeArrayUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsFixedSize(self) -> IArray[T]: return self.__fixedSize.GetValue()
class CollectionBase[T](_CollectionBase[T], ArrayCollectionAbstract[T, IList[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def AsReversed(self) -> IList[T]: return self._AsReversed()
class Collection[T](_CollectionBase[T], ArrayCollectionBase[T, IList[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def AsReversed(self) -> IList[T]: return self._AsReversed()

class SortedCollection[T: SupportsEqualityAndRichComparison](_SortedList[T], _ArrayCollectionAbstract[T, ISortedList[T]], ISortedList[T]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[ISortedTuple[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[ISortedTuple[T]] = _ReadOnlyReversedSortedArrayUpdater[T](self, updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsImmutable(self) -> ITuple[T]: return self._GetCollectionViewMonitor().GetImmutableView()
    @final
    def AsReadOnly(self) -> ISortedTuple[T]: return self.__readOnly.GetValue()
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[ISortedList[T]]]) -> IFunction[ISortedList[T]]: return _ReversedSortedListUpdater[T](self, func)
    
    @final
    def AsReversed(self) -> ISortedList[T]: return self._AsReversed()

class List[T](ArrayBase[T, IList[T]], Collection[T]):
    def __init__(self) -> None: super().__init__()
class SortedList[T: SupportsEqualityAndRichComparison](_ArrayAbstract[T, ISortedList[T]], SortedCollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    @final
    def TryGetSourceMutability(self) -> None: return None