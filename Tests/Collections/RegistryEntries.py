"""
Benches of the entries of the registries: how a registry holds what it registers, and how it lets go
of what dies.

No finalizer of the framework changes a list of a registry (Registre 8). A registry holds an object
through a weak reference without a callback, so that the death of the object, which may come at any
point, even in the middle of an operation of the registry, runs nothing. The registry drops the
entries of dead objects itself: at an invalidation, at a lookup, or in a purge that runs once the
registrations since the last purge reach the entries it left. The collection registry holds strongly
the monitors registered by RegisterObject, which its own collection keeps, and weakly those
registered by RegisterMonitor, which other objects own; removing one only empties its entry, which
the outermost invalidation detaches (D-130).

D-123 to D-125 came from finalizers that removed a node in the middle of a traversal, of an addition,
or of the removal of the head (Registre 1). Their benches place a pass of the garbage collector at
the entry of a method that the operation calls, while a registered object waits for the collector in
a cycle, at the points that the probe regfin_window found (Registre 1 §3.2 and §3.3). The pass runs
because the bench calls gc.collect() there: what it shows does not depend on when CPython schedules
its own passes. D-131 came from a cursor whose death removed a node of the sorted index during a
binary search (Registre 8); its bench places a pass during the search in the same way.

A registry that keeps an index alongside its list, sorted for the cursors of the indexables, keyed
for those of the linked lists, returns for each object a node that removes it from both, so that a
disposed cursor leaves the index (D-127, D-132). The entries of an index are removed by identity, so
that the removal of an object never removes the entry of another one of the same key (D-128, D-133),
and the index is purged along with the list. A keyed registry drops the entry of a dead object
before registering another one under its key (D-135). See Registre 2 and Registre 10.
"""

import contextlib
import gc
import pkgutil
import unittest
import weakref

from collections.abc import Callable, Generator
from typing import Any
from unittest import mock

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Collection import ArrayCollection, ArrayList, CreateList
from WinCopies.Collections.Circular import CircularList
from WinCopies.Collections.Extensions.Enumeration import ResumableTupleEnumerator
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Linked.Doubly.Welded import MakeList
from WinCopies.Collections.Registry import IActivationObject, IActivatableMonitor
from WinCopies.Collections.Registry.Core import CollectionRegistry, InvalidatableObjectRegistry, ObjectRegistryBase
from WinCopies.Collections.Registry.Mapping import KeyedDisposableObjectRegistry
from WinCopies.Collections.Registry.Sorted import SortedDisposableObjectRegistry
from WinCopies.Typing.Delegate import IFunction
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable
from WinCopies.Typing.Object import CreateWeakReferenceRegister

_KERNEL: str = "WinCopies.Collections.Registry.Kernel"
_CORE: str = "WinCopies.Collections.Registry.Core"
_SORTED: str = "WinCopies.Collections.Registry.Sorted"
_MAPPING: str = "WinCopies.Collections.Registry.Mapping"

class _Object(Abstract, IInvalidatable):
    """An object to register, which records its invalidation. A dead one is kept in a cycle with
    itself, so that it dies only at a pass of the collector, as enumerators and views do."""

    def __init__(self, name: str, log: list[str], cyclic: bool = False) -> None:
        super().__init__()

        self.__name: str = name
        self.__log: list[str] = log
        self.__cycle: object|None = self if cyclic else None

    def _Dispose(self, reason: DiscardReason) -> None: self.__log.append(self.__name)

class _Monitor(Abstract, IActivatableMonitor):
    """A monitor that records its invalidation, and may act then, once. It is always active, so that
    each invalidation of its registry reaches it."""

    def __init__(self, name: str, log: list[str], action: Callable[[], object]|None = None) -> None:
        super().__init__()

        self.__name: str = name
        self.__log: list[str] = log
        self.__action: Callable[[], object]|None = action

    def InvalidateObjects(self) -> None:
        action: Callable[[], object]|None = self.__action

        self.__log.append(self.__name)
        self.__action = None

        if action is not None: action()

    def IsActive(self) -> bool: return True

    def SetActivationObject(self, activationObject: IActivationObject) -> None: pass

class _Handle(IFunction[int]):
    """Cell initialiser for ArrayList, which takes a provider rather than a sequence."""

    def GetValue(self) -> int: return 0

class _Collector:
    """Runs one pass of the garbage collector at the entry of the method that its target names, the
    first time the method is called once the collector is armed."""

    def __init__(self, target: str) -> None:
        self.__target: str = target
        self.__armed: bool = False
        self.fired: int = 0

    def Arm(self) -> None: self.__armed = True

    @contextlib.contextmanager
    def Patch(self) -> Generator[None]:
        original: Callable[..., object] = pkgutil.resolve_name(self.__target)

        def collecting(*args: Any, **kwargs: Any) -> object:
            if self.__armed:
                self.__armed = False
                self.fired += 1

                gc.collect()

            return original(*args, **kwargs)

        with mock.patch(self.__target, collecting): yield

@contextlib.contextmanager
def _collectorDisabled() -> Generator[None]:
    enabled: bool = gc.isenabled()

    gc.disable()

    try: yield
    finally:
        if enabled: gc.enable()

@contextlib.contextmanager
def _drainBounded() -> Generator[None]:
    """Stops a drain that would never end, as D-125 made it, after forty removals."""

    original: Callable[..., object] = pkgutil.resolve_name(f"{_KERNEL}.WeakReferenceRegistry.TryRemoveFirst")
    calls: list[int] = [0]

    def bounded(self: Any) -> object:
        calls[0] += 1

        if calls[0] > 40: raise RuntimeError("the drain does not end")

        return original(self)

    with mock.patch(f"{_KERNEL}.WeakReferenceRegistry.TryRemoveFirst", bounded): yield

def _count(items: Any) -> int:
    count: int = 0
    node: Any = items.GetFirstNode()

    while node is not None:
        count += 1
        node = node.GetNext()

    return count

def _registryNodes(registry: object) -> int: return _count(getattr(registry, "_ObjectRegistryBase__items")._GetItems())

def _weakMonitorNodes(registry: object) -> int:
    """The entries of the monitors registered by RegisterMonitor, active or not, which the registry
    holds weakly."""

    count: int = 0

    for items in (getattr(registry, "_CollectionRegistry__actives"), getattr(registry, "_CollectionRegistry__inactives")):
        node: Any = items._GetItems().GetFirstNode()

        while node is not None:
            if isinstance(getattr(node.GetValue(), "_MonitorEntry__tryGetMonitor"), weakref.ref): count += 1

            node = node.GetNext()

    return count

def _sortedEntries(enumerator: object) -> int:
    count: int = getattr(getattr(enumerator, "_ResumableIncrementalEnumerator__cursors"), "_GetSortedItems")().GetCount()

    return count

def _keyedEntries(enumerator: object) -> int:
    count: int = getattr(getattr(enumerator, "_GetCursors")(), "_GetKeyedItems")().GetCount()

    return count

class _SortedRegistry(SortedDisposableObjectRegistry[int, _Object]):
    """A sorted registry that gives all its objects the same key."""

    def _GetKey(self, item: _Object) -> int: return 0

class _KeyedRegistry(KeyedDisposableObjectRegistry[int, _Object]):
    """A keyed registry that gives all its objects the same key."""

    def _GetKey(self, item: _Object) -> int: return 0

def _registration(layout: tuple[tuple[str, bool], ...], target: str, added: tuple[str, ...] = ()) -> tuple[list[str], set[str], int]:
    """Registers the objects of the layout, the dead ones left for the collector, then X with a pass of
    the collector at the entry of target, then those added, and invalidates the registry. Returns
    what was invalidated, what lives, and the number of passes run."""

    with _collectorDisabled():
        log: list[str] = []
        registry: InvalidatableObjectRegistry[IInvalidatable] = InvalidatableObjectRegistry[IInvalidatable]()
        kept: dict[str, _Object] = {}

        for name, dead in layout:
            item: _Object = _Object(name, log, dead)

            registry.RegisterObject(item)

            if not dead: kept[name] = item

            del item

        collector: _Collector = _Collector(target)

        kept["X"] = _Object("X", log)

        with collector.Patch():
            collector.Arm()
            registry.RegisterObject(kept["X"])

        for name in added:
            kept[name] = _Object(name, log)

            registry.RegisterObject(kept[name])

        with _drainBounded(): registry.InvalidateObjects()

        return log, set(kept), collector.fired

class TestADeadObjectChangesNoListOfTheRegistry(unittest.TestCase):
    """D-124 and D-125 (Registre 1 §3.2 and §3.3): a registered object that dies in the middle of an
    operation of the registry does not lose the registration in progress, nor those after it, nor
    stop the drain of an invalidation (Registre 8)."""

    def test_an_object_dying_during_a_registration_loses_nothing(self) -> None:
        """The points that regfin_window found: once the last node is read, once the new node is
        about to be built, and once it is about to be linked."""

        for label, layout, target, added in (("after the last node is read",       (("L", True),),               f"{_KERNEL}._List._GetNodeAsInterface",                 ()),
                                             ("after the last node is read, behind P", (("P", False), ("L", True)), f"{_KERNEL}._List._GetNodeAsInterface",                 ()),
                                             ("before the new node is built",      (("L", True),),               f"{_KERNEL}._Node.__init__",                            ("Y", "Z")),
                                             ("before the new node is built, behind P", (("P", False), ("L", True)), f"{_KERNEL}._Node.__init__",                            ()),
                                             ("before the new node is linked",     (("P", False), ("L", True)), "WinCopies.Collections.Linked.Node.LinkedNode._SetNext", ())):
            with self.subTest(at = label):
                log, alive, fired = _registration(layout, target, added)

                self.assertEqual(fired, 1, "the bench placed no pass of the collector")
                self.assertEqual(alive - set(log), set(), "a live object was not invalidated")

    def test_an_object_dying_during_the_removal_of_the_head_does_not_stop_the_drain(self) -> None:
        with _collectorDisabled():
            log: list[str] = []
            registry: InvalidatableObjectRegistry[IInvalidatable] = InvalidatableObjectRegistry[IInvalidatable]()
            head: _Object = _Object("H", log)
            last: _Object = _Object("M", log)

            registry.RegisterObject(head)
            registry.RegisterObject(_Object("N", log, True))
            registry.RegisterObject(last)

            collector: _Collector = _Collector("WinCopies.Collections.Linked.Doubly.Node.DoublyLinkedNodeBase._UpdateFirst")

            with collector.Patch(), _drainBounded():
                collector.Arm()
                registry.InvalidateObjects()

        self.assertEqual(collector.fired, 1, "the bench placed no pass of the collector")
        self.assertEqual(log, ["H", "M"])

class TestTheCollectionRegistryInvalidatesItsLiveMonitors(unittest.TestCase):
    """D-123 and D-130: what happens to the list of the collection registry while its monitors are
    invalidated stops nothing. A monitor removed during an invalidation is only emptied, and only
    the outermost invalidation detaches entries (Registre 8)."""

    def __Register(self, names: str, actions: dict[str, Callable[[], object]]|None = None) -> tuple[CollectionRegistry[IActivatableMonitor], list[str], dict[str, _Monitor], dict[str, IRemovable]]:
        registry: CollectionRegistry[IActivatableMonitor] = CollectionRegistry[IActivatableMonitor]()
        log: list[str] = []
        monitors: dict[str, _Monitor] = {}
        handles: dict[str, IRemovable] = {}

        for name in names:
            monitors[name] = _Monitor(name, log, None if actions is None else actions.get(name))
            handles[name] = registry.RegisterMonitor(monitors[name])

        return registry, log, monitors, handles

    def __Invalidate(self, registry: CollectionRegistry[IActivatableMonitor], log: list[str]) -> list[str]:
        registry.InvalidateObjects()

        result: list[str] = list(log)

        log.clear()

        return result

    def test_a_monitor_removed_during_its_own_invalidation_leaves_the_others_invalidated(self) -> None:
        handles: dict[str, IRemovable] = {}
        registry, log, _, registered = self.__Register("ABC", {"A": lambda: handles["A"].Remove()})

        handles.update(registered)

        self.assertEqual(self.__Invalidate(registry, log), ["A", "B", "C"])
        self.assertEqual(self.__Invalidate(registry, log), ["B", "C"])

    def test_a_monitor_removed_by_the_one_before_it_is_invalidated_no_more(self) -> None:
        handles: dict[str, IRemovable] = {}
        registry, log, _, registered = self.__Register("ABC", {"A": lambda: handles["B"].Remove()})

        handles.update(registered)

        self.assertEqual(self.__Invalidate(registry, log), ["A", "C"])
        self.assertEqual(self.__Invalidate(registry, log), ["A", "C"])

    def test_a_monitor_registered_during_an_invalidation_is_invalidated_by_it(self) -> None:
        kept: list[_Monitor] = []
        registry: CollectionRegistry[IActivatableMonitor] = CollectionRegistry[IActivatableMonitor]()
        log: list[str] = []

        def register() -> None:
            kept.append(_Monitor("D", log))

            registry.RegisterMonitor(kept[-1])

        first: _Monitor = _Monitor("A", log, register)

        registry.RegisterMonitor(first)

        self.assertEqual(self.__Invalidate(registry, log), ["A", "D"])

    def test_a_monitor_dropped_during_its_invalidation_leaves_the_others_invalidated(self) -> None:
        """D-123 as regfin_items found it: a monitor releases its own owner while it is invalidated."""

        monitors: dict[str, _Monitor] = {}
        registry, log, registered, _ = self.__Register("ABC", {"B": lambda: monitors.pop("B")})

        monitors.update(registered)

        del registered

        self.assertEqual(self.__Invalidate(registry, log), ["A", "B", "C"])

        gc.collect()

        self.assertEqual(self.__Invalidate(registry, log), ["A", "C"])

    def test_a_nested_invalidation_detaches_nothing_that_the_outer_one_reads(self) -> None:
        """A monitor writes, so to speak, during its invalidation: the registry is invalidated again
        while a dead monitor follows it."""

        registry: CollectionRegistry[IActivatableMonitor] = CollectionRegistry[IActivatableMonitor]()
        log: list[str] = []
        first: _Monitor = _Monitor("A", log, registry.InvalidateObjects)
        dead: _Monitor = _Monitor("B", log)
        last: _Monitor = _Monitor("C", log)

        for monitor in (first, dead, last): registry.RegisterMonitor(monitor)

        del dead

        gc.collect()

        self.assertEqual(self.__Invalidate(registry, log), ["A", "A", "C", "C"])

class TestARegistryLetsGoOfWhatDies(unittest.TestCase):
    """The entries of dead objects do not pile up, though no finalizer removes them: the purge runs
    once the registrations since the last purge reach the entries it left, and at least a fixed
    minimum of sixteen (Registre 8)."""

    def test_abandoned_enumerators_do_not_pile_up(self) -> None:
        source: Any = CreateList([0, 1, 2])
        registry: object = source._GetCollectionRegistries().GetEnumeratorRegistry()._GetRegistry()

        for _ in range(100):
            enumerator: Any = source.TryGetEnumerator()

            enumerator.TryMoveNext()

            del enumerator

            gc.collect()

        self.assertLessEqual(_registryNodes(registry), 32)

    def test_dropped_circular_lists_do_not_pile_up_in_their_source(self) -> None:
        source: Any = CreateList([0, 1, 2, 3])
        registries: object = source._GetCollectionRegistries()

        for _ in range(100):
            circular: CircularList[int] = CircularList[int](source, 1)

            del circular

            gc.collect()

        self.assertLessEqual(_weakMonitorNodes(registries), 32)

        source.Add(9)

        self.assertEqual(_weakMonitorNodes(registries), 0, "a write did not detach the entries of the dropped lists")

    def test_a_dropped_array_collection_leaves_the_registry_of_its_array(self) -> None:
        """D-129: the array outlives the collection that wraps it."""

        array: Any = getattr(ArrayList[int](3, _Handle()), "_GetItems")()
        collection: ArrayCollection[int] = ArrayCollection[int](array)
        registries: weakref.ReferenceType[Any] = weakref.ref(getattr(collection, "_GetCollectionRegistries")())

        del collection

        gc.collect()

        self.assertIsNone(registries(), "the array kept the registries of a dropped collection")

class TestTheSortedIndexOfTheCursorsLetsGoOfDeadCursors(unittest.TestCase):
    """The sorted index of the resumable cursors of the indexables (Registre 2, Registre 8)."""

    def test_a_dead_cursor_does_not_keep_its_index_from_being_reused(self) -> None:
        enumerator: ResumableTupleEnumerator[int] = ResumableTupleEnumerator[int](CreateList([10, 20, 30, 40]))

        enumerator.TryMoveNext()
        enumerator.TryMoveNext()
        enumerator.PlaceCursor()

        gc.collect()

        self.assertIs(enumerator.PlaceCursor(), enumerator.PlaceCursor())

    def test_a_cursor_dying_during_the_search_of_the_index_breaks_nothing(self) -> None:
        """D-131: a cursor dies in the middle of the binary search of the index, at the first key it
        reads, while the search goes past it to place a cursor further on."""

        with _collectorDisabled():
            enumerator: ResumableTupleEnumerator[int] = ResumableTupleEnumerator[int](CreateList(list(range(10))))
            kept: list[Any] = []

            for _ in range(5):
                enumerator.TryMoveNext()
                kept.append(enumerator.PlaceCursor())

            enumerator.TryMoveNext()

            dead: list[object] = [enumerator.PlaceCursor()]

            dead.append(dead)

            del dead

            enumerator.TryMoveNext()

            collector: _Collector = _Collector("WinCopies.Collections.Registry.Sorted.GetKey")

            with collector.Patch():
                collector.Arm()

                placed: Any = enumerator.PlaceCursor()

        self.assertEqual(collector.fired, 1, "the bench placed no pass of the collector")
        self.assertIs(enumerator.PlaceCursor(), placed)

class TestADisposedCursorLeavesTheIndexOfItsRegistry(unittest.TestCase):
    """A disposed cursor leaves the index of its registry along with its list, so that the next
    cursor placed where it was is a new one, which the placement after reuses (Registre 2, Registre 10)."""

    def test_a_disposed_cursor_of_an_indexable_is_not_placed_again(self) -> None:
        """D-127: the sorted index kept the disposed cursor, which the lookup found first, so that
        each placement at its index registered a new cursor."""

        enumerator: ResumableTupleEnumerator[int] = ResumableTupleEnumerator[int](CreateList([10, 20, 30]))

        enumerator.TryMoveNext()
        enumerator.TryMoveNext()

        disposed: Any = enumerator.PlaceCursor()

        disposed.Dispose()

        placed: Any = enumerator.PlaceCursor()

        self.assertIsNot(placed, disposed)
        self.assertIs(enumerator.PlaceCursor(), placed)
        self.assertEqual(_sortedEntries(enumerator), 1)

    def test_a_disposed_cursor_of_a_linked_list_is_not_placed_again(self) -> None:
        """D-132: the dictionary kept the disposed cursor, which the placement at its node returned."""

        items: Any = MakeList(10, 20, 30)
        enumerator: Any = items.TryGetResumableNodeEnumerator()

        enumerator.TryMoveNext()
        enumerator.TryMoveNext()

        disposed: Any = enumerator.PlaceCursor()

        disposed.Dispose()

        placed: Any = enumerator.PlaceCursor()

        self.assertIsNot(placed, disposed)

        enumerator.TryMoveNext()
        placed.Resume()

        self.assertEqual(enumerator.GetCurrent().GetValue(), 20)
        self.assertEqual(_keyedEntries(enumerator), 1)

class TestTheIndexesRemoveTheirEntriesByIdentity(unittest.TestCase):
    """The removal of an object removes its own entry of the index, never the entry of another object
    of the same key (Registre 2, Registre 10)."""

    def test_the_sorted_index_keeps_the_node_of_another_object_of_the_same_key(self) -> None:
        """D-128: the removal by key removed the first node of the key, which was not its own."""

        log: list[str] = []
        registry: _SortedRegistry = _SortedRegistry()
        first: _Object = _Object("A", log)
        second: _Object = _Object("B", log)

        registry.RegisterObject(first)

        node: IRemovable = getattr(registry, "_Push")(second)

        node.Remove()

        self.assertIs(registry.TryGetValue(0).TryGetValue(), first)
        self.assertEqual(getattr(registry, "_GetSortedItems")().GetCount(), 1)

    def test_the_dictionary_keeps_the_entry_that_another_object_took_since(self) -> None:
        """D-133: the removal by key removed the entry that another object took since under the key."""

        log: list[str] = []
        registry: _KeyedRegistry = _KeyedRegistry()
        node: IRemovable = getattr(registry, "_Push")(_Object("A", log))

        gc.collect()

        second: _Object = _Object("B", log)

        registry.RegisterObject(second)
        node.Remove()

        self.assertIs(registry.TryGetValue(0).TryGetValue(), second)

class TestTheIndexesLetGoOfDeadCursors(unittest.TestCase):
    """The purge of a registry removes the entries of dead cursors from its index too, so that they do
    not pile up until the end of the enumeration (Registre 9 §5, Registre 10)."""

    def test_abandoned_cursors_of_an_indexable_do_not_pile_up_in_the_sorted_index(self) -> None:
        enumerator: ResumableTupleEnumerator[int] = ResumableTupleEnumerator[int](CreateList(list(range(200))))

        for _ in range(100):
            enumerator.TryMoveNext()
            enumerator.PlaceCursor()

            gc.collect()

        self.assertLessEqual(_sortedEntries(enumerator), 32)

    def test_abandoned_cursors_of_a_linked_list_do_not_pile_up_in_the_dictionary(self) -> None:
        items: Any = MakeList(*range(200))
        enumerator: Any = items.TryGetResumableNodeEnumerator()

        for _ in range(100):
            enumerator.TryMoveNext()
            enumerator.PlaceCursor()

            gc.collect()

        self.assertLessEqual(_keyedEntries(enumerator), 32)

class TestAKeyedRegistryLetsANewObjectTakeTheKeyOfADeadOne(unittest.TestCase):
    """D-135: no finalizer removes the entry of a dead object any more, so that the registration under
    its key raised KeyError until a lookup or a purge dropped it (Registre 10)."""

    def test_an_object_takes_the_key_of_a_dead_one(self) -> None:
        log: list[str] = []
        registry: _KeyedRegistry = _KeyedRegistry()

        registry.RegisterObject(_Object("A", log))

        gc.collect()

        second: _Object = _Object("B", log)

        registry.RegisterObject(second)

        self.assertIs(registry.TryGetValue(0).TryGetValue(), second)

    def test_an_object_does_not_take_the_key_of_a_live_one(self) -> None:
        log: list[str] = []
        registry: _KeyedRegistry = _KeyedRegistry()
        first: _Object = _Object("A", log)

        registry.RegisterObject(first)

        with self.assertRaises(KeyError): registry.RegisterObject(_Object("B", log))

        self.assertIs(registry.TryGetValue(0).TryGetValue(), first)

def _run(bench: type[unittest.TestCase]) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    unittest.defaultTestLoader.loadTestsFromTestCase(bench).run(result)

    return result

def _fell(result: unittest.TestResult) -> int: return len(result.failures) + len(result.errors)

class TestTheRegistryEntryBenchesCanFail(unittest.TestCase):
    """Each bench above is run against the framework rebuilt as it was before, or with one part of
    the fix taken out: green on the intact tree, red on the rebuilt one."""

    def __AssertFalls(self, bench: type[unittest.TestCase], *patches: Any) -> None:
        self.assertEqual(_fell(_run(bench)), 0, "the bench is expected to pass on the intact tree")

        with contextlib.ExitStack() as stack:
            for patch in patches: stack.enter_context(patch)

            broken: unittest.TestResult = _run(bench)

        self.assertGreater(_fell(broken), 0, "the bench did not fall on the rebuilt tree")

    def test_the_benches_of_a_dying_object_fall_with_the_finalizer_of_the_cookie(self) -> None:
        """The registry registers through the cookie that a finalizer removes, as before."""

        self.__AssertFalls(TestADeadObjectChangesNoListOfTheRegistry, mock.patch(f"{_CORE}.CreateDisposableReferenceRegister", CreateWeakReferenceRegister))

    def test_the_benches_of_the_monitors_fall_when_a_removal_detaches_at_once(self) -> None:
        def detaching(self: Any) -> None: self.Detach()

        self.__AssertFalls(TestTheCollectionRegistryInvalidatesItsLiveMonitors, mock.patch(f"{_CORE}._MonitorEntry.Remove", detaching))

    def test_the_benches_of_the_dead_entries_fall_without_the_purge(self) -> None:
        def counting(self: Any) -> None: pass

        self.__AssertFalls(TestARegistryLetsGoOfWhatDies, mock.patch(f"{_CORE}._Purger.Register", counting))

    def test_the_benches_of_the_sorted_index_fall_with_the_finalizer_of_the_cookie(self) -> None:
        """The death of a cursor removes its node of the sorted index from a finalizer, as before (D-131)."""

        self.__AssertFalls(TestTheSortedIndexOfTheCursorsLetsGoOfDeadCursors, mock.patch(f"{_CORE}.CreateDisposableReferenceRegister", CreateWeakReferenceRegister))

    def test_the_benches_of_the_sorted_index_fall_when_a_lookup_keeps_dead_nodes(self) -> None:
        def keeping(self: Any, key: Any) -> Any:
            node: Any = self._GetSortedItems().TryGetNode(key)

            return None if node is None else node.TryGetValue()

        self.__AssertFalls(TestTheSortedIndexOfTheCursorsLetsGoOfDeadCursors, mock.patch("WinCopies.Collections.Registry.Sorted.SortedObjectRegistryBase.TryGetItem", keeping))

    def test_the_benches_of_the_disposed_cursors_fall_when_their_node_removes_only_itself(self) -> None:
        """The node that a cursor removes at its disposal leaves the index as it was, as before (D-127, D-132)."""

        def nodeOnly(self: Any) -> None: getattr(self, "_GetNode")().Remove()

        self.__AssertFalls(TestADisposedCursorLeavesTheIndexOfItsRegistry, mock.patch(f"{_KERNEL}.CompositeNode.Remove", nodeOnly))

    def test_the_benches_of_the_identity_fall_when_the_sorted_index_removes_by_key(self) -> None:
        def byKey(self: Any, node: Any) -> bool:
            removed: bool = self.TryRemove(node.GetKey())

            return removed

        self.__AssertFalls(TestTheIndexesRemoveTheirEntriesByIdentity, mock.patch(f"{_SORTED}.SortedList.TryRemoveNode", byKey))

    def test_the_benches_of_the_identity_fall_when_the_dictionary_removes_by_key(self) -> None:
        def byKey(self: Any) -> None: getattr(self, "_KeyedNode__items").TryRemove(getattr(self, "_KeyedNode__key"))

        self.__AssertFalls(TestTheIndexesRemoveTheirEntriesByIdentity, mock.patch(f"{_MAPPING}._KeyedNode.Remove", byKey))

    def test_the_benches_of_the_dead_cursors_fall_when_the_purge_leaves_the_indexes(self) -> None:
        """Only the list of the registry is purged, as before."""

        listOnly: Callable[[Any], int] = getattr(ObjectRegistryBase, "_Purge")

        self.__AssertFalls(TestTheIndexesLetGoOfDeadCursors, mock.patch(f"{_SORTED}.SortedObjectRegistryBase._Purge", listOnly), mock.patch(f"{_MAPPING}.KeyedObjectRegistryBase._Purge", listOnly))

    def test_the_benches_of_the_key_of_a_dead_object_fall_when_the_registration_keeps_its_entry(self) -> None:
        """The registration adds the entry without dropping the one of a dead object first, as before (D-135)."""

        compositeNode: Callable[..., IRemovable] = pkgutil.resolve_name(f"{_KERNEL}.CompositeNode")
        keyedNode: Callable[..., IRemovable] = pkgutil.resolve_name(f"{_MAPPING}._KeyedNode")

        def adding(self: Any, obj: Any, node: Any) -> IRemovable:
            items: Any = getattr(self, "_GetKeyedItems")()
            key: Any = getattr(self, "_GetKey")(obj)
            reference: weakref.ReferenceType[Any] = weakref.ref(obj)

            try: items.Add(key, reference)

            except KeyError:
                node.Remove()

                raise

            return compositeNode(node, keyedNode(key, reference, items))

        self.__AssertFalls(TestAKeyedRegistryLetsANewObjectTakeTheKeyOfADeadOne, mock.patch(f"{_MAPPING}.KeyedObjectRegistryBase._GetRemovable", adding))
