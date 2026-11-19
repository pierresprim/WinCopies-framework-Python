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
from WinCopies.Collections.Registry import IObjectMonitor
from WinCopies.Collections.Registry.Core import CollectionRegistry, InvalidatableObjectRegistry
from WinCopies.Typing.Delegate import IFunction
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable
from WinCopies.Typing.Object import CreateWeakReferenceRegister

_KERNEL: str = "WinCopies.Collections.Registry.Kernel"
_CORE: str = "WinCopies.Collections.Registry.Core"

class _Object(Abstract, IInvalidatable):
    """An object to register, which records its invalidation. A dead one is kept in a cycle with
    itself, so that it dies only at a pass of the collector, as enumerators and views do."""

    def __init__(self, name: str, log: list[str], cyclic: bool = False) -> None:
        super().__init__()

        self.__name: str = name
        self.__log: list[str] = log
        self.__cycle: object|None = self if cyclic else None

    def _Dispose(self, reason: DiscardReason) -> None: self.__log.append(self.__name)

class _Monitor(Abstract, IObjectMonitor):
    """A monitor that records its invalidation, and may act then, once."""

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
    monitors: object|None = getattr(registry, "_CollectionRegistry__monitors")

    return 0 if monitors is None else _count(getattr(monitors, "_WeakMonitors__items")._GetItems())

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

    def __Register(self, names: str, actions: dict[str, Callable[[], object]]|None = None) -> tuple[CollectionRegistry[IObjectMonitor], list[str], dict[str, _Monitor], dict[str, IRemovable]]:
        registry: CollectionRegistry[IObjectMonitor] = CollectionRegistry[IObjectMonitor]()
        log: list[str] = []
        monitors: dict[str, _Monitor] = {}
        handles: dict[str, IRemovable] = {}

        for name in names:
            monitors[name] = _Monitor(name, log, None if actions is None else actions.get(name))
            handles[name] = registry.RegisterMonitor(monitors[name])

        return registry, log, monitors, handles

    def __Invalidate(self, registry: CollectionRegistry[IObjectMonitor], log: list[str]) -> list[str]:
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
        registry: CollectionRegistry[IObjectMonitor] = CollectionRegistry[IObjectMonitor]()
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

        registry: CollectionRegistry[IObjectMonitor] = CollectionRegistry[IObjectMonitor]()
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

        self.__AssertFalls(TestTheCollectionRegistryInvalidatesItsLiveMonitors, mock.patch(f"{_CORE}._WeakMonitor.Remove", detaching))

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
