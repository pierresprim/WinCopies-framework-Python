from typing import final

from WinCopies.Collections.Extensions import CollectionViewMonitorBase, ITuple
from WinCopies.Typing.Delegate import Method
from WinCopies.Typing.Discard import DiscardReason

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
    def _CreateView(self, items: ITuple[TOut], onDisposed: Method[DiscardReason]) -> ITuple[TOut]:
        return self._GetSource().GetCollectionMonitors().GetRevocableViewMonitor().CreateRevocableView(items, onDisposed)