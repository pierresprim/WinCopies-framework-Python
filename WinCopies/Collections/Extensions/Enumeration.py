from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Enumeration import IInvalidatableEnumeratorBase, IEnumerator, IInvalidatableEnumerator, IncrementalEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator, IInvalidatableResumableEnumerator
from WinCopies.Collections.Enumeration.Resumable.Indexable import ResumableIncrementalEnumerator
from WinCopies.Collections.Extensions import ITuple, IEnumeratorMonitor, IResumableEnumeratorMonitor
from WinCopies.Collections.Generation.Registry import IObjectRegistry
from WinCopies.Collections.Generation.Registry.Core import InvalidatableObjectRegistry
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class TupleEnumeratorBase[TItem, TList](IncrementalEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__list
    
    @final
    def _GetMaxValue(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetCurrent(self) -> TItem: return self._GetInnerContainer().GetAt(self._GetValue())
class TupleEnumerator[T](TupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

class ResumableTupleEnumeratorBase[TItem, TList](ResumableIncrementalEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__list
    
    @final
    def _GetMaxValue(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetCurrent(self) -> TItem: return self._GetInnerContainer().GetAt(self._GetValue())
class ResumableTupleEnumerator[T](ResumableTupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

class IEnumeratorRegistry(IObjectRegistry[IInvalidatableEnumeratorBase], IEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()

    @final
    def RegisterEnumerator[T](self, enumerator: IEnumerator[T]) -> IInvalidatableEnumerator[T]:
        self.RegisterObject((enumerator := enumerator.ToInvalidatable()))
        
        return enumerator
    
    @abstractmethod
    def AsMonitor(self) -> IEnumeratorMonitor:
        ...
class IResumableEnumeratorRegistry(IEnumeratorRegistry, IResumableEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()

    @final
    def RegisterResumableEnumerator[T](self, enumerator: IResumableEnumerator[T]) -> IInvalidatableResumableEnumerator[T]:
        self.RegisterObject((enumerator := enumerator.ToInvalidatable()))
        
        return enumerator
    
    @abstractmethod
    def AsMonitor(self) -> IResumableEnumeratorMonitor:
        ...

class EnumeratorMonitor[T](Abstract, IEnumeratorMonitor, GenericConstraint[T, IEnumeratorRegistry]):
    def __init__(self, registry: T) -> None:
        super().__init__()

        self.__registry: T = registry
    
    @final
    def _GetContainer(self) -> T: return self.__registry
    
    @final
    def CreateEnumerator[U](self, items: ITuple[U]) -> IEnumerator[U]: return self._GetInnerContainer().CreateEnumerator(items)
class EnumeratorMonitorUpdater[TMonitor, TRegistry](ValueFunctionUpdater[TMonitor]):
    def __init__(self, registry: TRegistry, updater: Method[IFunction[TMonitor]]) -> None:
        super().__init__(updater)

        self.__registry: TRegistry = registry
    
    @final
    def _GetRegistry(self) -> TRegistry:
        return self.__registry

@final
class _EnumeratorMonitor(EnumeratorMonitor[IEnumeratorRegistry]):
    def __init__(self, registry: IEnumeratorRegistry) -> None: super().__init__(registry)
    
    def _AsContainer(self, container: IEnumeratorRegistry) -> IEnumeratorRegistry: return container
@final
class _EnumeratorMonitorUpdater(EnumeratorMonitorUpdater[IEnumeratorMonitor, IEnumeratorRegistry]):
    def __init__(self, registry: IEnumeratorRegistry, updater: Method[IFunction[IEnumeratorMonitor]]) -> None: super().__init__(registry, updater)
    
    def _GetValue(self) -> IEnumeratorMonitor: return _EnumeratorMonitor(self._GetRegistry())

@final
class _ResumableEnumeratorMonitor(EnumeratorMonitor[IResumableEnumeratorRegistry], IResumableEnumeratorMonitor):
    def __init__(self, registry: IResumableEnumeratorRegistry) -> None: super().__init__(registry)
    
    def _AsContainer(self, container: IResumableEnumeratorRegistry) -> IResumableEnumeratorRegistry: return container
    
    def CreateResumableEnumerator[U](self, items: ITuple[U]) -> IResumableEnumerator[U]:
        return self._GetContainer().CreateResumableEnumerator(items)
@final
class _ResumableEnumeratorMonitorUpdater(EnumeratorMonitorUpdater[IResumableEnumeratorMonitor, IResumableEnumeratorRegistry]):
    def __init__(self, registry: IResumableEnumeratorRegistry, updater: Method[IFunction[IResumableEnumeratorMonitor]]) -> None: super().__init__(registry, updater)
    
    def _GetValue(self) -> IResumableEnumeratorMonitor: return _ResumableEnumeratorMonitor(self._GetRegistry())

class EnumeratorRegistryBase[T: IEnumeratorMonitor](Abstract, IEnumeratorRegistry):
    def __init__(self) -> None:
        def update(func: IFunction[T]) -> None: self.__monitor = func
        
        super().__init__()

        self.__registry: IObjectRegistry[IInvalidatableEnumeratorBase] = InvalidatableObjectRegistry[IInvalidatableEnumeratorBase]()
        self.__monitor: IFunction[T] = self._CreateUpdater(update) # type: ignore[no-redef]

    @final
    def _GetRegistry(self) -> IObjectRegistry[IInvalidatableEnumeratorBase]:
        return self.__registry
    
    @abstractmethod
    def _CreateUpdater(self, updater: Method[IFunction[T]]) -> EnumeratorMonitorUpdater[T, IEnumeratorRegistry]:
        ...

    @final
    def RegisterObject(self, item: IInvalidatableEnumeratorBase) -> None: self._GetRegistry().RegisterObject(item)

    @final
    def InvalidateObjects(self) -> None: self._GetRegistry().InvalidateObjects()
    
    @final
    def CreateEnumerator[U](self, items: ITuple[U]) -> IInvalidatableEnumerator[U]:
        return self.RegisterEnumerator(TupleEnumerator[U](items))
    
    @final
    def _AsMonitor(self) -> T:
        return self.__monitor.GetValue()

class EnumeratorRegistry(EnumeratorRegistryBase[IEnumeratorMonitor]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateUpdater(self, updater: Method[IFunction[IEnumeratorMonitor]]) -> EnumeratorMonitorUpdater[IEnumeratorMonitor, IEnumeratorRegistry]:
        return _EnumeratorMonitorUpdater(self, updater)
    
    @final
    def AsMonitor(self) -> IEnumeratorMonitor:
        return self._AsMonitor()
class ResumableEnumeratorRegistry(EnumeratorRegistryBase[IResumableEnumeratorMonitor], IResumableEnumeratorRegistry):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateUpdater(self, updater: Method[IFunction[IResumableEnumeratorMonitor]]) -> EnumeratorMonitorUpdater[IResumableEnumeratorMonitor, IResumableEnumeratorRegistry]:
        return _ResumableEnumeratorMonitorUpdater(self, updater)
    
    @final
    def CreateResumableEnumerator[U](self, items: ITuple[U]) -> IInvalidatableResumableEnumerator[U]:
        return self.RegisterResumableEnumerator(ResumableTupleEnumerator[U](items))
    
    @final
    def AsMonitor(self) -> IResumableEnumeratorMonitor:
        return self._AsMonitor()