from typing import final

from WinCopies.Collections.Extensions import (IEquatableCollectionViewMonitor, IHashableCollectionViewMonitor,
                                              IGenericCollectionViewMonitorImplementation,
                                              ITuple, IEquatableTuple, IHashableTuple,
                                              CollectionViewMonitorAbstract as _CollectionViewMonitorAbstract)
from WinCopies.Typing.Delegate import Method
from WinCopies.Typing.Discard import DiscardReason

class CollectionViewMonitorAbstract[TIn, TOut, TCollection](_CollectionViewMonitorAbstract[TOut, TCollection]):
    def __init__(self, source: ITuple[TIn], items: TCollection) -> None:
        super().__init__(items)

        self.__source: ITuple[TIn] = source

    @final
    def _GetSource(self) -> ITuple[TIn]:
        return self.__source
class CollectionViewMonitorBase[TIn, TOut](CollectionViewMonitorAbstract[TIn, TOut, ITuple[TOut]], IGenericCollectionViewMonitorImplementation[ITuple[TOut]]):
    def __init__(self, source: ITuple[TIn], items: ITuple[TOut]) -> None: super().__init__(source, items)

    @final
    def GetImmutableView(self) -> ITuple[TOut]: return self._GetImmutableView()
class CollectionViewMonitor[TIn, TOut](CollectionViewMonitorBase[TIn, TOut]):
    def __init__(self, source: ITuple[TIn], items: ITuple[TOut]) -> None: super().__init__(source, items)

    @final
    def _CreateView(self, items: ITuple[TOut], onDisposed: Method[DiscardReason]) -> ITuple[TOut]:
        return self._GetSource().GetCollectionMonitors().GetRevocableViewMonitor().CreateRevocableView(items, onDisposed)

class EquatableCollectionViewMonitorBase[TIn, TOut](CollectionViewMonitorAbstract[TIn, TOut, IEquatableTuple[TOut]], IEquatableCollectionViewMonitor[TOut], IGenericCollectionViewMonitorImplementation[IEquatableTuple[TOut]]):
    def __init__(self, source: ITuple[TIn], items: IEquatableTuple[TOut]) -> None: super().__init__(source, items)

    @final
    def GetImmutableView(self) -> IEquatableTuple[TOut]: return self._GetImmutableView()
class EquatableCollectionViewMonitor[TIn, TOut](EquatableCollectionViewMonitorBase[TIn, TOut]):
    def __init__(self, source: ITuple[TIn], items: IEquatableTuple[TOut]) -> None: super().__init__(source, items)

    @final
    def _CreateView(self, items: IEquatableTuple[TOut], onDisposed: Method[DiscardReason]) -> IEquatableTuple[TOut]: return self._GetMonitor().CreateRevocableView(items, onDisposed)

class HashableCollectionViewMonitorBase[TIn, TOut](CollectionViewMonitorAbstract[TIn, TOut, IHashableTuple[TOut]], IHashableCollectionViewMonitor[TOut], IGenericCollectionViewMonitorImplementation[IHashableTuple[TOut]]):
    def __init__(self, source: ITuple[TIn], items: IHashableTuple[TOut]) -> None: super().__init__(source, items)

    @final
    def GetImmutableView(self) -> IHashableTuple[TOut]: return self._GetImmutableView()
class HashableCollectionViewMonitor[TIn, TOut](HashableCollectionViewMonitorBase[TIn, TOut]):
    def __init__(self, source: ITuple[TIn], items: IHashableTuple[TOut]) -> None: super().__init__(source, items)

    @final
    def _CreateView(self, items: IHashableTuple[TOut], onDisposed: Method[DiscardReason]) -> IHashableTuple[TOut]: return self._GetMonitor().CreateRevocableView(items, onDisposed)