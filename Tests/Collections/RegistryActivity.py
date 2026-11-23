"""
Benches of the activity of the registries: a collection registry invalidates, at a write of its
collection, only the monitors that are active, and a monitor goes back among the active ones when it
asks to (Registre 11 and Registre 12).

A monitor of a collection registry implements IActivatableMonitor: it tells whether it is active, and
receives at its registration the activation object by which it asks to be active again. The registry
reads its activity at its registration, and again once it invalidated it, and a write that finds no
active monitor runs nothing. An invalidation drains the active monitors, and reaches a monitor that
becomes active while it runs. A registry of enumerators is active from the start of its first
enumerator to the next invalidation, and a collection registry registered in another one, as that of a
CircularList in its source, asks to be active there once one of its own monitors is. A collection
registry refuses to be invalidated during its own invalidation, as when a monitor writes to the
collection then.

The benches register into the registries of real collections monitors that record their invalidation,
and whose activity they set, and read IsActive() and the active and inactive entries of the registries.
They count no call of an internal method.
"""

import contextlib
import unittest

from collections.abc import Callable
from typing import Any
from unittest import mock

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Collection import ArrayCollection, ArrayList, CreateList
from WinCopies.Collections.Circular import CircularList
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Registry import IObjectMonitor, IActivationObject, IActivatableMonitor
from WinCopies.Collections.Registry.Core import CollectionRegistry
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import IFunction

_CORE: str = "WinCopies.Collections.Registry.Core"

class _Monitor(Abstract, IActivatableMonitor):
    """A monitor that records its invalidation, and may act then, once. Its invalidation empties it, as
    it empties a registry, so that it is inactive from then on, until the bench activates it again
    through the activation object it received."""

    def __init__(self, name: str, log: list[str], active: bool = False, action: Callable[[], object]|None = None) -> None:
        super().__init__()

        self.__name: str = name
        self.__log: list[str] = log
        self.__active: bool = active
        self.__action: Callable[[], object]|None = action
        self.__activation: IActivationObject|None = None

    def InvalidateObjects(self) -> None:
        action: Callable[[], object]|None = self.__action

        self.__log.append(self.__name)
        self.__active = False
        self.__action = None

        if action is not None: action()

    def IsActive(self) -> bool: return self.__active

    def _SetActivationObject(self, activationObject: IActivationObject) -> None: self.__activation = activationObject

    def Activate(self) -> None:
        activation: IActivationObject|None = self.__activation

        self.__active = True

        if activation is not None: activation.Activate()

def _entries(registry: object) -> tuple[int, int]:
    """The active and the inactive entries of a collection registry, which creates its list of active
    entries once one is needed."""

    def count(items: Any) -> int:
        result: int = 0
        node: Any = None if items is None else items.TryGetFirstNode()

        while node is not None:
            result += 1
            node = node.GetNext()

        return result

    return count(getattr(registry, "_CollectionRegistry__actives")), count(getattr(registry, "_CollectionRegistry__inactives"))

def _source() -> Any: return CreateList([0, 1, 2, 3])

class _Cells(IFunction[int]):
    """Cell initialiser for ArrayList, which takes a provider rather than a sequence."""

    def GetValue(self) -> int: return 0

class _Failure(Exception):
    """The failure of a monitor during its invalidation."""

class TestAWriteReachesOnlyTheActiveMonitors(unittest.TestCase):
    """A write invalidates the active monitors of its collection, and no inactive one: a write that finds
    no active monitor runs nothing (Registre 11 §6, bench 1)."""

    def test_a_write_invalidates_no_inactive_monitor(self) -> None:
        source: Any = _source()
        log: list[str] = []
        monitor: _Monitor = _Monitor("M", log)

        source.GetCollectionMonitors().RegisterMonitor(monitor)
        source.TrySetAt(0, 7)

        self.assertEqual(log, [])

    def test_a_write_invalidates_an_active_monitor(self) -> None:
        source: Any = _source()
        log: list[str] = []
        monitor: _Monitor = _Monitor("M", log, True)

        source.GetCollectionMonitors().RegisterMonitor(monitor)
        source.TrySetAt(0, 7)

        self.assertEqual(log, ["M"])

class TestTheFirstEnumeratorActivatesItsRegistries(unittest.TestCase):
    """An enumerator registers at its start: the first one makes the registry of the enumerators active,
    and the collection registry with it, and a second one changes nothing (Registre 11 §6, bench 2)."""

    def test_the_first_start_activates_the_registries(self) -> None:
        source: Any = _source()
        registries: Any = source._GetCollectionRegistries()
        enumerators: Any = registries.GetEnumeratorRegistry()
        before: tuple[int, int] = _entries(registries)
        enumerator: Any = source.TryGetEnumerator()

        self.assertFalse(enumerators.IsActive(), "an enumerator that did not start made its registry active")
        self.assertFalse(registries.IsActive(), "an enumerator that did not start made the collection registry active")

        enumerator.TryMoveNext()

        self.assertTrue(enumerators.IsActive())
        self.assertTrue(registries.IsActive())
        self.assertEqual(_entries(registries), (before[0] + 1, before[1] - 1))

    def test_a_second_start_changes_nothing(self) -> None:
        source: Any = _source()
        registries: Any = source._GetCollectionRegistries()
        first: Any = source.TryGetEnumerator()

        first.TryMoveNext()

        after: tuple[int, int] = _entries(registries)
        second: Any = source.TryGetEnumerator()

        second.TryMoveNext()

        self.assertEqual(_entries(registries), after)

class TestAnInvalidatedRegistryIsDeactivated(unittest.TestCase):
    """The invalidation empties the registry of the enumerators, which goes among the inactive monitors,
    and the next write does not invalidate a monitor that its invalidation emptied (Registre 11 §6,
    bench 3)."""

    def test_a_write_deactivates_the_registry_of_a_started_enumerator(self) -> None:
        source: Any = _source()
        registries: Any = source._GetCollectionRegistries()
        enumerators: Any = registries.GetEnumeratorRegistry()
        before: tuple[int, int] = _entries(registries)
        enumerator: Any = source.TryGetEnumerator()

        enumerator.TryMoveNext()
        source.TrySetAt(0, 7)

        self.assertFalse(enumerator.TryMoveNext(), "the write did not invalidate the enumerator")
        self.assertFalse(enumerators.IsActive())
        self.assertFalse(registries.IsActive())
        self.assertEqual(_entries(registries), before)

    def test_the_next_write_does_not_invalidate_a_deactivated_monitor(self) -> None:
        source: Any = _source()
        log: list[str] = []
        monitor: _Monitor = _Monitor("M", log, True)

        source.GetCollectionMonitors().RegisterMonitor(monitor)
        source.TrySetAt(0, 7)
        source.TrySetAt(1, 8)

        self.assertEqual(log, ["M"])

class TestAMonitorActivatedDuringAnInvalidationIsReachedByIt(unittest.TestCase):
    """A monitor that becomes active while a write invalidates its collection is invalidated by that
    write, whether the invalidation already passed it or not: it goes at the end of the active monitors,
    which the invalidation drains (Registre 11 §3.4, Registre 12 §5.3, bench 4)."""

    def test_an_inactive_monitor_activated_by_another_one_is_invalidated(self) -> None:
        source: Any = _source()
        log: list[str] = []
        later: _Monitor = _Monitor("B", log)
        first: _Monitor = _Monitor("A", log, True, later.Activate)

        source.GetCollectionMonitors().RegisterMonitor(first)
        source.GetCollectionMonitors().RegisterMonitor(later)
        source.TrySetAt(0, 7)

        self.assertEqual(log, ["A", "B"])

    def test_a_monitor_activated_again_once_invalidated_is_invalidated_again(self) -> None:
        source: Any = _source()
        log: list[str] = []
        passed: _Monitor = _Monitor("B", log, True)
        last: _Monitor = _Monitor("A", log, True, passed.Activate)

        source.GetCollectionMonitors().RegisterMonitor(passed)
        source.GetCollectionMonitors().RegisterMonitor(last)
        source.TrySetAt(0, 7)

        self.assertEqual(log, ["B", "A", "B"])

class TestACircularListActivatesItsSource(unittest.TestCase):
    """The registry of a CircularList is a collection registry registered in that of its source: it asks
    to be active there once one of its own monitors is, so that the activation goes up from one level to
    the next. A write of the source then invalidates the enumerator of the CircularList, and deactivates
    both registries. Without an enumerator, the CircularList stays inactive in its source (Registre 11
    §6, bench 5)."""

    def test_an_enumerator_of_a_circular_list_activates_its_source(self) -> None:
        source: Any = _source()
        circular: Any = CircularList[int](source, 1)
        registries: Any = source._GetCollectionRegistries()
        own: Any = circular._GetCollectionRegistries()
        enumerator: Any = circular.TryGetEnumerator()

        enumerator.TryMoveNext()

        self.assertTrue(own.IsActive())
        self.assertTrue(registries.IsActive(), "the activation did not go up to the source")

        source.TrySetAt(0, 7)

        self.assertFalse(enumerator.TryMoveNext(), "the write of the source did not invalidate the enumerator of the CircularList")
        self.assertFalse(own.IsActive())
        self.assertFalse(registries.IsActive())

    def test_a_circular_list_without_an_enumerator_stays_inactive(self) -> None:
        source: Any = _source()
        circular: Any = CircularList[int](source, 1)
        registries: Any = source._GetCollectionRegistries()
        before: tuple[int, int] = _entries(registries)

        source.TrySetAt(0, 7)

        self.assertFalse(circular._GetCollectionRegistries().IsActive())
        self.assertFalse(registries.IsActive())
        self.assertEqual(_entries(registries), before)

class TestAWriteDuringAnInvalidationIsRefused(unittest.TestCase):
    """A monitor writes to the collection while a write invalidates it, as a callback of a consumer may.
    The collection registry refuses to be invalidated again, so that the nested write raises before it
    changes anything. The outer invalidation reaches every monitor, then raises in turn, before its own
    write changes anything either (Registre 12 §5.2, bench 6)."""

    def test_a_nested_write_is_refused_and_changes_nothing(self) -> None:
        source: Any = _source()
        log: list[str] = []
        writer: _Monitor = _Monitor("W", log, True, lambda: source.TrySetAt(1, 9))

        source.GetCollectionMonitors().RegisterMonitor(writer)

        with self.assertRaises(InvalidOperationError): source.TrySetAt(0, 7)

        self.assertEqual(log, ["W"])
        self.assertEqual((source.GetAt(0), source.GetAt(1)), (0, 1), "a write changed the collection")

    def test_the_collection_can_be_written_to_once_a_write_was_refused(self) -> None:
        source: Any = _source()
        writer: _Monitor = _Monitor("W", [], True, lambda: source.TrySetAt(1, 9))

        source.GetCollectionMonitors().RegisterMonitor(writer)

        with self.assertRaises(InvalidOperationError): source.TrySetAt(0, 7)

        source.TrySetAt(0, 7)

        self.assertEqual(source.GetAt(0), 7)

class TestARemovedInactiveMonitorIsInvalidatedNoMore(unittest.TestCase):
    """A monitor removed while it is inactive is invalidated no more, even once it asks to be active
    again: its entry, emptied by the removal, goes back among the active ones, and the invalidation
    detaches it without invalidating it (D-130, Registre 12 §5.3, bench 8)."""

    def test_a_removed_monitor_that_asks_to_be_active_is_not_invalidated(self) -> None:
        source: Any = _source()
        registries: Any = source._GetCollectionRegistries()
        before: tuple[int, int] = _entries(registries)
        log: list[str] = []
        monitor: _Monitor = _Monitor("M", log)
        handle: IRemovable = source.GetCollectionMonitors().RegisterMonitor(monitor)

        handle.Remove()
        monitor.Activate()
        source.TrySetAt(0, 7)

        self.assertEqual(log, [])
        self.assertEqual(_entries(registries), before, "the invalidation did not detach the entry of the removed monitor")

class TestACollectionRegistryRequiresActivatableMonitors(unittest.TestCase):
    """A monitor that does not implement IActivatableMonitor cannot be registered in a collection
    registry: the checkers refuse it. The refusal is static, so that mypy keeps this bench: in strict
    mode, it reports an ignore comment that silences nothing, so that the comment below would fail its
    run if the constraint went away. pyright honours the comment, but does not report it when it
    silences nothing, in the configuration of the framework (Registre 11 §6, bench 9)."""

    def test_a_plain_object_monitor_is_refused_by_the_checkers(self) -> None:
        registry: CollectionRegistry[IObjectMonitor] = CollectionRegistry[IObjectMonitor]() # type: ignore[type-var]

        self.assertFalse(registry.IsActive())

class TestTheActivationGoesUpEveryLevel(unittest.TestCase):
    """A CircularList over another one, itself over a list: the start of an enumerator of the outer one
    activates the three registries, each asking to be active in the next one, and a write of the source
    invalidates the enumerator and deactivates all three (Registre 13 §2)."""

    def test_an_enumerator_of_the_outer_circular_list_activates_the_three_levels(self) -> None:
        source: Any = _source()
        inner: Any = CircularList[int](source, 1)
        outer: Any = CircularList[int](inner, 1)
        levels: tuple[Any, Any, Any] = (outer._GetCollectionRegistries(), inner._GetCollectionRegistries(), source._GetCollectionRegistries())
        enumerator: Any = outer.TryGetEnumerator()

        enumerator.TryMoveNext()

        self.assertEqual([level.IsActive() for level in levels], [True, True, True])

        source.TrySetAt(0, 7)

        self.assertFalse(enumerator.TryMoveNext(), "the write of the source did not invalidate the enumerator of the outer CircularList")
        self.assertEqual([level.IsActive() for level in levels], [False, False, False])

class TestAnArrayCollectionActivatesItsArray(unittest.TestCase):
    """An ArrayCollection registers its registries in those of the array it wraps: the start of its
    enumerator activates both, and a write of the array invalidates the enumerator and deactivates both
    (Registre 13 §2)."""

    def test_an_enumerator_of_an_array_collection_activates_its_array(self) -> None:
        array: Any = getattr(ArrayList[int](3, _Cells()), "_GetItems")()
        collection: Any = ArrayCollection[int](array)
        levels: tuple[Any, Any] = (collection._GetCollectionRegistries(), array._GetCollectionRegistries())
        enumerator: Any = collection.TryGetEnumerator()

        enumerator.TryMoveNext()

        self.assertEqual([level.IsActive() for level in levels], [True, True])

        array.TrySetAt(0, 5)

        self.assertFalse(enumerator.TryMoveNext(), "the write of the array did not invalidate the enumerator of the ArrayCollection")
        self.assertEqual([level.IsActive() for level in levels], [False, False])

class TestAMonitorThatRaisesLeavesEveryEntryInPlace(unittest.TestCase):
    """A monitor raises during its invalidation. The invalidation still reaches every active monitor,
    then raises in turn, and every entry is where the activity of its monitor says: the registry loses
    none, and is invalidated again by the next write (Registre 13 §2)."""

    def test_the_entry_of_a_monitor_that_raised_goes_among_the_inactive_ones(self) -> None:
        source: Any = _source()
        registries: Any = source._GetCollectionRegistries()
        before: tuple[int, int] = _entries(registries)
        log: list[str] = []
        failing: _Monitor = _Monitor("A", log, True, _raise)
        other: _Monitor = _Monitor("B", log, True)

        source.GetCollectionMonitors().RegisterMonitor(failing)
        source.GetCollectionMonitors().RegisterMonitor(other)

        with self.assertRaises(_Failure): source.TrySetAt(0, 7)

        self.assertEqual(log, ["A", "B"])
        self.assertEqual(_entries(registries), (before[0], before[1] + 2))

        failing.Activate()
        source.TrySetAt(1, 8)

        self.assertEqual(log, ["A", "B", "A"])

    def test_the_entry_of_a_monitor_that_raised_and_stays_active_stays_among_the_active_ones(self) -> None:
        source: Any = _source()
        registries: Any = source._GetCollectionRegistries()
        before: tuple[int, int] = _entries(registries)
        log: list[str] = []
        monitors: list[_Monitor] = []

        def failing() -> None:
            monitors[0].Activate()

            raise _Failure()

        monitors.append(_Monitor("A", log, True, failing))
        source.GetCollectionMonitors().RegisterMonitor(monitors[0])

        with self.assertRaises(_Failure): source.TrySetAt(0, 7)

        self.assertEqual(_entries(registries), (before[0] + 1, before[1]))

        source.TrySetAt(1, 8)

        self.assertEqual(log, ["A", "A"])

def _raise() -> None: raise _Failure()

def _run(bench: type[unittest.TestCase]) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    unittest.defaultTestLoader.loadTestsFromTestCase(bench).run(result)

    return result

def _fell(result: unittest.TestResult) -> int: return len(result.failures) + len(result.errors)

class TestTheRegistryActivityBenchesCanFail(unittest.TestCase):
    """Each bench above is run against the framework rebuilt as it was before the active registries, or
    with one part of them taken out: green on the intact tree, red on the rebuilt one. The bench of the
    checkers has no such control: mypy keeps it."""

    def __AssertFalls(self, bench: type[unittest.TestCase], *patches: Any) -> None:
        self.assertEqual(_fell(_run(bench)), 0, "the bench is expected to pass on the intact tree")

        with contextlib.ExitStack() as stack:
            for patch in patches: stack.enter_context(patch)

            broken: unittest.TestResult = _run(bench)

        self.assertGreater(_fell(broken), 0, "the bench did not fall on the rebuilt tree")

    def test_the_benches_of_the_activity_fall_when_a_write_invalidates_every_monitor(self) -> None:
        """As before the active registries: a write invalidates every monitor registered in the
        collection registry, active or not."""

        def invalidatingAll(self: Any) -> None:
            for items in (getattr(self, "_CollectionRegistry__actives"), getattr(self, "_CollectionRegistry__inactives")):
                node: Any = None if items is None else items.TryGetFirstNode()

                while node is not None:
                    following: Any = node.GetNext()
                    monitor: Any = node.GetValue().TryGetMonitor()

                    if monitor is not None: monitor.InvalidateObjects()

                    node = following

        for bench in (TestAWriteReachesOnlyTheActiveMonitors, TestAnInvalidatedRegistryIsDeactivated):
            with self.subTest(bench = bench.__name__): self.__AssertFalls(bench, mock.patch.object(CollectionRegistry, "InvalidateObjects", invalidatingAll))

    def test_the_benches_of_the_activation_fall_when_an_activation_does_nothing(self) -> None:
        def ignoring(self: Any, entry: Any) -> None: pass

        for bench in (TestTheFirstEnumeratorActivatesItsRegistries, TestAMonitorActivatedDuringAnInvalidationIsReachedByIt, TestACircularListActivatesItsSource, TestTheActivationGoesUpEveryLevel, TestAnArrayCollectionActivatesItsArray):
            with self.subTest(bench = bench.__name__): self.__AssertFalls(bench, mock.patch.object(CollectionRegistry, "_CollectionRegistry__Activate", ignoring))

    def test_the_bench_of_the_deactivation_falls_when_an_invalidated_monitor_stays_active(self) -> None:
        def keeping(self: Any, entry: Any) -> None:
            monitor: Any = entry.TryGetMonitor()

            if monitor is not None:
                try: monitor.InvalidateObjects()
                finally: entry.MoveTo(self._CollectionRegistry__GetAside())

        self.__AssertFalls(TestAnInvalidatedRegistryIsDeactivated, mock.patch.object(CollectionRegistry, "_CollectionRegistry__Invalidate", keeping))

    def test_the_bench_of_the_refusal_falls_without_it(self) -> None:
        def reentrant(self: Any) -> None:
            if self.IsActive(): self._CollectionRegistry__InvalidateObjects()

        self.__AssertFalls(TestAWriteDuringAnInvalidationIsRefused, mock.patch.object(CollectionRegistry, "InvalidateObjects", reentrant))

    def test_the_bench_of_a_raising_monitor_falls_when_its_entry_is_put_back_only_on_success(self) -> None:
        def losing(self: Any, entry: Any) -> None:
            monitor: Any = entry.TryGetMonitor()

            if monitor is not None:
                monitor.InvalidateObjects()

                if entry.TryGetMonitor() is not None: entry.MoveTo(self._CollectionRegistry__GetAside() if monitor.IsActive() else self._CollectionRegistry__inactives)

        self.__AssertFalls(TestAMonitorThatRaisesLeavesEveryEntryInPlace, mock.patch.object(CollectionRegistry, "_CollectionRegistry__Invalidate", losing))

    def test_the_bench_of_the_removal_falls_when_a_removal_does_nothing(self) -> None:
        def leaving(self: Any) -> None: pass

        self.__AssertFalls(TestARemovedInactiveMonitorIsInvalidatedNoMore, mock.patch(f"{_CORE}._MonitorEntry.Remove", leaving))