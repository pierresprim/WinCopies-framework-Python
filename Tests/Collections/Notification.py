"""
Unit tests for the invalidation notifier (WinCopies.Collections.Enumeration.Notification).

The notifier holds its subscribers weakly: a subscriber that dies leaves it, removed by a finalizer,
and one that nobody keeps alive is never notified. A subscriber also leaves it through the IRemovable
that Add returns, at any time, even during a notification. Either way of leaving is idempotent, and
leaving both ways, in either order, removes it once (Enumeration 6.11 §3).

The notifier is one object for its whole life, which holds a list of subscribers that can be empty,
and no operation of it happens in the middle of another (Enumeration 6.22 and 6.24). An addition, a
removal through the IRemovable, or a notification that arrives during an operation is not refused:
it waits in a queue, which the operation plays in the order of arrival once it is over, even when a
subscriber raised. A subscriber that dies leaves through a purge that its finalizer requests, by a
flag, and that the finalizer makes itself if no operation is in progress, or the operation in
progress once it is over (Registre 5). An addition creates the subscription at once, and
only the linking of its node waits: a subscriber added during a notification is not notified by it.
A subscriber removed through its IRemovable is notified no more, not even by the notification in
progress, nor by one that waits in the queue, an exception to the order of arrival: only the
unlinking of its node waits. The exceptions that the subscribers raise during an operation,
including in the notifications it plays from the queue, reach its caller at its end.

These benches are deterministic. A subscriber dies either between two operations of the notifier,
or during a notification by the fall of a reference count, which runs its finalizer at a known
point: during its own notification in the bench of D-123, or before its turn. In the notifier, D-123
to D-125 are closed by the transactional removal, and D-126 by the single notifier. The benches
still place no pass of the garbage collector inside an operation; benches that inject one, among
which that of D-126, are left for later, in the register of defects. A subscriber that requests a
notification at each of its notifications would make the notifier loop forever: the reactions that
request one fire once.
"""

import gc
import unittest

from collections import deque
from collections.abc import Callable, Iterable
from contextlib import ExitStack
from typing import Any, cast
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
from WinCopies.Typing.Extensions import ExceptionGroupBuilder
from WinCopies.Typing.Monitoring import IMonitor, TryDoWork

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

def _once(action: Callable[[], object]) -> Callable[[], object]:
    """A reaction that runs action at its first call only."""

    fired: bool = False

    def react() -> None:
        nonlocal fired

        if not fired:
            fired = True

            action()

    return react

def _ends(notifier: InvalidationNotifier) -> tuple[object, object]:
    """The head and the tail of the list of a notifier, private members, both None when the list is
    empty. Nothing observable tells an empty list apart from one left holding removed nodes, which
    notify nobody."""

    return getattr(notifier, "_InvalidationNotifier__first"), getattr(notifier, "_InvalidationNotifier__last")

def _messages(exception: BaseException) -> ReadOnlyArray[str]:
    """The messages of an exception, or of the exceptions of a group, in order."""

    if not isinstance(exception, BaseExceptionGroup): return (str(exception),)

    return tuple(str(e) for e in cast(BaseExceptionGroup[BaseException], exception).exceptions)

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
    subscriber, or by dying. The removal is not refused: like an addition or a notification during a
    notification (TestANotificationDefersChanges), it waits for the end of the notification, which
    goes on with the others. The subscriber is notified no more from its removal on, not even by the
    rest of the notification in progress."""

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
        the fall of a reference count. It has left once the notification is over: the list of the
        notifier is empty once the others leave, which the bench reads on its head and its tail,
        private members. In the bench of D-123, a subscriber dies during its own notification
        instead."""

        for dying in ("B", "C", "BC"):
            with self.subTest(dying = dying):
                bench: _Bench = _Bench()

                bench.Add("A", bench.Dropping(dying))
                bench.Add("B")
                bench.Add("C")

                self.assertEqual(bench.Notified(), _rest(dying))

                bench.Remove(_rest(dying))

                self.assertEqual(_ends(bench.notifier), (None, None), f"the notifier still holds the node of {dying}")

    def test_a_notifier_left_by_all_its_subscribers_is_empty_once_the_notification_is_over(self) -> None:
        """Its subscribers remove themselves through their IRemovable during the notification, and each
        of them finds the list unchanged once removed. Once the notification is over, the list is empty
        if none of them remains; otherwise, it empties once the others leave, which shows that the
        nodes removed during the notification were unlinked. Nothing observable tells an empty list
        apart from one left holding removed nodes, which notify nobody: the bench reads the head and the
        tail of the list, private members."""

        for names, leaving in (("A", "A"), ("AB", "AB"), ("ABC", "ABC"), ("ABC", "AC"), ("ABC", "B")):
            with self.subTest(names = names, leaving = leaving):
                bench: _Bench = _Bench()
                found: list[tuple[object, object]] = []

                for name in names: bench.Add(name, bench.Removing(name, lambda: found.append(_ends(bench.notifier))) if name in leaving else None)

                ends: tuple[object, object] = _ends(bench.notifier)

                bench.Notified()

                self.assertEqual(len(found), len(leaving))

                for removed in found: self.assertEqual(removed, ends, "the list changed during the notification")

                staying: str = "".join(name for name in names if name not in leaving)

                if staying:
                    self.assertNotEqual(_ends(bench.notifier), (None, None))

                    bench.Remove(staying)

                self.assertEqual(_ends(bench.notifier), (None, None))

    def test_a_removal_is_applied_even_when_a_subscriber_raises(self) -> None:
        """A and B remove themselves through their IRemovable during the notification, and one of them
        raises: the exception reaches the caller once the removals are applied, and the list of the
        notifier is empty, which the bench reads on its head and its tail, private members."""

        def fail() -> None: raise ValueError("fail")

        for raising in "AB":
            with self.subTest(raising = raising):
                bench: _Bench = _Bench()

                for name in "AB": bench.Add(name, bench.Removing(name, fail if name == raising else None))

                with self.assertRaises(ValueError): bench.notifier.Notify(False)

                self.assertEqual(_ends(bench.notifier), (None, None), f"{raising} raising kept the removals from being applied")

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
    """Each way of leaving removes the subscriber once, whatever happened before. Until the single
    notifier, the notifier handed over to an empty one when it emptied, and a removal that came late
    used to act on the notifier it replaced, and to replace the one in use in turn, losing its
    subscribers. The list now lasts as long as the notifier, and a removed node is never its head or
    its tail again. A node removed again would still unlink itself again, and clear the link of the
    node that followed it to the node before. A notification does not read that link; the removal of
    that node once it is the tail does, and loses the nodes before it: each bench ends by removing
    the subscribers that remain from the tail, one at a time. The IRemovable holds its notifier and
    its node weakly, and keeps neither alive."""

    def __assertUnwinds(self, bench: _Bench, names: ReadOnlyArray[str]) -> None:
        """The subscribers named, the whole list in order, are notified, and the others still are each
        time the last one leaves."""

        for count in range(len(names), 0, -1):
            self.assertEqual(bench.Notified(), names[:count])

            bench.Remove(names[count - 1])

        self.assertEqual(bench.Notified(), ())

    def test_removing_again_changes_nothing(self) -> None:
        for removed, again in (("A", "A"), ("B", "B"), ("AB", "B"), ("ABC", "C")):
            with self.subTest(removed = removed, again = again):
                bench: _Bench = _Bench("ABC")

                bench.Remove(removed)
                bench.Add("D")
                bench.Remove(again)

                self.__assertUnwinds(bench, _rest(removed) + ("D",))

    def test_a_subscriber_removed_then_released_leaves_once(self) -> None:
        for removed in _REMOVALS:
            with self.subTest(removed = removed):
                bench: _Bench = _Bench("ABC")

                bench.Remove(removed)
                bench.Add("D")
                bench.Drop(removed)

                self.__assertUnwinds(bench, _rest(removed) + ("D",))

    def test_a_subscriber_released_then_removed_leaves_once(self) -> None:
        for dead in _REMOVALS:
            with self.subTest(dead = dead):
                bench: _Bench = _Bench("ABC")

                bench.Drop(dead)
                bench.Add("D")
                bench.Remove(dead)

                self.__assertUnwinds(bench, _rest(dead) + ("D",))

    def test_a_notifier_is_freed_though_its_removables_are_kept(self) -> None:
        """Its owner drops it, then its subscribers die, while the bench keeps their IRemovable, unused.
        The finalizer of a subscriber holds the notifier as long as the subscriber lives, and the
        notifier is freed once they are gone. Until the IRemovable held its notifier weakly, it kept it
        alive until its first call (Enumeration 6.23 §4)."""

        bench: _Bench = _Bench("AB")
        held: ReferenceType[InvalidationNotifier] = ref(bench.notifier)

        del bench.notifier

        bench.Drop("AB")

        self.assertIsNone(held(), "the notifier is still alive")

class TestANotificationDefersChanges(unittest.TestCase):
    """During a notification, a subscriber can add to the notifier, remove from it, and notify it
    again. Nothing is refused: each change waits in the queue of the notifier, and is played once the
    notification is over, in the order of arrival, on the list as it is then. The exception is a
    removal through the IRemovable: it neutralizes the node at once, and only its unlinking waits
    (Enumeration 6.24, annotations)."""

    def __notified(self, bench: _Bench, change: str) -> ReadOnlyArray[str]:
        """The notification of the bench, a refusal of the change from a subscriber failing the bench."""

        try: return bench.Notified()
        except InvalidOperationError: self.fail(f"{change} from a subscriber was refused")

    def test_a_subscriber_added_during_a_notification_is_notified_from_the_next_one(self) -> None:
        """B adds N during the notification: its subscription is made at once, and only the linking of
        its node waits for the end of the notification, which does not notify it. The next one does,
        after the others."""

        bench: _Bench = _Bench("A")

        bench.Add("B", _once(lambda: bench.Add("N")))
        bench.Add("C")

        self.assertEqual(self.__notified(bench, "Add"), ("A", "B", "C"))
        self.assertEqual(bench.Notified(), ("A", "B", "C", "N"))

    def test_a_notification_requested_during_a_notification_is_played_after_it(self) -> None:
        """B notifies the notifier of a revocation during the notification: the revocation waits for
        the end of the notification, which goes on with C, and then reaches every subscriber."""

        bench: _Bench = _Bench("A")

        bench.Add("B", _once(lambda: bench.notifier.Notify(True)))
        bench.Add("C")

        self.assertEqual(self.__notified(bench, "Notify"), ("A", "B", "C", "A!", "B!", "C!"))

    def test_the_changes_requested_during_a_notification_are_played_in_the_order_of_arrival(self) -> None:
        """During the notification, A removes itself, B adds D, and C requests a revocation, then adds
        E. The revocation reaches D, added before it was requested, and not E, added after; A, removed
        before, receives nothing. The next notification finds the subscribers in the order in which
        they were added."""

        bench: _Bench = _Bench()

        def revokeThenAdd() -> None:
            bench.notifier.Notify(True)
            bench.Add("E")

        bench.Add("A", bench.Removing("A"))
        bench.Add("B", _once(lambda: bench.Add("D")))
        bench.Add("C", _once(revokeThenAdd))

        self.assertEqual(self.__notified(bench, "A change"), ("A", "B", "C", "B!", "C!", "D!"))
        self.assertEqual(bench.Notified(), ("B", "C", "D", "E"))

    def test_a_subscriber_removed_once_a_notification_waits_is_not_notified_by_it(self) -> None:
        """During the notification, B requests a revocation, then C removes A through its IRemovable.
        The revocation was queued before the removal, and still does not reach A: the removal
        neutralizes the node at once, a written exception to the order of arrival (Enumeration 6.24,
        annotations)."""

        bench: _Bench = _Bench("A")

        bench.Add("B", _once(lambda: bench.notifier.Notify(True)))
        bench.Add("C", _once(bench.Removing("A")))

        self.assertEqual(self.__notified(bench, "A change"), ("A", "B", "C", "B!", "C!"))
        self.assertEqual(bench.Notified(), ("B", "C"))

    def test_a_subscriber_added_then_removed_during_a_notification_is_never_notified(self) -> None:
        """During the notification, B adds N, then removes it through its IRemovable, before its node is
        linked. N is notified by nothing, and once the notification is over, its node is not left in
        the list: the list empties once the others leave, which the bench reads on its head and its
        tail, private members."""

        bench: _Bench = _Bench("A")

        def addThenRemove() -> None:
            bench.Add("N")
            bench.Remove("N")

        bench.Add("B", _once(addThenRemove))

        self.assertEqual(self.__notified(bench, "A change"), ("A", "B"))
        self.assertEqual(bench.Notified(), ("A", "B"))

        bench.Remove("AB")

        self.assertEqual(_ends(bench.notifier), (None, None), "the notifier still holds the node of N")

    def test_the_exceptions_of_a_deferred_notification_reach_the_caller_with_its_own(self) -> None:
        """C raises at each of its notifications, and B requests a revocation during the notification.
        The exception that C raises in the revocation, played from the queue, reaches the caller of the
        notification once everything is played, grouped after the one C raised in the notification."""

        bench: _Bench = _Bench("A")

        def fail() -> None: raise ValueError(bench.log[-1])

        bench.Add("B", _once(lambda: bench.notifier.Notify(True)))
        bench.Add("C", fail)

        with self.assertRaises(Exception) as raised: bench.notifier.Notify(False)

        self.assertEqual(tuple(bench.log), ("A", "B", "C", "A!", "B!", "C!"))
        self.assertEqual(_messages(raised.exception), ("C", "C!"))

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheNotifierBenchesCanFail(unittest.TestCase):
    """The benches above, run against the defects of the earlier versions of the notifier (Enumeration
    6.11 §3.2, the versions reviewed before f9f28d99, the notifier before the transactional removal,
    and the notifier before the single notifier), and against defects that the transactional removal,
    the single notifier and the request of a purge could have had (Enumeration 6.22 and 6.24, Registre
    5): green on the intact module, red on the rebuilt one, and red on their assertions rather than on
    an error. The private classes and members of the module are reached by name."""

    @staticmethod
    def __strongly(held: type) -> dict[str, Any]:
        """An IRemovable that holds strongly, rather than weakly, what is an instance of held: its
        notifier with InvalidationNotifier, as until 1c67be61, and its node too with object, as until
        f9f28d99. Add makes the weak references of the IRemovable through the ref of the module."""

        def strongly(obj: object) -> Callable[[], object]: return (lambda: obj) if isinstance(obj, held) else ref(obj)

        return {"ref": strongly}

    @staticmethod
    def __unguarded(notifier: Any, revoke: bool) -> None:
        """A notification that does not hold the monitor, which an addition, a removal or another
        notification then enters at once."""

        first: Any = getattr(notifier, "_InvalidationNotifier__first")

        def following(node: Any) -> Any: return node.GetNext()
        def notify(node: Any) -> None: node.Notify(revoke)

        EnumerateSafe(Iterate(lambda: first, following), notify, True)

    @staticmethod
    def __refusing(operation: str) -> dict[str, Any]:
        """The operation of the notifier named, Add or Notify, refused while the monitor is held, as
        until the single notifier."""

        original: Callable[..., Any] = getattr(InvalidationNotifier, operation)

        def refused(self: Any, *args: Any) -> Any:
            if getattr(self, "_InvalidationNotifier__monitor").IsBusy(): raise InvalidOperationError("The given monitor is already busy.")

            return original(self, *args)

        return {operation: refused}

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any], alsoRebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]] = ()) -> None:
        """Runs the bench on the intact module, then on the rebuilt one, once the garbage of the runs
        before is collected: a subscriber of theirs that died meanwhile would run its finalizer on the
        rebuilt module."""

        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact module")

        gc.collect()

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
        that lacked it, and by that of the node, rebuilt away throughout: the node runs its whole
        removal again on every call, and unlinks itself again, which no version did. This control used
        to rebuild instead a notifier that updated its head and its tail on every removal of a node,
        even one already removed, as until the seventh version: with a single list, a removed node is
        never its head or its tail, and that defect is harmless.
        - released, then removed: the IRemovable also holds its notifier and its node strongly, as
          until f9f28d99; otherwise, the node is freed once removed, and the late removal finds nothing
          to act on;
        - removed, then released: no longer rebuilt. Until the request of a purge, the finalizer
          removed its own node, and this order was held by the removal, which detached the finalizer,
          rebuilt away by a finalizer left attached, as in the second version, and in the fifth for the
          last node. The finalizer now only requests a purge, which reads the list: a node removed
          before its subscriber dies is never reached again, and no idempotence holds this order
          (Registre 5);
        - removed twice: the IRemovable also forwards every call, and holds its notifier and its node
          strongly, as in the third version."""

        node: type = getattr(Notification, "_Node")
        removable: type = getattr(Notification, "_Removable")
        initializeNode: Callable[..., None] = getattr(node, "__init__")
        initializeRemovable: Callable[[Any, Callable[[], None]], None] = getattr(removable, "__init__")

        def keepingItsRemoval(self: Any, action: Any, finalizerProvider: Any) -> None:
            initializeNode(self, action, finalizerProvider)

            setattr(self, "_rebuilt", getattr(self, "_Node__remove"))

        def removedAlways(self: Any, action: Callable[[], Any]) -> Any: return getattr(self, "_rebuilt")(action)

        def keeping(self: Any, action: Callable[[], None]) -> None:
            initializeRemovable(self, action)

            setattr(self, "_rebuilt", action)

        def forwarding(self: Any) -> None: getattr(self, "_rebuilt")()

        cases: ReadOnlyArray[tuple[str, ReadOnlyArray[tuple[Any, dict[str, Any]]]]] = (
            ("test_a_subscriber_released_then_removed_leaves_once", ((Notification, self.__strongly(object)),)),
            ("test_removing_again_changes_nothing", ((Notification, self.__strongly(object)), (removable, {"__init__": keeping, "Remove": forwarding}))))

        for name, others in cases:
            with self.subTest(bench = name): self.__assertFalls(TestLeavingTwiceLeavesOnce, name, node, {"__init__": keepingItsRemoval, "Remove": removedAlways}, others)

    def test_the_freeing_bench_falls_when_the_removable_holds_its_notifier_strongly(self) -> None:
        """As until the IRemovable held its notifier weakly."""

        self.__assertFalls(TestLeavingTwiceLeavesOnce, "test_a_notifier_is_freed_though_its_removables_are_kept", Notification, self.__strongly(InvalidationNotifier))

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

    def test_the_deferral_benches_fall_without_the_monitor(self) -> None:
        """A notification that does not hold the monitor: an addition or another notification during
        it is applied at once."""

        for name in ("test_a_subscriber_added_during_a_notification_is_notified_from_the_next_one", "test_a_notification_requested_during_a_notification_is_played_after_it"):
            with self.subTest(bench = name): self.__assertFalls(TestANotificationDefersChanges, name, InvalidationNotifier, {"Notify": self.__unguarded})

    def test_the_deferral_benches_fall_when_the_refusal_is_back(self) -> None:
        """As until the single notifier: an addition or a notification that finds the monitor held is
        refused."""

        benches: ReadOnlyArray[tuple[str, str]] = (
            ("test_a_subscriber_added_during_a_notification_is_notified_from_the_next_one", "Add"),
            ("test_a_notification_requested_during_a_notification_is_played_after_it", "Notify"))

        for name, operation in benches:
            with self.subTest(bench = name): self.__assertFalls(TestANotificationDefersChanges, name, InvalidationNotifier, self.__refusing(operation))

    def test_the_renotification_bench_falls_when_a_deferred_notification_is_dropped(self) -> None:
        """A notification that runs if it finds the monitor free, and is otherwise dropped rather than
        queued."""

        notify: Callable[[Any, bool], None] = getattr(InvalidationNotifier, "Notify")

        def dropped(self: Any, revoke: bool) -> None:
            if not getattr(self, "_InvalidationNotifier__monitor").IsBusy(): notify(self, revoke)

        self.__assertFalls(TestANotificationDefersChanges, "test_a_notification_requested_during_a_notification_is_played_after_it", InvalidationNotifier, {"Notify": dropped})

    def test_the_order_bench_falls_when_the_queue_is_played_last_in_first_out(self) -> None:
        """A queue that hands out the operation that arrived last: the revocation is played after the
        addition of E and before that of D."""

        class Lifo[T](deque[T]):
            def popleft(self) -> T: return self.pop()

        self.__assertFalls(TestANotificationDefersChanges, "test_the_changes_requested_during_a_notification_are_played_in_the_order_of_arrival", Notification, {"deque": Lifo})

    def test_the_going_on_benches_fall_when_a_removal_is_immediate_and_clears_the_next(self) -> None:
        """Two defects together: a notification that does not hold the monitor, so that a removal
        during it is applied at once, as a removal by a finalizer was until the transactional removal;
        and a removal that clears the link of the node to the next one, which the notification reads
        once the call that removed it has returned, as until f9f28d99. Either of them alone leaves the
        benches green."""

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
            with self.subTest(bench = name): self.__assertFalls(bench, name, node, {"Remove": cleared}, ((InvalidationNotifier, {"Notify": self.__unguarded}),))

    def test_the_removal_benches_fall_without_the_neutralization(self) -> None:
        """A removal during a notification that only waits for its turn in the queue: the subscriber
        removed before its turn is notified by the rest of the notification, and the one removed once a
        notification waits is notified by it."""

        node: type = getattr(Notification, "_Node")

        def kept(self: Any) -> None: pass

        benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]] = (
            (TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_removed_by_another_is_notified_no_more"),
            (TestANotificationDefersChanges, "test_a_subscriber_removed_once_a_notification_waits_is_not_notified_by_it"))

        for bench, name in benches:
            with self.subTest(bench = name): self.__assertFalls(bench, name, node, {"Neutralize": kept})

    def test_the_removal_by_another_bench_falls_when_the_removal_is_refused_during_a_notification(self) -> None:
        """As before the transactional removal: a removal through the IRemovable took the monitor, which
        the notification held."""

        remove: Callable[[Any, Any], None] = getattr(InvalidationNotifier, "_InvalidationNotifier__Remove")

        def refused(self: Any, node: Any) -> None:
            if getattr(self, "_InvalidationNotifier__monitor").IsBusy(): raise InvalidOperationError("The given monitor is already busy.")

            remove(self, node)

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_removed_by_another_is_notified_no_more", InvalidationNotifier, {"_InvalidationNotifier__Remove": refused})

    def test_the_unlinking_benches_fall_when_a_removal_during_an_operation_is_lost(self) -> None:
        """A removal that is applied if it finds the notifier free, and is otherwise lost rather than
        deferred: the node stays linked. A finalizer that finds the monitor held loses its request of a
        purge, which the holder of the monitor then does not see, while a finalizer that finds the
        monitor free still purges; the subscriber that dies before its turn leaves that way. A removal
        through the IRemovable is dropped once the node is neutralized; the other benches leave that
        way. Until the request of a purge, the finalizer removed its node through the same path as the
        IRemovable, and one rebuilt removal stood for both (Registre 5)."""

        remove: Callable[[Any, Any], None] = getattr(InvalidationNotifier, "_InvalidationNotifier__Remove")

        def requestLost(self: Any, name: str, value: Any) -> None:
            if not (name == "_InvalidationNotifier__mustPurge" and value and getattr(self, "_InvalidationNotifier__monitor").IsBusy()): object.__setattr__(self, name, value)

        def removalLost(self: Any, node: Any) -> None:
            if not getattr(self, "_InvalidationNotifier__monitor").IsBusy(): remove(self, node)
            else: node.Neutralize()

        benches: ReadOnlyArray[tuple[type[unittest.TestCase], str, dict[str, Any]]] = (
            (TestASubscriberLeavesWithinItsNotification, "test_a_subscriber_that_dies_before_its_turn_is_not_notified", {"__setattr__": requestLost}),
            (TestASubscriberLeavesWithinItsNotification, "test_a_notifier_left_by_all_its_subscribers_is_empty_once_the_notification_is_over", {"_InvalidationNotifier__Remove": removalLost}),
            (TestANotificationDefersChanges, "test_a_subscriber_added_then_removed_during_a_notification_is_never_notified", {"_InvalidationNotifier__Remove": removalLost}))

        for bench, name, rebuilt in benches:
            with self.subTest(bench = name): self.__assertFalls(bench, name, InvalidationNotifier, rebuilt)

    def test_the_emptying_bench_falls_when_the_list_keeps_its_head_once_empty(self) -> None:
        """A removal of the last node that clears the tail of the list and not its head, which nothing
        observable shows: the next addition replaces the head."""

        def headKept(self: Any, node: Any) -> None:
            def update() -> None:
                if node is getattr(self, "_InvalidationNotifier__last"): setattr(self, "_InvalidationNotifier__last", node.GetPrevious())
                elif node is getattr(self, "_InvalidationNotifier__first"): setattr(self, "_InvalidationNotifier__first", node.GetNext())

            node.Remove(update)

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_notifier_left_by_all_its_subscribers_is_empty_once_the_notification_is_over", InvalidationNotifier, {"_InvalidationNotifier__Unlink": headKept})

    def test_the_emptying_bench_falls_when_the_list_changes_during_the_notification(self) -> None:
        """A notification that does not hold the monitor, during which the removals are applied at
        once."""

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_notifier_left_by_all_its_subscribers_is_empty_once_the_notification_is_over", InvalidationNotifier, {"Notify": self.__unguarded})

    def test_the_raising_benches_fall_when_the_exceptions_are_raised_before_the_queue_is_played(self) -> None:
        """An operation that raises the exceptions of the subscribers once it is done, before it plays
        the queue, which it then leaves to the next operation: the removals and the notification that
        arrived during it are not applied, and the exceptions of the notification are not grouped with
        its own."""

        def early(self: Any, operation: Callable[[Callable[[Exception], None]], None]) -> None:
            queue: deque[Callable[[Callable[[Exception], None]], None]] = getattr(self, "_InvalidationNotifier__queue")
            monitor: IMonitor = getattr(self, "_InvalidationNotifier__monitor")
            exceptions: ExceptionGroupBuilder = ExceptionGroupBuilder()

            def drain() -> None:
                while len(queue) > 0: queue.popleft()(exceptions.Push)

            if monitor.IsBusy():
                queue.append(operation)

                return

            with monitor:
                operation(exceptions.Push)
                exceptions.TryThrow()
                drain()

            while len(queue) > 0 and TryDoWork(monitor, drain): pass

            exceptions.TryThrow()

        benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]] = (
            (TestASubscriberLeavesWithinItsNotification, "test_a_removal_is_applied_even_when_a_subscriber_raises"),
            (TestANotificationDefersChanges, "test_the_exceptions_of_a_deferred_notification_reach_the_caller_with_its_own"))

        for bench, name in benches:
            with self.subTest(bench = name): self.__assertFalls(bench, name, InvalidationNotifier, {"_InvalidationNotifier__Process": early})

    def test_the_exceptions_bench_falls_when_a_deferred_operation_loses_its_exceptions(self) -> None:
        """An operation that arrives while the monitor is held is queued with a collector that drops the
        exceptions of the subscribers: those of the notification played from the queue are lost."""

        process: Callable[[Any, Callable[[Callable[[Exception], None]], None]], None] = getattr(InvalidationNotifier, "_InvalidationNotifier__Process")

        def losing(self: Any, operation: Callable[[Callable[[Exception], None]], None]) -> None:
            def dropping(_: Callable[[Exception], None]) -> None: operation(lambda exception: None)

            process(self, dropping if getattr(self, "_InvalidationNotifier__monitor").IsBusy() else operation)

        self.__assertFalls(TestANotificationDefersChanges, "test_the_exceptions_of_a_deferred_notification_reach_the_caller_with_its_own", InvalidationNotifier, {"_InvalidationNotifier__Process": losing})

    def test_the_relay_bench_falls_when_the_callback_is_not_kept(self) -> None:
        """A notifier that hands out a new callback at each call to AsCallback(), rather than the one it
        keeps: the other notifier holds it weakly, and loses it at once. The control of the hand-over,
        a notifier that handed out the notifier it used, can no longer be written: the notifier uses no
        other one."""

        callback: type = getattr(Notification, "_NotifyCallback")

        def fresh(self: Any) -> Any: return callback(self)

        self.__assertFalls(TestASubscriberLeavesWithinItsNotification, "test_a_notifier_subscribed_to_another_stays_when_its_subscribers_leave", InvalidationNotifier, {"AsCallback": fresh})

if __name__ == '__main__': unittest.main()
