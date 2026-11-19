from __future__ import annotations

from abc import abstractmethod
from typing import cast, final
from weakref import ref

from WinCopies import Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Iteration import Generate, Iterate
from WinCopies.Collections.Registry import IObjectMonitor, IObjectRegistrar, IObjectRegistry, ICollectionRegistry
from WinCopies.Collections.Registry.Kernel import IRegistry as _IRegistry, IWeakReferenceRegistry as _IWeakReferenceRegistry, IItemRegistry as _IItemRegistry, Registry as _Registry, WeakReferenceRegistry as _WeakReferenceRegistry, ItemRegistry as _ItemRegistry, CreateItemRegistry as _CreateItemRegistry
from WinCopies.Collections.Linked.Doubly import IReadOnlyList
from WinCopies.Collections.Linked.Node import ILinkedNode, IReadWriteLinkedNode
from WinCopies.Collections.Loop import DoForEachItem
from WinCopies.Delegates import NoAction, FuncNone, GetActionAsMethod
from WinCopies.Typing.Delegate import Action, Method, Converter, Function, NullableFunction
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Object import IWeakReference, IWeakReferenceRegister, IDisposableReferenceRegister, CreateDisposableReferenceRegister

def _DoForEachItem[T](items: Generator[T], method: Method[T], action: Action|None) -> None:
    DoForEachItem(items, method, True if action is None else GetActionAsMethod(action))

class IRegistry[TIn, TOut](_IRegistry[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def InvalidateObjects(self, action: Action|None = None) -> None:
        ...
class Registry[TIn, TItem, TOut](_Registry[TIn, TItem, TOut], IRegistry[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

class IWeakReferenceRegistry[T: IInvalidatable](_IWeakReferenceRegistry[T], IRegistry[IWeakReferenceRegister[T], T]):
    def __init__(self) -> None: super().__init__()
class IItemRegistry[T: IObjectMonitor](_IItemRegistry[T], IRegistry[T, T]):
    def __init__(self) -> None: super().__init__()

class IDefaultRegistry[TIn, TOut](IRegistry[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _HasItems(self) -> bool:
        ...
    @abstractmethod
    def _InvalidateObjects(self, action: Action|None = None) -> None:
        ...
    
    @final
    def InvalidateObjects(self, action: Action|None = None) -> None:
        if self._HasItems(): self._InvalidateObjects(action)
        elif action is not None: action()

class WeakReferenceRegistry[T: IInvalidatable](_WeakReferenceRegistry[T], IWeakReferenceRegistry[T], IDefaultRegistry[IWeakReferenceRegister[T], T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _HasItems(self) -> bool: return self._GetItems().HasItems()
    
    @final
    def _InvalidateObjects(self, action: Action|None = None) -> None: _DoForEachItem(Generate(self.TryRemoveFirst), lambda cookie: cookie.Invalidate(), action)
class ItemRegistry[T: IObjectMonitor](_ItemRegistry[T], IItemRegistry[T], IDefaultRegistry[T, T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _HasItems(self) -> bool: return self._GetItems().HasItems()

    @final
    def _InvalidateObjects(self, action: Action|None = None) -> None: _DoForEachItem(Iterate(self.TryGetFirstNode, lambda node: node.GetNext()), lambda node: node.GetValue().InvalidateObjects(), action)

def CreateWeakReferenceRegistry[T: IInvalidatable]() -> IWeakReferenceRegistry[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return WeakReferenceRegistry[T]()
def CreateItemRegistry[T: IObjectMonitor]() -> IItemRegistry[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return ItemRegistry[T]()

_minimumPurgeThreshold: int = 16

@final
class _Purger(Abstract):
    """Triggers the purge of a registry, so that the entries of dead objects do not pile up between two invalidations.

    The purge runs once the registrations since the last purge reach the number of entries that this purge left, and at least a fixed minimum. A purge that leaves n entries is thus followed by n registrations at least before the next one, which reads 2n entries at most, so that a registration costs at most two steps of purge on average.

    Args:
        purge: The purge of the registry, which returns the number of entries it left.
    """

    def __init__(self, purge: Function[int]) -> None:
        super().__init__()

        self.__purge: Function[int] = purge
        self.__count: int = 0
        self.__threshold: int = _minimumPurgeThreshold
    
    def Register(self) -> None:
        """Counts a registration, and purges the registry if the registrations since the last purge reach the threshold.
        """

        count: int = self.__count + 1

        if count < self.__threshold: self.__count = count
        
        else:
            self.__count = 0
            self.__threshold = max(self.__purge(), _minimumPurgeThreshold)
    
    def Reset(self) -> None:
        """Starts the count again, once the registry is emptied.
        """

        self.__count = 0
        self.__threshold = _minimumPurgeThreshold

class _PurgeableWeakReferenceRegistry[T: IInvalidatable](WeakReferenceRegistry[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def PushReference(self, item: IDisposableReferenceRegister[T]) -> INodeBase: return self._GetItems().AddLastNode(item.GetCookie())

    @final
    def Purge(self) -> int:
        """Removes the nodes whose object is dead.

        Returns:
            The number of nodes left.
        """

        count: int = 0
        node: IReadWriteLinkedNode[IWeakReference[T]]|None = self._GetItems().GetFirstNode()

        while node is not None:
            # The nodes of the list are all read-write, though the interface returns the next one as a read-only node.
            following: IReadWriteLinkedNode[IWeakReference[T]]|None = cast(IReadWriteLinkedNode[IWeakReference[T]]|None, node.GetNext())

            if node.GetValue().TryGetValue() is None: node.Remove()
            else: count += 1

            node = following
        
        return count

@final
class _Monitor(Abstract, IObjectMonitor):
    def __init__(self, monitor: IObjectMonitor) -> None:
        super().__init__()

        self.__monitor: IObjectMonitor = monitor

    def InvalidateObjects(self) -> None: self.__monitor.InvalidateObjects()
@final
class _Registrar[T](Abstract, IObjectRegistrar[T]):
    def __init__(self, registrar: IObjectRegistrar[T]) -> None:
        super().__init__()

        self.__registrar: IObjectRegistrar[T] = registrar

    def RegisterObject(self, item: T) -> None: self.__registrar.RegisterObject(item)

class ObjectRegistryBase[TIn, TOut: IInvalidatable](Abstract, IObjectRegistry[TIn]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: _PurgeableWeakReferenceRegistry[TOut] = _PurgeableWeakReferenceRegistry[TOut]()
        self.__purger: _Purger = _Purger(self._Purge)

        self.__push: Converter[TOut, INodeBase] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__monitor: IObjectMonitor = _Monitor(self)
        self.__registrar: IObjectRegistrar[TIn] = _Registrar(self)
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__items.AsReadOnly()
    
    @final
    def __Push(self, obj: TOut) -> INodeBase:
        self.__purger.Register()

        cookie: IDisposableReferenceRegister[TOut] = CreateDisposableReferenceRegister(obj)
        node: INodeBase = self._GetRemovable(obj, self.__items.PushReference(cookie))

        cookie.RegisterNode(node)

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INodeBase:
        def finalize() -> None:
            self.__push = self.__PushFirst
            self.__clear = NoAction

            self.__purger.Reset()
        
        self.__push = self.__Push
        self.__clear = lambda: self.__items.InvalidateObjects(finalize)

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INodeBase:
        return self.__push(self._Convert(item))
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> INodeBase:
        """Gets the node that _Push returns for a registered object, so that its removal removes the object from every structure of the registry.

        A registry that keeps an index alongside its list adds the object to it here, and returns a node that removes both entries.

        Args:
            obj: The registered object.
            node: The node of the object in the list of the registry.

        Returns:
            The node to return for the object.
        """

        return node
    
    def _Purge(self) -> int:
        """Removes the entries of the dead objects. A registry that keeps an index alongside its list removes their entries from it too.

        Returns:
            The number of entries left in the list of the registry.
        """

        return self.__items.Purge()
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...
    
    @final
    def RegisterObject(self, item: TIn) -> None: self._Push(item)
    
    def InvalidateObjects(self) -> None: self.__clear()

    @final
    def AsMonitor(self) -> IObjectMonitor: return self.__monitor
    @final
    def AsRegistrar(self) -> IObjectRegistrar[TIn]: return self.__registrar
class ObjectRegistry[T](ObjectRegistryBase[T, IInvalidatable]):
    def __init__(self) -> None: super().__init__()

class InvalidatableObjectRegistry[T: IInvalidatable](ObjectRegistryBase[T, T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: T) -> T: return item

@final
class _CollectionFactoryCookie(Abstract, IRemovable):
    def __init__(self, node: IRemovable) -> None:
        super().__init__()

        self.__node: IRemovable = node

    def Remove(self) -> None: self.__node.Remove()

@final
class _WeakMonitor[T: IObjectMonitor](Abstract, IRemovable):
    """Holds weakly, without a callback, a monitor registered by RegisterMonitor.

    The monitor is never detached from the registry by a finalizer, nor by its removal. Its removal only empties the reference, and the registry detaches the entry itself, as it does for a dead monitor, so that the list of the registry changes only while no monitor is being invalidated.

    Args:
        monitor: The monitor to hold.
    """

    def __init__(self, monitor: T) -> None:
        super().__init__()

        self.__tryGetMonitor: NullableFunction[T] = ref(monitor)
        self.__node: IRemovable|None = None
    
    def TryGetMonitor(self) -> T|None: return self.__tryGetMonitor()

    def SetNode(self, node: IRemovable) -> None: self.__node = node

    def Detach(self) -> None:
        node: IRemovable|None = self.__node

        if node is not None:
            self.__node = None

            node.Remove()
    
    def Remove(self) -> None: self.__tryGetMonitor = FuncNone

@final
class _WeakMonitors[T: IObjectMonitor](Abstract):
    """The monitors that a collection registry holds weakly, created once the first of them is registered.

    Only the outermost invalidation of the registry detaches the entries of dead or removed monitors, and its purge does not detach while an invalidation is in progress, so that no entry is detached while a monitor is being invalidated, and the next node is still the right one once it is invalidated.

    Args:
        canDetach: Whether the purge can detach entries, that is whether no invalidation of the registry is in progress.
    """

    def __init__(self, canDetach: Function[bool]) -> None:
        super().__init__()

        self.__items: _IItemRegistry[_WeakMonitor[T]] = _CreateItemRegistry()
        self.__canDetach: Function[bool] = canDetach
        self.__purger: _Purger = _Purger(self.__Purge)
    
    @final
    def __Purge(self) -> int:
        count: int = 0
        canDetach: bool = self.__canDetach()
        node: ILinkedNode[_WeakMonitor[T]]|None = self.__items.TryGetFirstNode()

        while node is not None:
            entry: _WeakMonitor[T] = node.GetValue()
            following: ILinkedNode[_WeakMonitor[T]]|None = node.GetNext()

            if canDetach and entry.TryGetMonitor() is None: entry.Detach()
            else: count += 1

            node = following
        
        return count
    
    def IsEmpty(self) -> bool: return self.__items.AsReadOnly().IsEmpty()

    def Register(self, item: T) -> IRemovable:
        self.__purger.Register()

        entry: _WeakMonitor[T] = _WeakMonitor[T](item)

        entry.SetNode(self.__items.Push(entry))

        return entry
    
    def GetMonitors(self, detach: bool) -> Generator[T]:
        node: ILinkedNode[_WeakMonitor[T]]|None = self.__items.TryGetFirstNode()

        while node is not None:
            entry: _WeakMonitor[T] = node.GetValue()
            monitor: T|None = entry.TryGetMonitor()

            if monitor is None:
                following: ILinkedNode[_WeakMonitor[T]]|None = node.GetNext()

                if detach: entry.Detach()

                node = following
            
            else:
                yield monitor

                node = node.GetNext()

class CollectionRegistry[T: IObjectMonitor](Abstract, ICollectionRegistry[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IItemRegistry[T] = CreateItemRegistry()
        self.__monitors: _WeakMonitors[T]|None = None
        self.__invalidations: int = 0

        self.__activate: Action = self.__Activate
        self.__invalidateObjects: Action = NoAction

        self.__monitor: IObjectMonitor = _Monitor(self)
        self.__registrar: IObjectRegistrar[T] = _Registrar(self)

    @final
    def __Activate(self) -> None:
        def finalize() -> None:
            monitors: _WeakMonitors[T]|None = self.__monitors

            if self._GetItems().IsEmpty() and (monitors is None or monitors.IsEmpty()):
                self.__activate = self.__Activate
                self.__invalidateObjects = NoAction
        
        self.__activate = NoAction
        self.__invalidateObjects = lambda: self.__InvalidateObjects(finalize)
    
    @final
    def __GetMonitors(self) -> Generator[T]:
        item: ILinkedNode[T]|None = self.__items.TryGetFirstNode()

        while item is not None:
            yield item.GetValue()

            item = item.GetNext()
        
        monitors: _WeakMonitors[T]|None = self.__monitors

        if monitors is not None: yield from monitors.GetMonitors(self.__invalidations == 1)
    @final
    def __InvalidateObjects(self, action: Action) -> None:
        self.__invalidations += 1

        try: _DoForEachItem(self.__GetMonitors(), lambda monitor: monitor.InvalidateObjects(), action)
        finally: self.__invalidations -= 1

    @final
    def _GetItems(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

    @final
    def RegisterObject(self, item: T) -> None:
        """Registers a monitor, and holds it strongly, unlike RegisterMonitor.

        It suits the monitors that the owner of this registry keeps for as long as the registry lives.

        Args:
            item: The monitor to register.
        """

        self.__activate()

        self.__items.Push(item)
    @final
    def RegisterMonitor(self, item: T) -> IRemovable:
        monitors: _WeakMonitors[T]|None = self.__monitors

        if monitors is None: self.__monitors = monitors = _WeakMonitors[T](lambda: self.__invalidations == 0)

        self.__activate()

        return _CollectionFactoryCookie(monitors.Register(item))
    
    def InvalidateObjects(self) -> None: self.__invalidateObjects()

    @final
    def AsMonitor(self) -> IObjectMonitor: return self.__monitor
    @final
    def AsRegistrar(self) -> IObjectRegistrar[T]: return self.__registrar