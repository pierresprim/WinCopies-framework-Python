"""
Unit tests for the invalidation notifier (WinCopies.Collections.Enumeration.Notification).

The notifier holds its subscribers weakly: a subscriber that dies leaves it, removed by a finalizer,
and one that nobody keeps alive is never notified. A subscriber also leaves it through the IRemovable
that Add returns. Either way of leaving is idempotent, and leaving both ways, in either order,
removes it once (Enumeration 6.11 §3).

These benches are deterministic: every subscriber dies between two operations of the notifier,
never during one. A finalizer that runs during a notification or during an addition is the subject
of D-123 and D-124, accepted for now (Registre 1); the benches leave it out, so as neither to depend
on it nor to freeze it. Removing oneself from within a notification is refused for now, and is to
be replaced by a deferred removal.
"""

import gc
import unittest

from collections.abc import Callable
from contextlib import ExitStack
from typing import Any
from unittest import mock

import WinCopies.Collections.Enumeration.Notification as Notification

from WinCopies import Abstract
from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Enumeration.Notification import INotifyCallback, InvalidationNotifier
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Iteration import Iterate
from WinCopies.Collections.Iteration.Traversal import EnumerateSafe
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Object import WeakReferenceFinalizer

class _Subscriber(Abstract, INotifyCallback):
    def __init__(self, name: str, log: list[str], react: Callable[[], object]|None = None) -> None:
        super().__init__()

        self.__name: str = name
        self.__log: list[str] = log
        self.__react: Callable[[], object]|None = react

    def Notify(self, revoke: bool) -> None:
        self.__log.append(self.__name + ("!" if revoke else ""))

        if self.__react is not None: self.__react()

class _Bench:
    """A notifier with named subscribers, which the bench keeps alive until it drops them."""

    def __init__(self, names: str = "") -> None:
        self.notifier: InvalidationNotifier = InvalidationNotifier()
        self.log: list[str] = []
        self.subscribers: dict[str, _Subscriber] = {}
        self.removables: dict[str, IRemovable] = {}

        for name in names: self.Add(name)

    def Add(self, name: str, react: Callable[[], object]|None = None) -> None:
        subscriber: _Subscriber = _Subscriber(name, self.log, react)

        self.subscribers[name] = subscriber
        self.removables[name] = self.notifier.Add(subscriber)

    def Drop(self, names: str) -> None:
        """Releases the subscribers, outside any operation of the notifier."""

        for name in names: del self.subscribers[name]

        gc.collect()

    def Remove(self, names: str) -> None:
        for name in names: self.removables[name].Remove()

    def Notified(self, revoke: bool = False) -> ReadOnlyArray[str]:
        self.log.clear()
        self.notifier.Notify(revoke)

        return tuple(self.log)

_REMOVALS: ReadOnlyArray[str] = ("A", "B", "C", "AB", "BC", "AC", "ABC")
"""The subscribers removed out of A, B, C: at the head, inside, at the tail, and together."""

def _rest(removed: str) -> ReadOnlyArray[str]: return tuple(name for name in "ABC" if name not in removed)

class TestANotifierNotifiesItsSubscribers(unittest.TestCase):
    def test_it_notifies_every_subscriber_in_order_with_the_flag(self) -> None:
        bench: _Bench = _Bench("ABC")

        self.assertEqual(bench.Notified(), ("A", "B", "C"))
        self.assertEqual(bench.Notified(True), ("A!", "B!", "C!"))

    def test_a_notifier_without_subscribers_notifies_nobody(self) -> None:
        self.assertEqual(_Bench().Notified(), ())

    def test_an_exception_reaches_the_caller_once_everyone_is_notified(self) -> None:
        """The notification is safe: an exception does not stop it, and reaches the caller at its
        end, alone, or grouped with the others."""

        def fail() -> None: raise ValueError("fail")

        for failing in ("B", "AC"):
            with self.subTest(failing = failing):
                bench: _Bench = _Bench()

                for name in "ABC": bench.Add(name, fail if name in failing else None)

                with self.assertRaises(ValueError if len(failing) == 1 else ExceptionGroup) as raised: bench.notifier.Notify(False)

                self.assertEqual(tuple(bench.log), ("A", "B", "C"), f"{failing} failing stopped the notification")

                if isinstance(raised.exception, ExceptionGroup): self.assertEqual(len(raised.exception.exceptions), len(failing))

class TestASubscriberLeavesTheNotifier(unittest.TestCase):
    def test_a_removed_subscriber_is_notified_no_more(self) -> None:
        """Through its IRemovable; one added afterwards is notified, after those that remain. Until the
        third version of the notifier, a removal at the head or at the tail lost the others."""

        for removed in _REMOVALS:
            with self.subTest(removed = removed):
                bench: _Bench = _Bench("ABC")

                bench.Remove(removed)

                self.assertEqual(bench.Notified(), _rest(removed))

                bench.Add("D")

                self.assertEqual(bench.Notified(), _rest(removed) + ("D",))

    def test_a_subscriber_that_dies_is_notified_no_more(self) -> None:
        """Removed by the finalizer of its weak reference, between two operations."""

        for dead in _REMOVALS:
            with self.subTest(dead = dead):
                bench: _Bench = _Bench("ABC")

                bench.Drop(dead)

                self.assertEqual(bench.Notified(), _rest(dead))

                bench.Add("D")

                self.assertEqual(bench.Notified(), _rest(dead) + ("D",))

    def test_a_subscriber_nobody_keeps_is_never_notified(self) -> None:
        """The subscription does not keep its subscriber alive: one created in the call to Add dies at
        the end of the statement."""

        log: list[str] = []
        notifier: InvalidationNotifier = InvalidationNotifier()

        notifier.Add(_Subscriber("A", log))
        notifier.Notify(False)

        self.assertEqual(log, [])

class TestLeavingTwiceLeavesOnce(unittest.TestCase):
    """Each way of leaving removes the subscriber once, whatever happened before. When the notifier
    empties, it hands over to an empty one; a removal that came late used to act on the notifier it
    replaced, and to replace the one in use in turn, losing its subscribers."""

    def test_removing_again_changes_nothing(self) -> None:
        for removed, again in (("A", "A"), ("AB", "B"), ("ABC", "C")):
            with self.subTest(removed = removed, again = again):
                bench: _Bench = _Bench("ABC")

                bench.Remove(removed)
                bench.Add("D")
                bench.Remove(again)

                self.assertEqual(bench.Notified(), _rest(removed) + ("D",))

    def test_a_subscriber_removed_then_released_leaves_once(self) -> None:
        for removed in _REMOVALS:
            with self.subTest(removed = removed):
                bench: _Bench = _Bench("ABC")

                bench.Remove(removed)
                bench.Add("D")
                bench.Drop(removed)

                self.assertEqual(bench.Notified(), _rest(removed) + ("D",))

    def test_a_subscriber_released_then_removed_leaves_once(self) -> None:
        for dead in _REMOVALS:
            with self.subTest(dead = dead):
                bench: _Bench = _Bench("ABC")

                bench.Drop(dead)
                bench.Add("D")
                bench.Remove(dead)

                self.assertEqual(bench.Notified(), _rest(dead) + ("D",))

class TestANotificationRefusesChanges(unittest.TestCase):
    """While it notifies, the notifier refuses to be changed or notified again by a subscriber: the
    refusal is raised in that subscriber, and reaches the caller once everyone is notified. The
    notifier stays as it was."""

    def __assertRefused(self, label: str, change: Callable[[_Bench], object], expected: ReadOnlyArray[str]) -> None:
        bench: _Bench = _Bench("A")
        fired: bool = False

        def once() -> None:
            nonlocal fired

            if not fired:
                fired = True

                change(bench)

        bench.Add("B", once)
        bench.Add("C")

        with self.assertRaises(InvalidOperationError, msg = f"{label} from a subscriber was not refused"): bench.notifier.Notify(False)

        self.assertEqual(tuple(bench.log), ("A", "B", "C"), f"{label} from a subscriber stopped the notification")
        self.assertEqual(bench.Notified(), expected, f"{label} from a subscriber changed the notifier")

    def test_adding_is_refused(self) -> None: self.__assertRefused("Add", lambda bench: bench.Add("N"), ("A", "B", "C"))
    def test_removing_through_the_removable_is_refused(self) -> None: self.__assertRefused("Remove", lambda bench: bench.Remove("C"), ("A", "B", "C"))
    def test_notifying_again_is_refused(self) -> None: self.__assertRefused("Notify", lambda bench: bench.notifier.Notify(True), ("A", "B", "C"))

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheNotifierBenchesCanFail(unittest.TestCase):
    """The benches above, run against the defects of the earlier versions of the notifier (Enumeration
    6.11 §3.2): green on the intact module, red on the rebuilt one, and red on their assertions rather
    than on an error. The private classes of the module are reached by name."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any], alsoRebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]] = ()) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact module")

        with ExitStack() as patches:
            for other, members in ((target, rebuilt),) + alsoRebuilt: patches.enter_context(mock.patch.multiple(other, **members))

            broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")
        self.assertEqual(broken.errors, [], f"{name} fell on an error rather than on its assertions")

    def test_the_removal_bench_falls_when_the_node_is_unlinked_before_the_count(self) -> None:
        """As in the first version: the node was unlinked before the notifier updated its head and its
        tail, which then read links already cleared."""

        node: type = getattr(Notification, "_Node")
        remove: Callable[[Any, Callable[[], None]], None] = getattr(node, "Remove")

        def unlinkedFirst(self: Any, action: Callable[[], None]) -> None:
            remove(self, lambda: None)
            action()

        for name in ("test_a_removed_subscriber_is_notified_no_more", "test_a_subscriber_that_dies_is_notified_no_more"):
            with self.subTest(bench = name): self.__assertFalls(TestASubscriberLeavesTheNotifier, name, node, {"Remove": unlinkedFirst})

    def test_the_twice_benches_fall_without_the_idempotence_that_holds_them(self) -> None:
        """Each order of leaving twice is held by its own idempotence, rebuilt away as in the version
        that lacked it. Throughout, the notifier updates its head and its tail on every removal of a
        node, even one already removed, as until the seventh version:
        - released, then removed: nothing else, as in the fifth and sixth versions;
        - removed, then released: the finalizer is also left attached by the removal, as in the second
          version, and in the fifth for the last node;
        - removed twice: the IRemovable also forwards every call, as in the third version."""

        node: type = getattr(Notification, "_Node")
        notifier: type = getattr(Notification, "_InvalidationNotifier")
        removable: type = getattr(notifier, "_Removable")
        remove: Callable[[Any, Callable[[], None]], None] = getattr(node, "Remove")
        initialize: Callable[[Any, Any, Any], None] = getattr(removable, "__init__")

        def countedAlways(self: Any, action: Callable[[], None]) -> None:
            action()
            remove(self, lambda: None)

        class Attached[T](WeakReferenceFinalizer[T]):
            def __init__(self, obj: T, action: Callable[[], None]) -> None: super().__init__(obj, action)

            def Remove(self) -> None: pass

        def keeping(self: Any, owner: Any, node: Any) -> None:
            initialize(self, owner, node)

            setattr(self, "_rebuilt", (owner, node))

        def forwarding(self: Any) -> None:
            owner, node = getattr(self, "_rebuilt")

            getattr(owner, "_OnNodeRemoved")(node, True)

        cases: ReadOnlyArray[tuple[str, ReadOnlyArray[tuple[Any, dict[str, Any]]]]] = (
            ("test_a_subscriber_released_then_removed_leaves_once", ()),
            ("test_a_subscriber_removed_then_released_leaves_once", ((Notification, {"WeakReferenceFinalizer": Attached}),)),
            ("test_removing_again_changes_nothing", ((removable, {"__init__": keeping, "Remove": forwarding}),)))

        for name, others in cases:
            with self.subTest(bench = name): self.__assertFalls(TestLeavingTwiceLeavesOnce, name, node, {"Remove": countedAlways}, others)

    def test_the_weak_benches_fall_when_the_subscribers_are_held_strongly(self) -> None:
        """A notifier that keeps its subscribers alive: neither dying nor being dropped would end a
        subscription. The weak reference of each node is rebuilt as a strong one."""

        class Strong[T]:
            def __init__(self, obj: T, action: Callable[[], None]) -> None: self.__obj: T|None = obj
            def TryGetValue(self) -> T|None: return self.__obj
            def Remove(self) -> None: self.__obj = None

        for bench, name in ((TestASubscriberLeavesTheNotifier, "test_a_subscriber_that_dies_is_notified_no_more"), (TestASubscriberLeavesTheNotifier, "test_a_subscriber_nobody_keeps_is_never_notified")):
            with self.subTest(bench = name): self.__assertFalls(bench, name, Notification, {"WeakReferenceFinalizer": Strong})

    def test_the_refusal_benches_fall_without_the_monitor(self) -> None:
        """A notification that does not hold the monitor, which a change or another notification then
        enters."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")

        def unguarded(self: Any, revoke: bool) -> None:
            first: Any = getattr(self, "_InvalidationNotifier__first")

            def following(node: Any) -> Any: return node.GetNext()
            def notify(node: Any) -> None: node.Notify(revoke)

            EnumerateSafe(Iterate(lambda: first, following), notify, True)

        for name in ("test_adding_is_refused", "test_removing_through_the_removable_is_refused", "test_notifying_again_is_refused"):
            with self.subTest(bench = name): self.__assertFalls(TestANotificationRefusesChanges, name, notifier, {"Notify": unguarded})

if __name__ == '__main__': unittest.main()
