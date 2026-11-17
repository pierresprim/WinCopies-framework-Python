"""
Unit tests for the invalidation notifier (WinCopies.Collections.Enumeration.Notification).

The notifier holds its subscribers weakly: a subscriber that dies leaves it, removed by a finalizer,
and one that nobody keeps alive is never notified. A subscriber also leaves it through the IRemovable
that Add returns, at any time, even during a notification. Either way of leaving is idempotent, and
leaving both ways, in either order, removes it once (Enumeration 6.11 §3).

A removal never happens in the middle of an operation of the notifier (Enumeration 6.22): one that
arrives during an addition or a notification, through the IRemovable or by a finalizer, is applied
once the operation is over, even when a subscriber raised. A subscriber removed during a
notification is notified no more, not even by the rest of the notification in progress: only the
unlinking of its node waits. The notifier hands over to an empty one when the removal of its last
subscriber is applied, hence never during a notification. Adding to the notifier and notifying it
again during a notification are still refused.

These benches are deterministic. A subscriber dies either between two operations of the notifier,
or during a notification by the fall of a reference count, which runs its finalizer at a known
point: during its own notification in the bench of D-123, or before its turn. In the notifier, D-123
to D-125 are closed by the transactional removal. The benches still place no pass of the garbage
collector inside an operation; benches that inject one are left for later, in the register of
defects.
"""

import gc
import unittest

from collections.abc import Callable, Iterable
from contextlib import ExitStack
from typing import Any
from unittest import mock
from weakref import ReferenceType, ref

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

    def Dropping(self, names: str) -> Callable[[], object]:
        """A reaction by which a subscriber releases subscribers during a notification, itself or
        others: the bench drops the only strong reference it keeps to them. Each of them dies at once,
        by the fall of its reference count, except the subscriber that reacts, which dies once the call
        that notifies it has returned."""

        def drop() -> None:
            for name in names: self.subscribers.pop(name, None)

        return drop

    def Remove(self, names: Iterable[str]) -> None:
        for name in names: self.removables[name].Remove()

    def Removing(self, names: str, then: Callable[[], object]|None = None) -> Callable[[], object]:
        """A reaction by which a subscriber removes subscribers through their IRemovable during a
        notification, itself or others, and then runs then, if given."""

        def remove() -> None:
            self.Remove(names)

            if then is not None: then()

        return remove

    def Notified(self, revoke: bool = False) -> ReadOnlyArray[str]:
        self.log.clear()
        self.notifier.Notify(revoke)

        return tuple(self.log)

_REMOVALS: ReadOnlyArray[str] = ("A", "B", "C", "AB", "BC", "AC", "ABC")
"""The subscribers removed out of A, B, C: at the head, inside, at the tail, and together."""

def _rest(removed: str) -> ReadOnlyArray[str]: return tuple(name for name in "ABC" if name not in removed)

def _provider(notifier: InvalidationNotifier) -> object:
    """The notifier in use behind an InvalidationNotifier, a private member: an empty one, or one that
    holds nodes."""

    return getattr(notifier, "_InvalidationNotifier__notifierProvider")

_EMPTY: type = getattr(Notification, "_DefaultInvalidationNotifier")

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

    def test_a_notification_goes_on_past_a_subscriber_that_dies_during_it(self) -> None:
        """D-123 (Registre 1): the subscriber releases itself during its own notification, and is then
        held only by the notification until the call returns. Its finalizer then runs, before the
        notification reads the next node: until f9f28d99, the removal it made cleared that link, and
        the notification stopped there; since the transactional removal, that removal waits for the
        end of the notification. The finalizer runs by the fall of a reference count, not by a pass of
        the garbage collector."""

        for dying in _REMOVALS:
            with self.subTest(dying = dying):
                bench: _Bench = _Bench()

                for name in "ABC": bench.Add(name, bench.Dropping(name) if name in dying else None)

                self.assertEqual(bench.Notified(), ("A", "B", "C"))
                self.assertEqual(bench.Notified(), _rest(dying))

                bench.Add("D")

                self.assertEqual(bench.Notified(), _rest(dying) + ("D",))

class TestASubscriberLeavesWithinItsNotification(unittest.TestCase):
    """A subscriber leaves during a notification through its IRemovable, used by itself or by another
    subscriber, or by dying. The removal is not refused, unlike an addition or a nested notification
    (TestANotificationRefusesChanges): it waits for the end of the notification, which goes on with
    the others. The subscriber is notified no more from its removal on, not even by the rest of the
    notification in progress."""

    def test_a_subscriber_that_removes_itself_is_notified_no_more(self) -> None:
        """Through its IRemovable, during its own notification: it is notified this time, and no more.
        One added afterwards is notified, after those that remain."""

        for leaving in _REMOVALS:
            with self.subTest(leaving = leaving):
                bench: _Bench = _Bench()

                for name in "ABC": bench.Add(name, bench.Removing(name) if name in leaving else None)

                self.assertEqual(bench.Notified(), ("A", "B", "C"))
                self.assertEqual(bench.Notified(), _rest(leaving))

                bench.Add("D")

                self.assertEqual(bench.Notified(), _rest(leaving) + ("D",))

    def test_a_subscriber_removed_by_another_is_notified_no_more(self) -> None:
        """B removes, through their IRemovable, A, whose turn has come, C, whose turn has not, or both.
        The removal is not refused, and C is not notified even by the notification in progress: its
        node is neutralized at once, and only its unlinking waits for the end of the notification."""

        for removed, notified in (("A", ("A", "B", "C")), ("C", ("A", "B")), ("AC", ("A", "B"))):
            with self.subTest(removed = removed):
                bench: _Bench = _Bench("A")

                bench.Add("B", bench.Removing(removed))
                bench.Add("C")

                try: first: ReadOnlyArray[str] = bench.Notified()
                except InvalidOperationError: self.fail(f"removing {removed} from a subscriber was refused")

                self.assertEqual(first, notified)
                self.assertEqual(bench.Notified(), _rest(removed))

                bench.Add("D")

                self.assertEqual(bench.Notified(), _rest(removed) + ("D",))

    def test_a_subscriber_that_dies_before_its_turn_is_not_notified(self) -> None:
        """A, notified first, releases it during the notification, and its finalizer runs at once, by
        the fall of a reference count. It has left once the notification is over: the notifier empties
        when the others leave. In the bench of D-123, a subscriber dies during its own notification
        instead."""

        for dying in ("B", "C", "BC"):
            with self.subTest(dying = dying):
                bench: _Bench = _Bench()

                bench.Add("A", bench.Dropping(dying))
                bench.Add("B")
                bench.Add("C")

                self.assertEqual(bench.Notified(), _rest(dying))

                bench.Remove(_rest(dying))

                self.assertIs(type(_provider(bench.notifier)), _EMPTY, f"the notifier still holds the node of {dying}")

    def test_a_notifier_left_by_all_its_subscribers_hands_over_to_an_empty_one_once_the_notification_is_over(self) -> None:
        """Its subscribers remove themselves through their IRemovable during the notification, and each
        of them still finds the notifier in use once removed. Once the notification is over, the
        notifier has handed over to an empty one if none of them remains, as when they leave outside a
        notification or die (TestLeavingTwiceLeavesOnce); otherwise, it does so once the others leave,
        which shows that the nodes removed during the notification were unlinked. Nothing observable
        tells an empty notifier apart from one left holding removed nodes, which still notifies and
        adds: the bench reads the private member that holds the notifier in use."""

        for names, leaving in (("A", "A"), ("AB", "AB"), ("ABC", "ABC"), ("ABC", "AC"), ("ABC", "B")):
            with self.subTest(names = names, leaving = leaving):
                bench: _Bench = _Bench()
                found: list[object] = []

                for name in names: bench.Add(name, bench.Removing(name, lambda: found.append(_provider(bench.notifier))) if name in leaving else None)

                inUse: object = _provider(bench.notifier)

                bench.Notified()

                self.assertEqual(len(found), len(leaving))

                for notifier in found: self.assertIs(notifier, inUse, "the notifier handed over during the notification")

                staying: str = "".join(name for name in names if name not in leaving)

                if staying:
                    self.assertIsNot(type(_provider(bench.notifier)), _EMPTY)

                    bench.Remove(staying)

                self.assertIs(type(_provider(bench.notifier)), _EMPTY)

    def test_a_removal_is_applied_even_when_a_subscriber_raises(self) -> None:
        """A and B remove themselves through their IRemovable during the notification, and one of them
        raises: the exception reaches the caller once the removals are applied, and the notifier has
        handed over to an empty one."""

        def fail() -> None: raise ValueError("fail")

        for raising in "AB":
            with self.subTest(raising = raising):
                bench: _Bench = _Bench()

                for name in "AB": bench.Add(name, bench.Removing(name, fail if name == raising else None))

                with self.assertRaises(ValueError): bench.notifier.Notify(False)

                self.assertIs(type(_provider(bench.notifier)), _EMPTY, f"{raising} raising kept the removals from being applied")

    def test_a_notifier_subscribed_to_another_stays_when_its_subscribers_leave(self) -> None:
        """Subscribed through AsCallback(): its subscribers remove themselves through their IRemovable
        during a notification of the other notifier, which goes on notifying the one that remains, and
        one added once all of them left."""

        for leaving in ("X", "XY"):
            with self.subTest(leaving = leaving):
                relay: _Bench = _Bench()

                for name in "XY": relay.Add(name, relay.Removing(name) if name in leaving else None)

                source: InvalidationNotifier = InvalidationNotifier()

                source.Add(relay.notifier.AsCallback())
                source.Notify(False)

                self.assertEqual(tuple(relay.log), ("X", "Y"))

                relay.Add("Z")
                relay.log.clear()
                source.Notify(False)

                self.assertEqual(tuple(relay.log), tuple(name for name in "XY" if name not in leaving) + ("Z",))

class TestLeavingTwiceLeavesOnce(unittest.TestCase):
    """Each way of leaving removes the subscriber once, whatever happened before. When the notifier
    empties, it hands over to an empty one; a removal that came late used to act on the notifier it
    replaced, and to replace the one in use in turn, losing its subscribers. The IRemovable now holds
    its notifier weakly: one that has handed over is freed, and a removal that comes late finds
    nothing to act on."""

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

    def test_a_notifier_that_handed_over_is_freed_though_the_removables_are_kept(self) -> None:
        """Its subscribers die while the bench keeps their IRemovable, unused. Until the IRemovable held
        its notifier weakly, it kept alive, until its first call, the notifier that had handed over, with
        the last node it held (Enumeration 6.23 §4)."""

        bench: _Bench = _Bench("AB")
        held: ReferenceType[object] = ref(_provider(bench.notifier))

        bench.Drop("AB")

        self.assertIs(type(_provider(bench.notifier)), _EMPTY)
        self.assertIsNone(held(), "the notifier that handed over is still alive")

class TestANotificationRefusesChanges(unittest.TestCase):
    """While it notifies, the notifier refuses to be added to or notified again by a subscriber: the
    refusal is raised in that subscriber, and reaches the caller once everyone is notified. The
    notifier stays as it was. A removal is not refused, but waits for the end of the notification
    (TestASubscriberLeavesWithinItsNotification)."""

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
    def test_notifying_again_is_refused(self) -> None: self.__assertRefused("Notify", lambda bench: bench.notifier.Notify(True), ("A", "B", "C"))

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheNotifierBenchesCanFail(unittest.TestCase):
    """The benches above, run against the defects of the earlier versions of the notifier (Enumeration
    6.11 §3.2, the versions reviewed before f9f28d99, and the notifier before the transactional
    removal), and against defects that the transactional removal could have had (Enumeration 6.22):
    green on the intact module, red on the rebuilt one, and red on their assertions rather than on an
    error. The private classes of the module are reached by name."""

    @staticmethod
    def __strongly() -> dict[str, Any]:
        """An IRemovable that holds its notifier strongly, as until it held it weakly."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")
        removable: type = getattr(notifier, "_Removable")

        def strongly(self: Any, node: Any) -> Any: return removable(lambda: self, node)

        return {"_InvalidationNotifier__CreateRemovable": strongly}

    @staticmethod
    def __unguarded(notifier: Any, revoke: bool) -> None:
        """A notification that does not hold the monitor, which an addition or another notification
        then enters, and during which a removal is applied at once."""

        first: Any = getattr(notifier, "_InvalidationNotifier__first")

        def following(node: Any) -> Any: return node.GetNext()
        def notify(node: Any) -> None: node.Notify(revoke)

        EnumerateSafe(Iterate(lambda: first, following), notify, True)

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any], alsoRebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]] = ()) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact module")

        with ExitStack() as patches:
            for other, members in ((target, rebuilt),) + alsoRebuilt: patches.enter_context(mock.patch.multiple(other, **members))

            broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")
        self.assertEqual(broken.errors, [], f"{name} fell on an error rather than on its assertions")

    def test_the_removal_bench_falls_when_the_node_is_unlinked_before_the_count(self) -> None:
        """As in the first version: the node was unlinked before the notifier updated its head and its
        tail, which then read links already cleared. Since f9f28d99, the removal keeps the link to the
        next node, and the rebuilt defect shows at the tail only."""

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
        - released, then removed: the IRemovable also holds its notifier strongly, as until it held it
          weakly, and nothing else, as in the fifth and sixth versions; otherwise, the notifier that
          handed over once all of them left is freed, and the late removal finds nothing to act on;
        - removed, then released: the finalizer is also left attached by the removal, as in the second
          version, and in the fifth for the last node;
        - removed twice: the IRemovable also forwards every call to the notifier it holds strongly, as
          in the third version."""

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

            setattr(self, "_rebuilt", (owner(), node))

        def forwarding(self: Any) -> None:
            owner, node = getattr(self, "_rebuilt")

            getattr(owner, "_OnNodeRemoved")(node, True)

        cases: ReadOnlyArray[tuple[str, ReadOnlyArray[tuple[Any, dict[str, Any]]]]] = (
            ("test_a_subscriber_released_then_removed_leaves_once", ((notifier, self.__strongly()),)),
            ("test_a_subscriber_removed_then_released_leaves_once", ((Notification, {"WeakReferenceFinalizer": Attached}),)),
            ("test_removing_again_changes_nothing", ((removable, {"__init__": keeping, "Remove": forwarding}),)))

        for name, others in cases:
            with self.subTest(bench = name): self.__assertFalls(TestLeavingTwiceLeavesOnce, name, node, {"Remove": countedAlways}, others)

    def test_the_freeing_bench_falls_when_the_removable_holds_its_notifier_strongly(self) -> None:
        """As until the IRemovable held its notifier weakly."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")

        self.__assertFalls(TestLeavingTwiceLeavesOnce, "test_a_notifier_that_handed_over_is_freed_though_the_removables_are_kept", notifier, self.__strongly())

    def test_the_weak_benches_fall_when_the_subscribers_are_held_strongly(self) -> None:
        """A notifier that keeps its subscribers alive: neither dying nor being dropped would end a
        subscription. The weak reference of each node is rebuilt as a strong one."""

        class Strong[T]:
            def __init__(self, obj: T, action: Callable[[], None]) -> None: self.__obj: T|None = obj
            def TryGetValue(self) -> T|None: return self.__obj
            def Remove(self) -> None: self.__obj = None

        benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]] = (
            (TestASubscriberLeavesTheNotifier, "test_a_subscriber_that_dies_is_notified_no_more"),
            (TestASubscriberLeavesTheNotifier, "test_a_subscriber_nobody_keeps_is_never_notified"),
            (TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_that_dies_before_its_turn_is_not_notified"))

        for bench, name in benches:
            with self.subTest(bench = name): self.__assertFalls(bench, name, Notification, {"WeakReferenceFinalizer": Strong})

    def test_the_refusal_benches_fall_without_the_monitor(self) -> None:
        """A notification that does not hold the monitor."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")

        for name in ("test_adding_is_refused", "test_notifying_again_is_refused"):
            with self.subTest(bench = name): self.__assertFalls(TestANotificationRefusesChanges, name, notifier, {"Notify": self.__unguarded})

    def test_the_going_on_benches_fall_when_a_removal_is_immediate_and_clears_the_next(self) -> None:
        """Two defects together: a notification that does not hold the monitor, so that a removal
        during it is applied at once, as a removal by a finalizer was until the transactional removal;
        and a removal that clears the link of the node to the next one, which the notification reads
        once the call that removed it has returned, as until f9f28d99. Either of them alone leaves the
        benches green."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")
        node: type = getattr(Notification, "_Node")
        remove: Callable[[Any, Callable[[], Any]], Any] = getattr(node, "Remove")

        def cleared(self: Any, action: Callable[[], Any]) -> Any:
            result: Any = remove(self, action)

            setattr(self, "_Node__next", None)

            return result

        benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]] = (
            (TestASubscriberLeavesTheNotifier, "test_a_notification_goes_on_past_a_subscriber_that_dies_during_it"),
            (TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_that_removes_itself_is_notified_no_more"))

        for bench, name in benches:
            with self.subTest(bench = name): self.__assertFalls(bench, name, node, {"Remove": cleared}, ((notifier, {"Notify": self.__unguarded}),))

    def test_the_removal_by_another_bench_falls_without_the_neutralization(self) -> None:
        """A removal during a notification that only waits for its end: the subscriber removed before
        its turn is notified by the rest of the notification."""

        node: type = getattr(Notification, "_Node")

        def kept(self: Any) -> None: pass

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_removed_by_another_is_notified_no_more", node, {"Neutralize": kept})

    def test_the_removal_by_another_bench_falls_when_the_removal_is_refused_during_a_notification(self) -> None:
        """As before the transactional removal: a removal through the IRemovable took the monitor, which
        the notification held."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")
        onNodeRemoved: Callable[[Any, Any, bool], None] = getattr(notifier, "_OnNodeRemoved")

        def refused(self: Any, node: Any, explicit: bool) -> None:
            if explicit and getattr(self, "_InvalidationNotifier__monitor").IsBusy(): raise InvalidOperationError("The given monitor is already busy.")

            onNodeRemoved(self, node, explicit)

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_removed_by_another_is_notified_no_more", notifier, {"_OnNodeRemoved": refused})

    def test_the_unlinking_benches_fall_when_a_removal_during_an_operation_is_lost(self) -> None:
        """A removal that is applied if it finds the notifier free, and is otherwise dropped rather than
        deferred, after the node is neutralized when the removal is explicit: the node stays linked."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")
        onNodeRemoved: Callable[[Any, Any, bool], None] = getattr(notifier, "_OnNodeRemoved")

        def lost(self: Any, node: Any, explicit: bool) -> None:
            if not getattr(self, "_InvalidationNotifier__monitor").IsBusy(): onNodeRemoved(self, node, explicit)
            elif explicit: node.Neutralize()

        for name in ("test_a_subscriber_that_dies_before_its_turn_is_not_notified", "test_a_notifier_left_by_all_its_subscribers_hands_over_to_an_empty_one_once_the_notification_is_over"):
            with self.subTest(bench = name): self.__assertFalls(TestASubscriberLeavesWithinItsNotification, name, notifier, {"_OnNodeRemoved": lost})

    def test_the_emptying_bench_falls_when_the_drain_does_not_hand_over(self) -> None:
        """A drain that empties the notifier without handing over to an empty one."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")

        def kept(self: Any) -> None: pass

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_notifier_left_by_all_its_subscribers_hands_over_to_an_empty_one_once_the_notification_is_over", notifier, {"_InvalidationNotifier__Update": kept})

    def test_the_emptying_bench_falls_when_the_notifier_hands_over_during_the_notification(self) -> None:
        """A notification that does not hold the monitor, during which the removal of the last
        subscriber is applied at once."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_notifier_left_by_all_its_subscribers_hands_over_to_an_empty_one_once_the_notification_is_over", notifier, {"Notify": self.__unguarded})

    def test_the_raising_bench_falls_when_an_exception_skips_the_drain(self) -> None:
        """An operation that applies the removals that arrived during it only when it returns."""

        notifier: type = getattr(Notification, "_InvalidationNotifier")

        def unprotected(self: Any, func: Callable[[], Any]) -> Any:
            with getattr(self, "_InvalidationNotifier__monitor"):
                result: Any = func()

                getattr(self, "_InvalidationNotifier__Drain")()

            getattr(self, "_InvalidationNotifier__Commit")()

            return result

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_removal_is_applied_even_when_a_subscriber_raises", notifier, {"_InvalidationNotifier__Process": unprotected})

    def test_the_relay_bench_falls_when_the_callback_is_the_notifier_in_use(self) -> None:
        """A notifier that hands out the notifier it uses, itself a callback, rather than a callback
        that forwards to it: the hand-over to an empty one, once all its subscribers left, ends its
        subscription to the other notifier."""

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_notifier_subscribed_to_another_stays_when_its_subscribers_leave", InvalidationNotifier, {"AsCallback": _provider})

if __name__ == '__main__': unittest.main()
