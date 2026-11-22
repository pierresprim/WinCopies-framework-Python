from __future__ import annotations

from abc import abstractmethod
from typing import cast, final
from weakref import ref

from WinCopies import Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Iteration import Generate, Iterate
from WinCopies.Collections.Registry import IObjectMonitor, IActivationObject, IActivatableMonitor, IObjectRegistrar, IObjectRegistry, ICollectionRegistry
from WinCopies.Collections.Registry.Kernel import IRegistry as _IRegistry, IWeakReferenceRegistry as _IWeakReferenceRegistry, IItemRegistry as _IItemRegistry, Registry as _Registry, WeakReferenceRegistry as _WeakReferenceRegistry, ItemRegistry as _ItemRegistry, CreateItemRegistry as _CreateItemRegistry
from WinCopies.Collections.Linked.Doubly import IReadOnlyList
from WinCopies.Collections.Linked.Node import ILinkedNode, IReadWriteLinkedNode
from WinCopies.Collections.Loop import DoForEachItem
from WinCopies.Delegates import NoAction, FuncNone, GetActionAsMethod
from WinCopies.Typing import InvalidOperationError
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

@final
class _NoActivationObject(Abstract, IActivationObject):
    """The activation object of a monitor that no collection registry holds, which does nothing.
    """

    def __init__(self) -> None: super().__init__()

    def Activate(self) -> None: pass

_noActivationObject: IActivationObject = _NoActivationObject()

def GetInvalidationActiveError() -> InvalidOperationError:
    return InvalidOperationError("A collection cannot be changed while its registry invalidates its monitors.")

def _GetActivationObject(current: IActivationObject, activationObject: IActivationObject) -> IActivationObject:
    """Gets the activation object that a monitor receives, once checked that it received none before.

    Args:
        current: The activation object that the monitor holds.
        activationObject: The activation object that the monitor receives.

    Returns:
        The activation object for the monitor to hold.

    Raises:
        InvalidOperationError: The monitor already received an activation object.
    """

    if current is not _noActivationObject: raise InvalidOperationError("This monitor already received an activation object.")

    return activationObject

class ObjectRegistryBase[TIn, TOut: IInvalidatable](Abstract, IObjectRegistry[TIn], IActivatableMonitor):
    def __init__(self) -> None:
        super().__init__()

        self.__items: _PurgeableWeakReferenceRegistry[TOut] = _PurgeableWeakReferenceRegistry[TOut]()
        self.__purger: _Purger = _Purger(self._Purge)

        self.__push: Converter[TOut, INodeBase] = self.__PushFirst
        self.__clear: Action = NoAction
        self.__activation: IActivationObject = _noActivationObject

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

        self.__activation.Activate()

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
    def IsActive(self) -> bool:
        """Tells whether an object was registered here since the last invalidation, which empties the registry.

        Returns:
            True if an object was registered here since the last invalidation, False otherwise.
        """

        return self.__clear is not NoAction
    @final
    def SetActivationObject(self, activationObject: IActivationObject) -> None: self.__activation = _GetActivationObject(self.__activation, activationObject)

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
class _MonitorEntry[T: IActivatableMonitor](Abstract, IRemovable):
    """The entry of a monitor in the lists of a collection registry. It holds the monitor strongly, for RegisterObject, or weakly and without a callback, for RegisterMonitor, and knows the list it is in.

    The entry is never detached from its list by a finalizer, nor by its removal. Its removal only empties the reference, and the registry detaches the entry itself, as it does for a dead monitor, at an invalidation for an active entry, and at a purge for an inactive one.

    Args:
        tryGetMonitor: Returns the monitor, or None once it is dead.
    """

    def __init__(self, tryGetMonitor: NullableFunction[T]) -> None:
        super().__init__()

        self.__tryGetMonitor: NullableFunction[T] = tryGetMonitor
        self.__items: _IItemRegistry[_MonitorEntry[T]]|None = None
        self.__node: IRemovable|None = None
    
    def TryGetMonitor(self) -> T|None: return self.__tryGetMonitor()

    def IsIn(self, items: _IItemRegistry[_MonitorEntry[T]]) -> bool: return self.__items is items

    def MoveTo(self, items: _IItemRegistry[_MonitorEntry[T]]) -> None:
        """Detaches this entry from its list, if it is in one, and adds it at the end of another one.

        Args:
            items: The list to add this entry to.
        """

        self.Detach()

        self.__node = items.Push(self)
        self.__items = items

    def Detach(self) -> None:
        node: IRemovable|None = self.__node

        if node is not None:
            self.__node = None
            self.__items = None

            node.Remove()
    
    def Remove(self) -> None: self.__tryGetMonitor = FuncNone

@final
class _ActivationObject(Abstract, IActivationObject):
    """The activation object that a collection registry gives to a monitor it registers, which exposes only the activation of its entry.

    Args:
        activate: Activates the entry of the monitor.
    """

    def __init__(self, activate: Action) -> None:
        super().__init__()

        self.__activate: Action = activate
    
    def Activate(self) -> None: self.__activate()

class CollectionRegistry[T: IActivatableMonitor](Abstract, ICollectionRegistry[T]):
    """Invalidates the active monitors registered here. Each monitor is either active, and invalidated by the writes of the collection, or inactive, and left out of them until it asks to be active again.

    An invalidation drains the active entries from the head, until none is left, and holds no node from a step to the next. A monitor that is still active once invalidated is set aside, then put back among the active ones at the end of the invalidation, and the others go among the inactive ones. A monitor that becomes active during an invalidation is put at the end of the active entries, so that the same invalidation reaches it. The registry refuses to be invalidated again before the end of an invalidation.
    """

    def __init__(self) -> None:
        super().__init__()

        # Created once needed, so that building a registry builds one list only.
        self.__actives: _IItemRegistry[_MonitorEntry[T]]|None = None
        self.__inactives: _IItemRegistry[_MonitorEntry[T]] = _CreateItemRegistry()
        self.__aside: _IItemRegistry[_MonitorEntry[T]]|None = None
        self.__purger: _Purger = _Purger(self.__Purge)
        self.__invalidating: bool = False
        self.__activation: IActivationObject = _noActivationObject

        self.__monitor: IObjectMonitor = _Monitor(self)
        self.__registrar: IObjectRegistrar[T] = _Registrar(self)
    
    @final
    def __GetActives(self) -> _IItemRegistry[_MonitorEntry[T]]:
        actives: _IItemRegistry[_MonitorEntry[T]]|None = self.__actives

        if actives is None: self.__actives = actives = _CreateItemRegistry()

        return actives
    @final
    def __GetAside(self) -> _IItemRegistry[_MonitorEntry[T]]:
        aside: _IItemRegistry[_MonitorEntry[T]]|None = self.__aside

        if aside is None: self.__aside = aside = _CreateItemRegistry()

        return aside
    
    @final
    def __Purge(self) -> int:
        def purge(items: _IItemRegistry[_MonitorEntry[T]]) -> int:
            count: int = 0
            node: ILinkedNode[_MonitorEntry[T]]|None = items.TryGetFirstNode()

            while node is not None:
                entry: _MonitorEntry[T] = node.GetValue()
                following: ILinkedNode[_MonitorEntry[T]]|None = node.GetNext()

                if entry.TryGetMonitor() is None: entry.Detach()
                else: count += 1

                node = following
            
            return count
        
        actives: _IItemRegistry[_MonitorEntry[T]]|None = self.__actives

        return purge(self.__inactives) + (0 if actives is None else purge(actives))
    
    @final
    def __Activate(self, entry: _MonitorEntry[T]) -> None:
        if entry.IsIn(self.__inactives):
            entry.MoveTo(self.__GetActives())

            self.__activation.Activate()
    @final
    def __Register(self, entry: _MonitorEntry[T], monitor: T) -> None:
        self.__purger.Register()

        if monitor.IsActive():
            entry.MoveTo(self.__GetActives())

            self.__activation.Activate()
        
        else: entry.MoveTo(self.__inactives)

        try: monitor.SetActivationObject(_ActivationObject(lambda: self.__Activate(entry)))
        except BaseException:
            entry.Detach()

            raise

    @final
    def __Drain(self) -> Generator[_MonitorEntry[T]]:
        actives: _IItemRegistry[_MonitorEntry[T]] = self.__GetActives()
        node: ILinkedNode[_MonitorEntry[T]]|None = actives.TryGetFirstNode()

        while node is not None:
            entry: _MonitorEntry[T] = node.GetValue()
            # Held until the monitor is invalidated, so that it cannot die in between.
            monitor: T|None = entry.TryGetMonitor()

            # The entry of the monitor being invalidated is in no list, until it is put where its activity says.
            entry.Detach()

            if monitor is not None: yield entry
            
            node = actives.TryGetFirstNode()
    @final
    def __Invalidate(self, entry: _MonitorEntry[T]) -> None:
        monitor: T|None = entry.TryGetMonitor()

        if monitor is not None:
            try: monitor.InvalidateObjects()
            finally:
                if entry.TryGetMonitor() is not None: entry.MoveTo(self.__GetAside() if monitor.IsActive() else self.__inactives)
    @final
    def __InvalidateObjects(self) -> None:
        self.__invalidating = True

        try: _DoForEachItem(self.__Drain(), self.__Invalidate, None)
        finally:
            aside: _IItemRegistry[_MonitorEntry[T]]|None = self.__aside

            if aside is not None:
                actives: _IItemRegistry[_MonitorEntry[T]] = self.__GetActives()
                node: ILinkedNode[_MonitorEntry[T]]|None = aside.TryGetFirstNode()

                while node is not None:
                    node.GetValue().MoveTo(actives)

                    node = aside.TryGetFirstNode()
            
            self.__invalidating = False

    @final
    def RegisterObject(self, item: T) -> None:
        """Registers a monitor, and holds it strongly, unlike RegisterMonitor.

        It suits the monitors that the owner of this registry keeps for as long as the registry lives.

        Args:
            item: The monitor to register.
        """

        self.__Register(_MonitorEntry[T](lambda: item), item)
    @final
    def RegisterMonitor(self, item: T) -> IRemovable:
        entry: _MonitorEntry[T] = _MonitorEntry[T](ref(item))

        self.__Register(entry, item)

        return _CollectionFactoryCookie(entry)
    
    def InvalidateObjects(self) -> None:
        """Invalidates the active monitors registered here.

        Raises:
            InvalidOperationError: The registry is already invalidating its monitors, as when a monitor writes to the collection during its invalidation.
        """

        if self.__invalidating: raise GetInvalidationActiveError()

        if self.IsActive(): self.__InvalidateObjects()

    @final
    def IsActive(self) -> bool:
        """Tells whether a monitor registered here is active.

        Returns:
            True if a monitor registered here is active, False otherwise.
        """

        actives: _IItemRegistry[_MonitorEntry[T]]|None = self.__actives

        return actives is not None and not actives.AsReadOnly().IsEmpty()
    @final
    def SetActivationObject(self, activationObject: IActivationObject) -> None: self.__activation = _GetActivationObject(self.__activation, activationObject)

    @final
    def AsMonitor(self) -> IObjectMonitor: return self.__monitor
    @final
    def AsRegistrar(self) -> IObjectRegistrar[T]: return self.__registrar
