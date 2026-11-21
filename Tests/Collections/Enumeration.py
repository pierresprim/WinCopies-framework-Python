"""
Conformance suite for the `Enumeration.5` model (`EnumeratorBase` /
`AbstractionEnumerator`).

Port of the review harness that settled the iteration and invalidation contract.
Each of its 56 points becomes one test method; a point the harness exercised over
a table keeps that table as `subTest` cases, so a regression names the case
rather than the section.

Three method constraints are inherited from that review and are load-bearing:

  * **a lifetime is never measured through a device that prolongs it** — a
    registrar that stores its cookie keeps the enumerator alive, so the
    collection points run on the real chain, never on a storing test double;
  * **`gc.collect()` before any liveness assertion** — an enumerator sits in a
    cycle through its own invalidation cookie;
  * **an absence is asserted, not left implicit** — `Invalidated` firing no
    specific hook is a clause of the endogenous/exogenous rule, and is checked as
    one so that a later reader does not "repair" it.

Unlike the standalone harness, this module needs no abort-time reporting: each
point is a test method, so a point that dies takes only itself down.

The last three sections are not part of that port, and are proved by benches of
their own that can fail: the opt-in invalidation of 392ead1, which holds who
builds the invalidation machinery, a wrapper and its source (Q12), which holds
what a wrapper reports when its source stops, and which sources it wraps, and the
exit of a with statement, which stops an enumerator and nothing else, and stops
then disposes a cursor.
"""

from __future__ import annotations

import gc
import inspect
import unittest
import weakref

from contextlib import ExitStack
from enum import StrEnum
from typing import Any, Type, cast
from unittest import mock



import WinCopies.Collections.Enumeration.Core as Core
import WinCopies.Collections.Linked.Singly as Singly
import WinCopies.Collections.Linked.Singly.Buffer as Buffer

from WinCopies import Abstract, IDisposable

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import List, CreateList
from WinCopies.Collections.Enumeration import IterationState, IterationResult, IterationData, EnumerationAbortReason, IIterationStatus, IterationStatus
from WinCopies.Collections.Enumeration.Abstraction import AbstractEnumeratorBase, AbstractionEnumerator, Selector, ConverterEnumerator
from WinCopies.Collections.Enumeration import GetNoDataEnumerationStatus, GetIterationInactiveError
from WinCopies.Collections.Enumeration.Disposable import ICursor
from WinCopies.Collections.Enumeration.Core import IEnumerator, IInvalidatableEnumeratorBase, IInvalidatableEnumerator, IDefaultInvalidatableEnumeratorBase, IDefaultInvalidatableEnumerator, EnumeratorAbstract, EnumeratorBase, Iterator, IteratorBase, IEnumeratorBase
from WinCopies.Collections.Enumeration.Extensions import IncrementalEnumerator
# `_Registrar` is internal on purpose: the phantom-entry point below has to build
# the real registry chain, and no public entry point exposes it.
from WinCopies.Collections.Extensions.Enumeration import EnumeratorRegistry, TupleEnumerator, ResumableTupleEnumerator
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Linked.Doubly.Welded import CreateList as CreateDoublyList
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorAbstract
from WinCopies.Collections.Registry import IObjectRegistrar
from WinCopies.Collections.Registry.Collection import _Registrar # pyright: ignore[reportPrivateUsage]
from WinCopies.Collections.Registry.Invalidation import InvalidationRegistrar
from WinCopies.String import GetValueOrDefault, SurroundWith
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Function, Converter
from WinCopies.Typing.Discard import IInvalidatable, BrokenObjectError, DiscardedError, InvalidatedError
from WinCopies.Typing.Monitoring import ThrowMonitorBusyError

# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def _st(e: IEnumerator[int]) -> str:
    """`State/Result` of an enumerator, as a single readable token."""

    state, result = _snap(e)

    return SurroundWith(state, '/', result)

def _data(e: _Base) -> str: return GetValueOrDefault(e.GetStatus().GetData().name, "Null")

def _snap(e: IEnumerator[int]) -> tuple[str, str]:
    status: IIterationStatus = e.GetStatus()

    return (status.GetState().name, status.GetResult().name)

def _drain(e: EnumeratorAbstract[int]) -> None:
    try:
        while e.MoveNext(): pass
    
    except Exception: pass

def _raises(f: Function[Any]) -> BaseException|None:
    """Returns the exception `f` raises, or `None` — the harness idiom that lets
    a point assert the *type* of a refusal instead of merely its occurrence."""
    try:
        f()

        return None

    except BaseException as ex: return ex

def _seq(e: _Base, *acts: Converter[_Base, Any]) -> Any:
    for act in acts:
        try: act(e)
        except Exception: pass

    return e

# ---------------------------------------------------------------------------
# Concrete helpers
# ---------------------------------------------------------------------------

class Action(StrEnum):
    REGISTER = "REGISTER"
    UNREGISTER = "UNREGISTER"

class _Spy(InvalidationRegistrar):
    """One-instance-per-enumeration registrar: a single slot, Set/Unset."""
    def __init__(self, sink: list[str]) -> None:
        super().__init__()

        self.__sink: list[str] = sink
        self.__cookie: IInvalidatable|None = None

    def Register(self, cookie: IInvalidatable) -> None:
        self.__cookie = cookie

        self.__sink.append(Action.REGISTER)

    def Unregister(self) -> None: self.__sink.append(Action.UNREGISTER)

    def Fire(self) -> None: cast(IInvalidatable, self.__cookie).Invalidate()

class _Cookies(InvalidationRegistrar):
    """Registrar that keeps everything it is handed — including beyond
    `Unregister()`, which the contract does not forbid and nothing must make
    dangerous."""
    def __init__(self) -> None:
        super().__init__()

        self.seen: list[IInvalidatable] = []
        self.trace: list[Action] = []

    def Register(self, cookie: IInvalidatable) -> None:
        self.seen.append(cookie)
        self.trace.append(Action.REGISTER)

    def Unregister(self) -> None: self.trace.append(Action.UNREGISTER)

class _Forgets(InvalidationRegistrar):
    """Does not retain the cookie: isolates what the removable itself adds to
    retention. `_Cookies` would not do here — by keeping cookies it holds the
    enumerator alive through a path other than the one under test."""
    def Register(self, cookie: IInvalidatable) -> None: pass
    def Unregister(self) -> None: pass

class _Meddler(InvalidationRegistrar):
    """Tries to mutate the registrar set from the notifications themselves."""
    def __init__(self, enumerator: _Base) -> None:
        super().__init__()

        self.e: _Base = enumerator
        self.node: IRemovable|None = None
        self.onRegister: BaseException|None = None
        self.onUnregister: BaseException|None = None

    def Register(self, cookie: IInvalidatable) -> None: self.onRegister = _raises(lambda: self.e.AddRegistrar(_Cookies()))
    def Unregister(self) -> None: self.onUnregister = _raises(cast(IRemovable, self.node).Remove)

class _Base(EnumeratorBase[int], IDefaultInvalidatableEnumerator[int]):
    """Instrumented enumerator: every hook writes to `sink` with the status read
    *at that point*, and raises when its name is in `raiseIn`."""
    def __init__(self, items: ReadOnlyArray[int]|range, raiseIn: set[str]|None=None, start: bool = True, sink: list[str]|None = None) -> None:
        super().__init__()

        self._items: list[int] = list(items)
        self._i: int = -1
        self._cur: int|None = None

        self.raiseIn: set[str] = set(() if raiseIn is None else raiseIn)
        self.start: bool = start
        self.sink: list[str] = [] if sink is None else sink

    def _t(self, name: str) -> None:
        self.sink.append(f"{name} [{_st(self)}]")

        if name in self.raiseIn: raise RuntimeError(f"boom:{name}")

    def IsResetSupported(self) -> bool: return True

    def _GetCurrent(self) -> int:
        self._t("_GetCurrent")

        return cast(int, self._cur)

    def _MoveNextOverride(self) -> bool:
        self._t(f"_MoveNextOverride#{self._i + 1}")

        self._i += 1

        if self._i < len(self._items):
            self._cur = self._items[self._i]

            return True

        return False

    def _ResetOverride(self) -> bool:
        self._t("_ResetOverride")

        self._i = -1

        return True

    def _Clear(self) -> None:
        self._t("_Clear")

        super()._Clear()

    def _OnStarting(self) -> bool:
        self._t("_OnStarting")

        return self.start

    def _OnCompleted(self) -> None: self._t("_OnCompleted")
    def _OnErrored(self) -> None: self._t("_OnErrored")
    def _OnAborted(self) -> None: self._t("_OnAborted")
    def _OnStopped(self) -> None: self._t("_OnStopped")

    def _OnTerminated(self, completed: bool) -> None:
        self.sink.append(f"_OnTerminated({completed}) [{_st(self)}]")

        if "_OnTerminated" in self.raiseIn: raise RuntimeError("boom:_OnTerminated")

    def _OnEnded(self) -> None: self._t("_OnEnded")

class _FakeStatus(Abstract, IIterationStatus):
    """Synthetic status: the only way to exercise all eight results without
    depending on the paths that produce them."""
    def __init__(self, result: IterationResult, data: IterationData = IterationData.Null) -> None:
        super().__init__()

        self.__result: IterationResult = result
        self.__data: IterationData = data

    def GetState(self): return IterationState.Ended
    def GetResult(self): return self.__result
    def GetData(self): return self.__data

def _build(items: ReadOnlyArray[int], raiseIn: set[str]|None = None, start: bool = True, curBoom: bool = False) -> _Base:
    class _Current(_Base):
        def __init__(self, items: ReadOnlyArray[int], raiseIn: set[str]|None = None, start: bool = True, sink: list[str]|None = None) -> None: super().__init__(items, raiseIn, start, sink)

        def _GetCurrent(self) -> int:
            if curBoom: raise RuntimeError("_GetCurrent")

            return cast(int, self._cur)

    return _Current(items, raiseIn = raiseIn, start = start)

def _invalidated() -> _Base:
    """An enumerator ended by invalidation, through the registrar path."""
    registrar = _Spy([])
    e = _build((1, 2, 3))

    e.AddRegistrar(registrar)
    e.MoveNext()
    registrar.Fire()

    return e

_SPECIFIC = ("_OnCompleted", "_OnStopped", "_OnErrored")

def _fired(sink: list[str]) -> str:
    """The specific hook actually fired — reported, not chosen between two: the
    earlier binary phrasing could not tell `_OnStopped` from *no hook at all*."""
    hits = [name for name in _SPECIFIC if any(line.startswith(name) for line in sink)]

    return " + ".join(hits) if hits else "none"

# ---------------------------------------------------------------------------
# The raise domain, on a synthetic status
# ---------------------------------------------------------------------------
# `MoveNext()` raises on any attempt to resume after a non-classic termination,
# and since the specialisation the raised type names the cause. The domain is
# carried by `TryGetIterationError()` alone: `IsErrored()` has no caller left in
# the framework, so their agreement holds by wording, not by construction.

class TestRaiseDomain(unittest.TestCase):
    """The raise contract, exercised on all eight results at once."""

    def test_is_errored_and_try_get_iteration_error_cover_the_same_domain(self) -> None:
        divergent = [r.name for r in IterationResult
                     if _FakeStatus(r).IsErrored() != (_FakeStatus(r).TryGetIterationError() is not None)]

        self.assertEqual(divergent, [], f"{len(list(IterationResult))} results should agree")

    def test_the_raised_type_names_the_cause(self) -> None:
        expected: dict[IterationResult, Type[InvalidOperationError]] = {
            IterationResult.Faulted: BrokenObjectError,
            IterationResult.Invalidated: InvalidatedError,
            IterationResult.Revoked: InvalidatedError,
            IterationResult.Stopped: InvalidOperationError}

        for result, errorType in expected.items():
            with self.subTest(result = result.name): self.assertIs(type(_FakeStatus(result).TryGetIterationError()), errorType)

    def test_stopped_is_not_a_discard(self) -> None:
        """A stop requested by the consumer does not make the object unusable."""
        self.assertNotIsInstance(_FakeStatus(IterationResult.Stopped).TryGetIterationError(), DiscardedError)

    def test_invalidated_is_a_discard(self) -> None:
        """Invalidation is exogenous: the object has become unusable."""
        self.assertIsInstance(_FakeStatus(IterationResult.Invalidated).TryGetIterationError(), DiscardedError)

    def test_revoked_is_a_discard(self) -> None:
        """Revocation is exogenous: the object has become unusable."""
        self.assertIsInstance(_FakeStatus(IterationResult.Revoked).TryGetIterationError(), DiscardedError)

    def test_all_types_remain_catchable_as_invalid_operation_error(self) -> None:
        """`UnusableError` derives from `InvalidOperationError`: the
        specialisation breaks no existing caller."""
        for result in (IterationResult.Faulted, IterationResult.Invalidated, IterationResult.Revoked, IterationResult.Stopped):
            with self.subTest(result = result.name): self.assertIsInstance(_FakeStatus(result).TryGetIterationError(), InvalidOperationError)

# ---------------------------------------------------------------------------
# The terminal sequence
# ---------------------------------------------------------------------------

class TestTerminalSequence(unittest.TestCase):
    """One completed enumeration, read five ways."""

    def setUp(self) -> None:
        self.sink: list[str] = []

        e = _Base((1, 2), sink = self.sink)

        e.AddRegistrar(_Spy(self.sink))

        _drain(e)

        self.names: list[str] = [line.split(" ")[0] for line in self.sink]

    def _index(self, name: str|Action) -> int: return self.names.index(name if isinstance(name, Action) else name)

    def test_registration_follows_on_starting_and_precedes_the_first_move_next(self) -> None:
        """1.5"""
        self.assertLess(self._index("_OnStarting"), self._index(Action.REGISTER), " < ".join(self.names[:3]))
        self.assertLess(self._index(Action.REGISTER), self._index("_MoveNextOverride#0"), " < ".join(self.names[:3]))

    def test_unregistration_heads_the_terminal_sequence(self) -> None:
        """1.6 — UNREGISTER precedes `_Clear`: the sequence is atomic with
        respect to invalidation."""
        self.assertLess(self._index(Action.UNREGISTER), self._index("_Clear"))

    def test_clear_then_switch_then_specific_then_terminated_then_ended(self) -> None:
        """2.1"""
        order = [self._index(n) for n in ("_Clear", "_OnCompleted", "_OnTerminated(True)", "_OnEnded")]

        self.assertEqual(order, sorted(order),
                         " < ".join(n for n in self.names if n.startswith(("_Clear", "_OnCompleted", "_OnTerminated", "_OnEnded"))))

    def test_clear_runs_in_the_pre_terminal_state(self) -> None:
        """2.2"""
        line = self.sink[self._index("_Clear")]

        self.assertIn("[Started/Running]", line, line)

    def test_notification_hooks_observe_the_terminal_state(self) -> None:
        """2.6"""
        for name in ("_OnCompleted", "_OnTerminated(True)", "_OnEnded"):
            with self.subTest(hook = name): self.assertIn("[Ended/Completed]", self.sink[self._index(name)])

# ---------------------------------------------------------------------------
# Hook attribution — the endogenous/exogenous rule
# ---------------------------------------------------------------------------

def _revoked(e: _Base, sink: list[str]) -> list[str]:
    """Revokes `e` after one step, through the revocator it hands to a registry, as a registry does."""

    registry = _Objects()

    e.Register(registry)
    e.MoveNext()
    registry.objects[0].Invalidate()

    return sink

class TestHookAttribution(unittest.TestCase):
    def test_specific_hooks_including_the_absence_on_invalidated(self) -> None:
        """The deliberate absence on `Invalidated`: `__Invalidate()` is private
        and only registries borrow it, so the implementer is not the party
        addressed by that cause. Asserted so a later reader does not 'fix' it.
        `Revoked` takes the same private path, through the revocator a registry
        holds, and fires no specific hook either (Enumeration 6.14)."""
        cases: ReadOnlyArray[tuple[str, Converter[_Base, Any], str]] = (
            ("Completed", _drain, "_OnCompleted"),
            ("Failed", lambda x: x.MoveNext(), "_OnCompleted"),
            ("Stopped", lambda x: (x.MoveNext(), x.Stop()), "_OnStopped"),
            ("Faulted", lambda x: (x.MoveNext(), cast(Any, setattr(x, "raiseIn", {"_MoveNextOverride#1"})), cast(Any, _drain(x))), "_OnErrored"))

        for label, act, expected in cases:
            with self.subTest(outcome = label):
                sink: list[str] = []
                e = _Base((1, 2), start = label != "Failed", sink = sink)

                try: act(e)
                except Exception: pass

                self.assertEqual(_fired(sink), expected)

        with self.subTest(outcome = "Invalidated"):
            sink = []
            registrar = _Spy(sink)
            e = _Base((1, 2, 3), sink = sink)

            e.AddRegistrar(registrar)
            e.MoveNext()
            registrar.Fire()

            self.assertEqual(_fired(sink), "none")

        with self.subTest(outcome = "Revoked"):
            sink = []
            e = _Base((1, 2, 3), sink = sink)

            self.assertEqual(_fired(_revoked(e, sink)), "none")

    def test_on_aborted_fires_on_the_three_interruptions_and_only_them(self) -> None:
        """§4 — the common treatment of every outcome going through
        `__Terminate`."""
        def getItems() -> ReadOnlyArray[tuple[str, Converter[_Base, Any]]]:
            return (("Completed", _drain),
                    ("Failed", lambda x: x.MoveNext()),
                    ("Stopped", lambda x: (x.MoveNext(), x.Stop())),
                    ("Faulted", lambda x: (x.MoveNext(), cast(Any, setattr(x, "raiseIn", {"_MoveNextOverride#1"})), cast(Any, _drain(x)))))
        
        aborted: dict[str, bool] = {}

        for label, act in getItems():
            sink: list[str] = []
            e = _Base((1, 2), start = label != "Failed", sink = sink)

            try: act(e)
            except Exception: pass

            aborted[label] = any(line.startswith("_OnAborted") for line in sink)

        sink = []
        registrar = _Spy(sink)
        e = _Base((1, 2, 3), sink = sink)

        e.AddRegistrar(registrar)
        e.MoveNext()
        registrar.Fire()

        aborted["Invalidated"] = any(line.startswith("_OnAborted") for line in sink)

        sink = []
        aborted["Revoked"] = any(line.startswith("_OnAborted") for line in _revoked(_Base((1, 2, 3), sink = sink), sink))

        self.assertEqual(aborted, {"Completed": False, "Failed": False,
                                   "Stopped": True, "Faulted": True, "Invalidated": True, "Revoked": True})

# ---------------------------------------------------------------------------
# Fault attribution
# ---------------------------------------------------------------------------

class TestFaultAttribution(unittest.TestCase):
    def test_attribution_table_over_both_source_lengths(self) -> None:
        """3.x — the outcome is the same whatever the `MoveNext()` that reaches
        the terminal sequence."""
        table: ReadOnlyArray[tuple[str, ReadOnlyArray[int], str]] = (("_OnStarting", (), "Ended/Faulted"), ("_MoveNextOverride#0", (1,), "Ended/Faulted"),
                 ("_ResetOverride", (1,), "Ended/Stopped"),
                 ("_Clear", (1,), "Ended/Completed"), ("_OnCompleted", (1,), "Ended/Completed"),
                 ("_OnTerminated", (1,), "Ended/Completed"), ("_OnEnded", (1,), "Ended/Completed"),
                 ("_Clear", (), "Ended/Completed"), ("_OnCompleted", (), "Ended/Completed"),
                 ("_OnTerminated", (), "Ended/Completed"), ("_OnEnded", (), "Ended/Completed"))

        for origin, items, expected in table:
            with self.subTest(origin = origin, length = len(items)):
                e = _Base(items, raiseIn = {origin})

                if origin == "_ResetOverride":
                    e.MoveNext()

                    try: e.TryReset()
                    except Exception: pass

                else: _drain(e)

                self.assertEqual(_st(e), expected)

    def _assertPropagates(self, origin: str) -> None:
        e = _Base((1,), raiseIn = {origin})

        e.MoveNext()

        with self.assertRaises(RuntimeError, msg = "fail-fast"):
            while e.MoveNext(): pass

    def test_a_fault_in_clear_reaches_the_consumer(self) -> None:
        """3.2"""
        self._assertPropagates("_Clear")

    def test_a_fault_in_on_completed_reaches_the_consumer(self) -> None:
        """3.2"""
        self._assertPropagates("_OnCompleted")

    def test_a_fault_in_on_ended_reaches_the_consumer(self) -> None:
        """3.2"""
        self._assertPropagates("_OnEnded")

    def test_notifications_following_a_fault_are_skipped(self) -> None:
        """3.10"""
        sink: list[str] = []

        _drain(_Base((1,), raiseIn = {"_OnCompleted"}, sink = sink))

        self.assertFalse(any(line.startswith("_OnEnded") for line in sink))

    def test_the_faulted_flag_survives_a_classic_termination(self) -> None:
        """3.12 — the only residual path where a fault precedes a classic
        outcome: `_Clear()` and the notification hooks raise *after* the outcome
        is played, hence without bearing on the result."""
        e = _Base((1, 2), raiseIn = {"_Clear"})

        _drain(e)

        self.assertIn("Faulted", _data(e))
        self.assertEqual(_st(e), "Ended/Completed")

    def test_the_faulted_flag_is_monotonic_until_the_next_reset(self) -> None:
        """3.12"""
        e = _Base((1, 2), raiseIn = {"_Clear"})

        _drain(e)

        before = _data(e)
        e.raiseIn = set()

        e.TryReset()

        self.assertIn("Faulted", before)
        self.assertEqual(_data(e), "Null", f"before {before}, after TryReset() {_data(e)}")

    def test_a_move_next_fault_ends_the_enumeration(self) -> None:
        """3.13"""
        e = _Base((1, 2, 3, 4))

        e.MoveNext()

        e.raiseIn = {"_MoveNextOverride#1"}

        try: e.MoveNext()
        except Exception: pass

        self.assertEqual(_st(e), "Ended/Faulted")
        self.assertIn("Faulted", _data(e))

    def test_no_resumption_after_a_move_next_fault(self) -> None:
        """3.13"""
        e = _Base((1, 2, 3, 4))

        e.MoveNext()

        e.raiseIn = {"_MoveNextOverride#1"}

        try: e.MoveNext()
        except Exception: pass

        self.assertIs(e.TryMoveNext(), False)
        self.assertEqual(_st(e), "Ended/Faulted")

    def test_the_terminal_fault_unrolls_its_own_sequence(self) -> None:
        """3.14"""
        sink: list[str] = []
        e = _Base((1, 2, 3), sink = sink)

        e.MoveNext()

        e.raiseIn = {"_MoveNextOverride#1"}

        try: e.MoveNext()
        except Exception: pass

        self.assertEqual([line.split(" ")[0] for line in sink][-5:],
                         ["_Clear", "_OnErrored", "_OnAborted", "_OnTerminated(False)", "_OnEnded"])

    def test_a_fault_in_on_starting_also_closes_the_enumeration(self) -> None:
        """3.15"""
        sink: list[str] = []
        e = _Base((1, 2, 3), raiseIn = {"_OnStarting"}, sink = sink)

        try: e.MoveNext()
        except Exception: pass

        before = _st(e)
        e.raiseIn = set()
        out: list[int] = []

        while e.TryMoveNext(): out.append(e.GetCurrent())

        self.assertEqual(before, "Ended/Faulted")
        self.assertEqual(out, [])
        self.assertEqual(len([line for line in sink if line.startswith("_OnStarting")]), 1)

    def test_try_reset_clears_the_flag_after_a_start_fault(self) -> None:
        """3.17"""
        e = _Base((1, 2, 3), raiseIn = {"_OnStarting"})

        try: e.MoveNext()
        except Exception: pass

        before = _data(e)
        e.raiseIn = set()

        self.assertIs(e.TryReset(), True, f"before {before}")
        self.assertEqual(_data(e), "Null")
        self.assertEqual(_st(e), "Idle/Idle")

    def test_register_and_unregister_stay_paired_on_faulty_paths(self) -> None:
        """3.16"""
        cases: ReadOnlyArray[tuple[str, Converter[_Base, Any]]] = (("advance fault", lambda x: (x.MoveNext(), cast(Any, setattr(x, "raiseIn", {"_MoveNextOverride#1"})), x.MoveNext())),
                 ("start fault then resumption", lambda x: (x.MoveNext(),)))

        for label, act in cases:
            with self.subTest(path = label):
                sink: list[str] = []
                e = _Base((1, 2), raiseIn = {"_OnStarting"} if "start" in label else None, sink = sink)

                e.AddRegistrar(_Spy(sink))

                try: act(e)
                except Exception: pass

                if "start" in label:
                    e.raiseIn = set()

                    _drain(e)

                self.assertEqual(sink.count(Action.REGISTER), sink.count(Action.UNREGISTER))

# ---------------------------------------------------------------------------
# Registrar pairing and the Stop() guard
# ---------------------------------------------------------------------------

class TestRegistrarPairing(unittest.TestCase):
    def test_register_and_unregister_are_paired_never_unset_on_an_empty_slot(self) -> None:
        """§1"""
        cases: ReadOnlyArray[tuple[str, Converter[_Base, Any]]] = (("full enumeration", _drain),
                 ("Stop() while running", lambda x: (x.MoveNext(), x.Stop())),
                 ("Stop() before start", lambda x: x.Stop()),
                 ("start refused", lambda x: x.MoveNext()))

        for label, act in cases:
            with self.subTest(path = label):
                sink: list[str] = []
                e = _Base((1, 2), start = label != "start refused", sink = sink)

                e.AddRegistrar(_Spy(sink))
                act(e)

                self.assertEqual(sink.count(Action.REGISTER), sink.count(Action.UNREGISTER))

    def test_the_stop_guard_passes_on_the_five_combinations(self) -> None:
        """P1"""
        combos: list[tuple[str, str]] = []

        e = _Base((1, 2, 3)); e.Stop(); combos.append(("Idle/Idle", _st(e)))
        e = _Base((1, 2, 3)); e.MoveNext(); e.Stop(); combos.append(("Started/Running", _st(e)))

        e = _Base((1, 2, 3)); e.MoveNext(); e.raiseIn = {"_MoveNextOverride#1"}

        try: e.MoveNext()
        except Exception: pass

        e.raiseIn = set(); e.Stop(); combos.append(("Started/Faulted", _st(e)))

        e = _Base((1,), raiseIn = {"_OnStarting"})

        try: e.MoveNext()
        except Exception: pass

        e.raiseIn = set(); e.Stop(); combos.append(("Idle/Faulted", _st(e)))

        e = _Base((1,)); _drain(e); e.Stop(); combos.append(("Ended/Completed", _st(e)))

        for entry, result in combos:
            with self.subTest(entry = entry): self.assertTrue(result.startswith("Ended"), result)

# ---------------------------------------------------------------------------
# The -ing pair, on the abstraction enumerator
# ---------------------------------------------------------------------------

class TestAbstractionHooks(unittest.TestCase):
    def setUp(self) -> None:
        self.positions: list[str] = []

        positions = self.positions

        class _Abs(AbstractionEnumerator[int, int]):
            def _GetCurrent(self) -> int: return self._GetContainer().GetCurrent()

            def _OnAborting(self, enumerator: IEnumerator[int]) -> None:
                positions.append(f"_OnAborting: container {enumerator.GetStatus().GetState().name}, "
                                 f"wrapper {self.GetStatus().GetState().name}")

            def _OnAbortedOverride(self) -> None:
                positions.append(f"_OnAbortedOverride: container {self._GetContainer().GetStatus().GetState().name}")

        self.Abs = _Abs

    def _assertFramesTheContainerStop(self) -> None:
        self.assertEqual(len(self.positions), 2, " | ".join(self.positions) or "no hook fired")
        self.assertIn("container Started", self.positions[0])
        self.assertIn("container Ended", self.positions[1])

    def test_the_ing_pair_frames_the_container_stop(self) -> None:
        """§4"""
        a = self.Abs(_Base((1, 2, 3)))

        a.MoveNext()
        a.Stop()

        self._assertFramesTheContainerStop()

    def test_the_ing_pair_also_frames_the_stop_on_the_faulty_path(self) -> None:
        """§4"""

        class _AbsBoom(self.Abs): # type: ignore[name-defined, misc]
            def _MoveNextOverride(self) -> bool:
                result: bool = super()._MoveNextOverride()

                if self._GetContainer().GetCurrent() == 2: raise RuntimeError("boom in the wrapper")

                return result

        a: _AbsBoom = _AbsBoom(_Base((1, 2, 3)))

        a.MoveNext()

        try: a.MoveNext()
        except Exception: pass

        self._assertFramesTheContainerStop()

    def test_no_ing_observation_when_the_container_ended_by_itself(self) -> None:
        """§4"""
        inner: _Base = _Base((1, 2, 3))
        a = self.Abs(inner)

        a.MoveNext()

        inner.raiseIn = {"_MoveNextOverride#1"}

        try: a.MoveNext()
        except Exception: pass

        self.assertEqual(len(self.positions), 1, " | ".join(self.positions))
        self.assertTrue(self.positions[0].startswith("_OnAbortedOverride"), self.positions[0])

    def test_no_ing_hook_on_the_endogenous_branch(self) -> None:
        """§4 — conforms to the endogenous/exogenous rule."""
        _drain(self.Abs(_Base((1,))))

        self.assertEqual(self.positions, [])

class TestUnfaultEnvelope(unittest.TestCase):
    def test_the_unfault_envelope_can_no_longer_stack(self) -> None:
        """C6 — stacking the `Unfault` envelope assumed resumption after a fault.
        Resumption having disappeared, the cause is checked to be gone rather
        than the symptom patched.

        Unfault() is public API, offered to consumers that need it. That the framework
        never calls it establishes nothing by itself — its callers would be outside this
        repository. What is asserted here is narrower and is the thing C6 is about: a run
        that faults does not reach it on its own.

        Counting is the only observation available on this route, which is why the patch is
        not a convenience. An exception out of the override terminates the enumerator through
        Abort, leaving the status ended; Unfault only rewrites the result of a *started* one,
        so on this route it would change nothing even if it were called. Its effect cannot be
        asserted here — only its invocation.

        Counting it means assigning over a final method of a concrete class, which both
        checkers reject by design and which no formulation makes type-clean — a string-keyed
        setattr or a cast to Any silences them by hiding the intent rather than declaring it.
        The suppression is kept narrow and named instead.

        The fault is raised on the terminating call, so the run is a full one and a fault
        really happens, and that is asserted before the count: a count of zero over a run
        that never faulted holds whatever the envelope does, which is what this bench used
        to do — the fault was armed after the run had ended, where an ended enumerator never
        re-enters the override.
        """
        calls: int = 0
        original = IterationStatus.Unfault

        def _counting(self: IterationStatus) -> None:
            nonlocal calls

            calls += 1

            return original(self)

        IterationStatus.Unfault = _counting # type: ignore[method-assign, misc]

        self.addCleanup(setattr, IterationStatus, "Unfault", original)

        count: int = 50
        e: _Base = _Base(range(count), {f"_MoveNextOverride#{count}"})

        for _ in range(count + 1):  # the items, then the terminating call, which faults
            try:
                if not e.TryMoveNext(): break

            except Exception: break

        self.assertTrue(e.GetStatus().HasFaulted(), "the run did not fault: the count below would hold either way")
        self.assertEqual(calls, 0, f"{calls} call(s) to Unfault over a faulting run — resumption no longer exists")

    def test_a_fault_on_a_started_run_is_not_undone(self) -> None:
        """C6 again, on the one route where the effect can be asserted instead of the call
        counted — so this bench needs no patch and no suppression.

        Which route that is follows from a rule rather than from a list. Advancement is part
        of the process, so an exception there compromises the process and the enumerator is
        terminated; retrieval is a one-off event, so an exception there is a local incident
        and the run goes on. The flag is kept either way, so that something which did happen
        is not hidden.

        The six sites that fault all follow it, measured. Out of _MoveNextOverride: Abort,
        ended Faulted. Out of _ResetOverride: Stop then Fault twice, ended Stopped, and reset
        refused afterwards. Out of _OnCompleted or _OnStopped: the transition first, then
        Fault on a status it has already ended. Out of _Clear, which runs *during* the
        termination: Fault on a still-started status, but with notify off, so the result is
        left to the Stop that follows. Out of _GetCurrent: Fault alone, notifying, on a
        started status.

        So what singles this route out is not startedness alone — _Clear faults a started
        status too — but startedness and notification together: only here does the result
        actually become Faulted while the run is live, which is the one state Unfault could
        undo. The enumerator then goes on: the next read moves, a later successful GetCurrent
        returns its item, the drain reaches the end. Through all of it the result must stay
        Faulted rather than revert to Running, which is exactly what an Unfault envelope
        would have done. The two axes part company at the end — the run completes, and the
        fault remains in the data.
        """

        e: _Base = _Base(range(5), {"_GetCurrent"})
        status: IIterationStatus = e.GetStatus()

        self.assertTrue(e.TryMoveNext())
        self.assertEqual(status.GetResult(), IterationResult.Running, "the run must be live, or the fault below means nothing")

        self.assertRaises(RuntimeError, e.GetCurrent)

        self.assertEqual(status.GetState(), IterationState.Started, "the fault must not have terminated the run")
        self.assertEqual(status.GetResult(), IterationResult.Faulted)

        e.raiseIn = set()

        self.assertTrue(e.TryMoveNext())
        self.assertEqual(status.GetResult(), IterationResult.Faulted, "moving on undid the fault")

        self.assertEqual(e.GetCurrent(), 1)
        self.assertEqual(status.GetResult(), IterationResult.Faulted, "a successful read undid the fault")

        while e.TryMoveNext(): pass

        self.assertEqual(status.GetResult(), IterationResult.Completed)
        self.assertTrue(status.HasFaulted(), "the fault must survive the completion as data")

# ---------------------------------------------------------------------------
# The invalidation cookie life cycle
# ---------------------------------------------------------------------------
# Three successive defects came out of this area in three passes — a single-use
# cookie, then a cookie with no strong owner, then a cookie never disarmed. The
# settled contract: stable identity for the life of the enumerator, cyclical
# arming. `Register()` arms, `Invalidate()` and `Unregister()` disarm; a cookie
# held beyond its registration has no effect.

class TestInvalidationCookie(unittest.TestCase):
    def test_the_cookie_survives_the_garbage_collector(self) -> None:
        """§D — measured on the real chain, not with `_Cookies`: that registrar
        keeps a strong reference, so it would hold alive the very thing it claims
        to measure. The real registry only observes weakly — which is the whole
        point here."""
        collection = List[int]((1, 2, 3))
        cursor: IEnumerator[int] = collection.TryGetEnumerator()

        cursor.MoveNext()
        gc.collect()
        collection.Add(9)

        self.assertEqual(_st(cursor), "Ended/Invalidated",
                         "without a strong owner, invalidation becomes non-deterministic")

    def test_the_cookie_is_still_reachable_after_a_collection_pass(self) -> None:
        """§D"""
        captured: list[Any] = []

        class _Weak(InvalidationRegistrar):
            def Register(self, cookie: IInvalidatable) -> None: captured.append(weakref.ref(cookie))
            def Unregister(self) -> None: pass

        collection = List((1, 2, 3))
        cursor = collection.TryGetEnumerator()

        cast(IInvalidatableEnumerator[int], cursor).AddRegistrar(_Weak())
        cursor.MoveNext()
        gc.collect()

        self.assertEqual(len(captured), 1)
        self.assertIsNotNone(captured[0](), "the cookie has no strong owner")

    def test_the_registration_invalidation_cycle_holds_over_four_rounds(self) -> None:
        """§D"""
        e: _Base = _Base(range(9))
        spy: _Cookies = _Cookies()

        e.AddRegistrar(spy)

        for index in range(4):
            e.TryReset()
            e.MoveNext()

            with self.subTest(round = index):
                self.assertEqual(_st(e), "Started/Running")

                spy.seen[-1].Invalidate()

                self.assertEqual(_st(e), "Ended/Invalidated")

    def test_stable_identity_cyclical_arming(self) -> None:
        """§D"""
        e = _Base(range(9))
        spy = _Cookies()

        e.AddRegistrar(spy)

        for _ in range(4):
            e.TryReset()
            e.MoveNext()
            spy.seen[-1].Invalidate()

        self.assertEqual(len(spy.seen), 4)
        self.assertEqual(len(set(map(id, spy.seen))), 1, "one cookie instance for the life of the enumerator")

    def test_a_cookie_held_beyond_its_registration_is_inert(self) -> None:
        """§D"""
        cases: ReadOnlyArray[tuple[str, Converter[_Base, object]]] = (("completion", _drain),
                 ("requested stop", lambda x: (x.MoveNext(), x.Stop())),
                 ("advance fault", lambda x: (x.MoveNext(), x.MoveNext())))

        for label, terminate in cases:
            with self.subTest(termination = label):
                e: _Base = _Base((1, 2, 3), raiseIn = {"_MoveNextOverride#1"} if label == "advance fault" else None)
                spy: _Cookies = _Cookies()

                e.AddRegistrar(spy)

                try: terminate(e)
                except Exception: pass

                e.TryReset()
                spy.seen[-1].Invalidate()

                self.assertEqual(_st(e), "Idle/Idle")

    def test_a_refused_start_emits_no_cookie(self) -> None:
        """§D"""
        e: _Base = _Base((1,), start = False)
        spy: _Cookies = _Cookies()

        e.AddRegistrar(spy)
        e.MoveNext()

        self.assertEqual(_st(e), "Ended/Failed")
        self.assertEqual(spy.seen, [])
        self.assertEqual(spy.trace, [])

    def test_the_registrars_of_one_registration_receive_the_same_cookie(self) -> None:
        """§D"""
        e: _Base = _Base((1, 2))
        a, b = _Cookies(), _Cookies()

        e.AddRegistrar(a)
        e.AddRegistrar(b)
        e.MoveNext()

        self.assertEqual(len(a.seen), 1)
        self.assertEqual(len(b.seen), 1)
        self.assertIs(a.seen[0], b.seen[0])

    def test_one_invalidation_unregisters_every_registrar(self) -> None:
        """§D"""
        e = _Base((1, 2))
        a, b = _Cookies(), _Cookies()

        e.AddRegistrar(a)
        e.AddRegistrar(b)
        e.MoveNext()
        a.seen[0].Invalidate()

        self.assertEqual(a.trace, [Action.REGISTER, Action.UNREGISTER])
        self.assertEqual(b.trace, [Action.REGISTER, Action.UNREGISTER])

    def test_register_and_unregister_stay_paired_over_three_full_cycles(self) -> None:
        """§D"""
        e: _Base = _Base((1, 2))
        spy: _Cookies = _Cookies()

        e.AddRegistrar(spy)

        for _ in range(3):
            e.TryReset()
            _drain(e)

        self.assertEqual(spy.trace.count(Action.REGISTER), 3)
        self.assertEqual(spy.trace.count(Action.UNREGISTER), 3)

# ---------------------------------------------------------------------------
# The registrar set is frozen while a registration is in progress
# ---------------------------------------------------------------------------
# Adding or removing an observer of a running protocol is reentrancy in the broad
# sense — the same shape as mutating a collection being enumerated. Both are
# therefore refused, notification window included: that is what makes
# unreachable the phantom entry a mid-iteration removal used to leave in the
# registry.

class TestFrozenRegistrarSet(unittest.TestCase):
    def test_adding_during_a_registration_raises(self) -> None:
        """§E — a late registrar protected nothing and still received the end
        notification."""
        e = _Base((1, 2, 3))

        e.AddRegistrar(_Cookies())
        e.MoveNext()

        self.assertIsInstance(_raises(lambda: e.AddRegistrar(_Cookies())), InvalidOperationError)

    def test_removing_during_a_registration_raises(self) -> None:
        """§E"""
        e = _Base((1, 2, 3))
        node = e.AddRegistrar(_Cookies())

        e.MoveNext()

        self.assertIsInstance(_raises(node.Remove), InvalidOperationError)

    def test_no_phantom_entry_survives_in_the_registry(self) -> None:
        """§E — an accepted removal used to leave an entry that invalidated every
        subsequent iteration."""
        registry = EnumeratorRegistry()
        e = _Base((1, 2, 3))
        node = e.AddRegistrar(_Registrar(
            registry._GetRegistry())) # pyright: ignore[reportPrivateUsage]

        e.MoveNext()

        refused = _raises(node.Remove)

        e.Stop()
        e.TryReset()
        e.MoveNext()

        before = _st(e)

        registry.InvalidateObjects()

        self.assertIsInstance(refused, InvalidOperationError)
        self.assertEqual(before, "Started/Running")
        self.assertEqual(_st(e), "Ended/Invalidated")

    def test_outside_a_registration_removal_is_free_and_idempotent(self) -> None:
        """§E"""
        e = _Base((1, 2))
        a, b, c = _Cookies(), _Cookies(), _Cookies()

        e.AddRegistrar(a)
        node = e.AddRegistrar(b)
        e.AddRegistrar(c)

        self.assertIsNone(_raises(node.Remove))
        self.assertIsNone(_raises(node.Remove))

        e.MoveNext()
        e.Stop()

        self.assertEqual(a.trace, [Action.REGISTER, Action.UNREGISTER])
        self.assertEqual(c.trace, [Action.REGISTER, Action.UNREGISTER])
        self.assertEqual(b.trace, [])

    def test_outside_a_registration_addition_is_free_and_effective_next_cycle(self) -> None:
        """§E"""
        e = _Base((1, 2))

        e.AddRegistrar(_Cookies())
        _drain(e)

        late = _Cookies()

        self.assertIsNone(_raises(lambda: e.AddRegistrar(late)))

        e.TryReset()
        e.MoveNext()

        self.assertEqual(late.trace, [Action.REGISTER])

    def test_mutating_the_set_from_a_notification_raises_on_both_sides(self) -> None:
        """§E"""
        e = _Base((1, 2, 3))
        meddler = _Meddler(e)

        meddler.node = e.AddRegistrar(meddler)

        e.MoveNext()
        e.Stop()

        self.assertIsInstance(meddler.onRegister, InvalidOperationError)
        self.assertIsInstance(meddler.onUnregister, InvalidOperationError)

    def test_the_removable_adds_no_retention(self) -> None:
        """§E — the removable's guard must not create a link back to the
        manager."""
        e = _Base((1, 2))
        kept = e.AddRegistrar(_Forgets())

        e.MoveNext()

        alive = weakref.ref(e)

        del e

        gc.collect()
        gc.collect()

        self.assertIsNone(alive())
        self.assertIsNotNone(kept)

    def test_a_registrar_keeping_its_cookie_holds_the_enumerator_alive(self) -> None:
        """§E — expected: the cookie holds the enumerator strongly. This is not a
        defect but a clause — keeping the cookie is functionally harmless, not
        free in lifetime."""
        e = _Base((1, 2))
        holder = _Cookies()

        e.AddRegistrar(holder)
        e.MoveNext()

        alive = weakref.ref(e)

        del e

        gc.collect()
        gc.collect()

        self.assertIsNotNone(alive())

    def test_pairing_is_total_over_three_cycles_and_two_registrars(self) -> None:
        """§E"""
        e = _Base((1, 2))
        a, b = _Cookies(), _Cookies()

        e.AddRegistrar(a)
        e.AddRegistrar(b)

        for _ in range(3):
            e.TryReset()
            _drain(e)

        self.assertEqual(a.trace, [Action.REGISTER, Action.UNREGISTER] * 3)
        self.assertEqual(b.trace, [Action.REGISTER, Action.UNREGISTER] * 3)

# ---------------------------------------------------------------------------
# The table of valid (state, result) combinations
# ---------------------------------------------------------------------------

_VALID: set[tuple[str, str]] = {
    ("Idle",    "Idle"),        # new; after TryReset() — every fault now closes the enumeration
    ("Started", "Running"),     # in progress; after Unfault() on a resumed read
    ("Started", "Faulted"),     # _GetCurrent() raises — the position has not moved, the read is retryable
    ("Ended",   "Faulted"),     # _MoveNextOverride() raises — the advance may have moved, the iteration is closed
                                # NB: the state says whether the iteration survived the fault (§14.5)
    ("Ended",   "Completed"),   # completion; empty source
    ("Ended",   "Failed"),      # start refused
    ("Ended",   "Stopped"),     # Stop(); _ResetOverride() raising
    ("Ended",   "Invalidated")} # invalidation

_PATHS: list[tuple[str, Function[Any]]] = [
    ("new",                    lambda: _build((1, 2))),
    ("in progress",            lambda: _seq(_build((1, 2)), lambda x: x.MoveNext())),
    ("completion",             lambda: _seq(_build((1, 2)), _drain)),
    ("empty source",           lambda: _seq(_build(()), _drain)),
    ("start refused",          lambda: _seq(_build((1,), start = False), lambda x: x.MoveNext())),
    ("Stop before start",      lambda: _seq(_build((1, 2)), lambda x: x.Stop())),
    ("Stop while running",     lambda: _seq(_build((1, 2, 3)), lambda x: x.MoveNext(), lambda x: x.Stop())),
    ("Stop after the end",     lambda: _seq(_build((1,)), _drain, lambda x: x.Stop())),
    ("TryReset",               lambda: _seq(_build((1, 2)), lambda x: x.MoveNext(), lambda x: x.TryReset())),
    ("_OnStarting fault",      lambda: _seq(_build((1,), {"_OnStarting"}), lambda x: x.MoveNext())),
    ("first MoveNext fault",   lambda: _seq(_build((1,), {"_MoveNextOverride#0"}), lambda x: x.MoveNext())),
    ("later MoveNext fault",   lambda: _seq(_build((1, 2), {"_MoveNextOverride#1"}), lambda x: x.MoveNext(), lambda x: x.MoveNext())),
    ("_Clear fault",           lambda: _seq(_build((1,), {"_Clear"}), _drain)),
    ("notification fault",     lambda: _seq(_build((1,), {"_OnCompleted"}), _drain)),
    ("_ResetOverride fault",   lambda: _seq(_build((1,), {"_ResetOverride"}), lambda x: x.MoveNext(), lambda x: x.TryReset())),
    ("_GetCurrent fault",      lambda: _seq(_build((1, 2), curBoom = True), lambda x: x.MoveNext(), lambda x: x.GetCurrent())),
    ("advance fault",          lambda: _seq(_build((1, 2, 3), {"_MoveNextOverride#1"}),
                                            lambda x: x.MoveNext(), lambda x: x.MoveNext(),
                                            lambda x: setattr(x, "raiseIn", set()), lambda x: x.MoveNext())),
    ("invalidation",           _invalidated)]

class TestStateTable(unittest.TestCase):
    def test_no_path_reaches_a_combination_outside_the_table(self) -> None:
        """§states"""
        for label, factory in _PATHS:
            with self.subTest(path = label):
                self.assertIn(_snap(factory()), _VALID)

    def test_the_eight_valid_combinations_are_all_covered(self) -> None:
        """§states"""
        reached = {_snap(factory()) for _, factory in _PATHS}

        self.assertEqual(reached, _VALID, f"covered {len(reached)}/{len(_VALID)}")

# ---------------------------------------------------------------------------
# The raise, on the real enumeration paths
# ---------------------------------------------------------------------------

def _raised(e: _Base, *args: Any) -> bool|BaseException:
    try: return e.MoveNext(*args)
    except BaseException as ex: return ex

class TestRealPaths(unittest.TestCase):
    def test_move_next_raises_the_expected_type_on_the_three_real_paths(self) -> None:
        """§C"""
        paths = (("invalidation", _invalidated(), InvalidatedError),
                 ("requested stop", _seq(_build((1, 2, 3)), lambda x: x.MoveNext(), lambda x: x.Stop()), InvalidOperationError),
                 ("advance fault", _seq(_build((1, 2), {"_MoveNextOverride#1"}),
                                        lambda x: x.MoveNext(), lambda x: x.MoveNext()), BrokenObjectError))

        for label, e, errorType in paths:
            with self.subTest(path = label):
                self.assertIs(type(_raised(e)), errorType)

    def test_no_classic_termination_raises_failed_included(self) -> None:
        """§C"""
        for label, e in self._classic():
            with self.subTest(path = label):
                self.assertNotIsInstance(_raised(e), BaseException)

    def test_raise_on_completion_raises_stop_iteration_not_an_iteration_error(self) -> None:
        """§C"""
        for label, e in self._classic():
            with self.subTest(path = label):
                self.assertIsInstance(_raised(e, True), StopIteration)

    @staticmethod
    def _classic() -> list[tuple[str, Any]]:
        return [("completion", _seq(_build((1, 2)), _drain)),
                ("empty source", _seq(_build(()), _drain)),
                ("start refused", _seq(_build((1,), start = False), lambda x: x.MoveNext()))]

    def test_has_faulted_keeps_history_and_result_as_two_axes(self) -> None:
        """§C"""
        F, D = IterationResult, IterationData

        table: ReadOnlyArray[tuple[IterationResult, IterationData, bool, bool, bool]] = (
            (F.Faulted, D.Null, True, False, True),
            (F.Invalidated, D.Null, True, False, True),
            (F.Revoked, D.Null, True, False, True),
            (F.Stopped, D.Null, False, False, False),
            (F.Completed, D.Faulted, False, True, True),
            (F.Completed, D.Null, False, False, False))

        for result, data, strict, nonStrict, either in table:
            with self.subTest(result = result.name, data = data.name or "Null"):
                status = _FakeStatus(result, data)

                self.assertEqual((status.HasFaulted(True), status.HasFaulted(False), status.HasFaulted(None)),
                                 (strict, nonStrict, either))


# ---------------------------------------------------------------------------
# Opt-in invalidation
# ---------------------------------------------------------------------------
# Since 392ead1, `EnumeratorBase` builds the invalidation machinery (the managed
# registrar and the revocator) only for an enumerator that declares it through
# `IDefaultInvalidatableEnumeratorBase`; every other one holds a shared null
# component, which refuses both doors. The three benches below hold who opts in,
# what a refusal leaves behind, and that the declaration reaches the members of
# the interface whatever the order of a class's bases.

class _Counter(IncrementalEnumerator[int]):
    """An index enumerator over 0 to n - 1: the layer below the tuple, which declares nothing."""
    def __init__(self, n: int) -> None:
        super().__init__()

        self.__n: int = n

    def _GetMaxValue(self) -> int: return self.__n
    def _GetCurrent(self) -> int: return self._GetValue()

class _Plain(Iterator[int]):
    """A non-invalidatable enumerator that reaches the protected doors, as a subclass may."""
    def __init__(self, items: ReadOnlyArray[int]) -> None: super().__init__(iter(items))

    def AddRegistrarAnyway(self, registrar: InvalidationRegistrar) -> IRemovable: return self._AddRegistrar(registrar)
    def RegisterAnyway(self, registry: IObjectRegistrar[IInvalidatable]) -> None: self._Register(registry)

class _Objects(Abstract, IObjectRegistrar[IInvalidatable]):
    """A registry that keeps what it is handed, so that an absence can be asserted."""
    def __init__(self) -> None:
        super().__init__()

        self.objects: list[IInvalidatable] = []

    def RegisterObject(self, item: IInvalidatable) -> None: self.objects.append(item)

def _allocations(factory: Function[Any]) -> tuple[int, int]:
    """The managed registrars and the revocators that `Core` builds while `factory` runs."""

    counts: list[int] = [0, 0]

    def counting(index: int, name: str) -> Any:
        original: Any = getattr(Core, name)

        def build(*args: Any) -> Any:
            counts[index] += 1

            return original(*args)

        return build

    with mock.patch.object(Core, "ManagedInvalidationRegistrar", counting(0, "ManagedInvalidationRegistrar")), mock.patch.object(Core, "_EnumeratorRevocator", counting(1, "_EnumeratorRevocator")): factory()

    return (counts[0], counts[1])

def _subclasses(cls: type) -> list[type]:
    found: list[type] = []
    subclass: type

    for subclass in cls.__subclasses__():
        found.append(subclass)
        found.extend(_subclasses(subclass))

    return found

class TestWhoOptsIn(unittest.TestCase):
    def test_only_a_declared_enumerator_builds_the_invalidation_machinery(self) -> None:
        """The promise of `Enumeration/5.0`, held on the structure rather than on a timing: no registrar, no
        revocator, no allocation for an enumerator that does not declare the invalidation. The tuple
        enumerators declare it, and with them the enumerators a mutable list delivers; the iterator,
        the index enumerator below the tuple and the wrappers do not. Since 27603402, every node
        enumerator of the linked lists declares it, a value enumerator through the node enumerator
        it reads (Enumeration 6.5 §2.1): those of the eight enumerable singly linked types, which
        register them, and those of the doubly linked lists, which do not register them yet
        (Enumeration 6.5 §4.4)."""

        items = CreateList([1, 2])
        linked: ReadOnlyArray[tuple[str, Singly.IEnumerableList[int]]] = (
            ("EnumerableQueue", Singly.EnumerableQueue[int]((1, 2))),
            ("EnumerableStack", Singly.EnumerableStack[int]((1, 2))),
            ("CountableEnumerableQueue", Singly.CountableEnumerableQueue[int]((1, 2))),
            ("CountableEnumerableStack", Singly.CountableEnumerableStack[int]((1, 2))),
            ("EnumerableBufferedQueue", Buffer.EnumerableBufferedQueue[int]((1, 2))),
            ("EnumerableBufferedStack", Buffer.EnumerableBufferedStack[int]((1, 2))),
            ("CountableEnumerableBufferedQueue", Buffer.CountableEnumerableBufferedQueue[int]((1, 2))),
            ("CountableEnumerableBufferedStack", Buffer.CountableEnumerableBufferedStack[int]((1, 2))))
        doubly = CreateDoublyList((1, 2))
        rows: ReadOnlyArray[tuple[str, Function[Any], bool]] = (
            ("TupleEnumerator", lambda: TupleEnumerator(items), True),
            ("ResumableTupleEnumerator", lambda: ResumableTupleEnumerator(items), True),
            ("List.TryGetEnumerator()", items.TryGetEnumerator, True),
            *((f"Singly: {name}.TryGetEnumerator()", collection.TryGetEnumerator, True) for name, collection in linked),
            ("Doubly: Welded.List.TryGetEnumerator()", doubly.TryGetEnumerator, True),
            ("Doubly: Welded.List.TryGetNodeEnumerator()", doubly.TryGetNodeEnumerator, True),
            ("Iterator", lambda: Iterator(iter((1, 2))), False),
            ("an index enumerator", lambda: _Counter(2), False),
            ("Selector", lambda: Selector(Iterator(iter((1, 2)))), False),
            ("ConverterEnumerator", lambda: ConverterEnumerator(Iterator(iter((1, 2))), str), False))

        for label, factory, declared in rows:
            with self.subTest(enumerator = label):
                built: list[Any] = []

                self.assertEqual(_allocations(lambda: built.append(factory())), (1, 1) if declared else (0, 0))
                self.assertIs(isinstance(built[0], IInvalidatableEnumeratorBase), declared)

_DOORS: ReadOnlyArray[str] = ("_AddRegistrar", "_Register")

def _knock(door: str, e: _Plain, registrar: list[str], registry: _Objects) -> None:
    if door == "_AddRegistrar": e.AddRegistrarAnyway(_Spy(registrar))

    else: e.RegisterAnyway(registry)

class TestARefusalLeavesNoTrace(unittest.TestCase):
    def test_a_non_invalidatable_enumerator_refuses_both_doors(self) -> None:
        """Before the start and between two steps alike: the refusal is raised at the call, where the
        mistake is, rather than accepted and lost. Nothing reaches the registrar or the registry."""

        for moment, steps in (("before the start", 0), ("between two steps", 1)):
            for door in _DOORS:
                with self.subTest(moment = moment, door = door):
                    registrar: list[str] = []
                    registry = _Objects()
                    e = _Plain((1, 2, 3))

                    for _ in range(steps): e.MoveNext()

                    with self.assertRaises(InvalidOperationError): _knock(door, e, registrar, registry)

                    self.assertEqual((registrar, registry.objects), ([], []))

    def test_the_enumeration_runs_on_as_if_nothing_had_been_asked(self) -> None:
        """`_Register` is refused inside the work of the monitor: the monitor must come out of it free.
        A second refusal says what the first said, where a busy monitor would answer with the
        reentrancy error; and the enumeration reads the rest of its items, then completes."""

        for door in _DOORS:
            with self.subTest(door = door):
                e = _Plain((1, 2, 3))

                e.MoveNext()

                first, second = (_raises(lambda: _knock(door, e, [], _Objects())) for _ in range(2))

                self.assertIsInstance(first, InvalidOperationError)
                self.assertEqual((type(second), str(second)), (type(first), str(first)))

                rest: list[int] = []

                while e.MoveNext(): rest.append(e.GetCurrent())

                self.assertEqual((rest, _st(e)), ([2, 3], "Ended/Completed"))

class TestTheDeclarationReachesItsInterface(unittest.TestCase):
    def test_every_declared_enumerator_resolves_the_members_of_its_interface(self) -> None:
        """A class lists its base class before its interfaces, and C3 puts that base first: a member
        it defines shadows the one an interface placed after it was meant to provide. That is how the
        first draft of 392ead1 left every tuple enumerator undeclared, `EnumeratorBase._CanInvalidate`
        answering False ahead of the interface's True. Every loaded class that declares the
        interface must resolve each of its members to the interface's own definition. Under the whole
        suite, the loaded classes are those of every module a bench reaches."""

        members: list[str] = [name for name, value in vars(IDefaultInvalidatableEnumeratorBase).items() if inspect.isfunction(value) and name != "__init__"]
        declared: list[type] = [cls for cls in _subclasses(EnumeratorBase) if issubclass(cls, IDefaultInvalidatableEnumeratorBase)]

        self.assertIn("_CanInvalidate", members)
        self.assertTrue({TupleEnumerator, ResumableTupleEnumerator} <= set(declared))

        for cls in declared:
            for name in members:
                with self.subTest(cls = cls.__qualname__, member = name):
                    self.assertIs(getattr(cls, name), getattr(IDefaultInvalidatableEnumeratorBase, name))

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

def _shadowed(self: Any) -> bool: return False
def _everyone(self: Any) -> bool: return True

class TestTheOptInBenchesCanFail(unittest.TestCase):
    """The three benches of the opt-in invalidation, run against the defects they are meant to catch:
    green on the intact tree, red on the rebuilt one. Each substitution is a class attribute, patched
    for the length of a block and restored on the way out."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **rebuilt): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")

    def test_the_table_falls_when_every_enumerator_builds_the_machinery(self) -> None:
        """As at 87fe2942: the machinery built for every enumerator, declared or not."""

        self.__assertFalls(TestWhoOptsIn, "test_only_a_declared_enumerator_builds_the_invalidation_machinery", getattr(Core, "_IInvalidatableEnumeratorBase"), {"_CanInvalidate": _everyone})

    def test_the_table_falls_when_no_enumerator_opts_in(self) -> None:
        """The first draft of 392ead1: `_CanInvalidate` defined on `EnumeratorBase`, ahead of the interface."""

        self.__assertFalls(TestWhoOptsIn, "test_only_a_declared_enumerator_builds_the_invalidation_machinery", EnumeratorBase, {"_CanInvalidate": _shadowed})

    def test_the_table_falls_when_the_node_enumerators_do_not_opt_in(self) -> None:
        """As before 27603402: the node enumerators of the linked lists built no machinery, and the
        value enumerators that read them none either."""

        self.__assertFalls(TestWhoOptsIn, "test_only_a_declared_enumerator_builds_the_invalidation_machinery", NodeEnumeratorAbstract, {"_CanInvalidate": _shadowed})

    def test_the_refusal_bench_falls_when_the_null_component_accepts_in_silence(self) -> None:
        """The first draft of 392ead1: a registrar accepted and never registered, a registry ignored.
        Each door is rebuilt alone, so that each is shown to be caught."""

        def accept(self: Any, invalidationRegistrar: Any, monitor: Any) -> Any: return None
        def ignore(self: Any, registry: Any) -> None: pass

        for door, rebuilt in (("AddRegistrar", accept), ("Register", ignore)):
            with self.subTest(door = door):
                self.__assertFalls(TestARefusalLeavesNoTrace, "test_a_non_invalidatable_enumerator_refuses_both_doors", getattr(Core, "_NullEnumeratorInvalidation"), {door: rebuilt})

    def test_the_trace_bench_falls_when_a_refusal_leaves_the_monitor_busy(self) -> None:
        """A `DoWork` that gives the monitor back only when its work succeeds. `EnumeratorBase` looks
        it up in `Core`, and the substitution is made there."""

        def doWork(monitor: Any, worker: Any, errorMessage: Any = None) -> None:
            if monitor.IsBusy(): ThrowMonitorBusyError(errorMessage)

            monitor.Initialize()
            worker()
            monitor.Dispose()

        self.__assertFalls(TestARefusalLeavesNoTrace, "test_the_enumeration_runs_on_as_if_nothing_had_been_asked", Core, {"DoWork": doWork})

    def test_the_resolution_bench_falls_when_a_base_shadows_the_interface(self) -> None:
        """The first draft of 392ead1 again, on the bench that names its cause."""

        self.__assertFalls(TestTheDeclarationReachesItsInterface, "test_every_declared_enumerator_resolves_the_members_of_its_interface", EnumeratorBase, {"_CanInvalidate": _shadowed})


# ---------------------------------------------------------------------------
# A wrapper and its source (Q12)
# ---------------------------------------------------------------------------
# A wrapper (`AbstractEnumeratorBase`) steps with its source's `TryMoveNext()`, and subscribes at
# construction to the notifier its source hands out (`GetSourceNotifier()`, which a wrapper relays
# from its own source). The source's invalidation and revocation, which its registries trigger,
# reach the wrapper through that subscription and abort it; the classic stops of the source, its end
# and a deliberate Stop(), are the wrapper's own end. A wrapper only wraps a source in its initial
# state, Idle/Idle, since it shares the source's position (Enumeration 6.10 §4.3, 6.13, 6.14). Q12
# came in with bab109da to 46a2f0fd, the guard in its present form with 6ebf66ca.

def _enumerator(items: Core.IEnumerable[int]) -> IEnumerator[int]:
    enumerator: IEnumerator[int]|None = items.TryGetEnumerator()

    assert enumerator is not None

    return enumerator

def _hooks(e: EnumeratorAbstract[Any]) -> list[str]:
    """Spies on the terminal hooks of one enumerator: each call writes its name to the list returned,
    then runs the hook it replaces."""

    sink: list[str] = []

    def spy(name: str) -> None:
        hook: Any = getattr(e, name)

        def spied(*args: Any) -> Any:
            sink.append(name + (f"({args[0]})" if args else ""))

            return hook(*args)

        setattr(e, name, spied)

    for name in ("_OnCompleted", "_OnStopped", "_OnErrored", "_OnAborted", "_OnTerminated"): spy(name)

    return sink

def _outcome(f: Function[object]) -> str:
    """What a call answers, or the name of what it raises."""

    try: return repr(f())
    except Exception as ex: return type(ex).__name__

def _failing(value: int) -> int:
    if value == 2: raise ValueError("conversion")

    return value

class _Refusing(TupleEnumerator[int]):
    """A source whose start raises: it ends Faulted without having started."""

    def _OnStarting(self) -> bool: raise ValueError("refused")

type _Scene = tuple[EnumeratorAbstract[int], IEnumerator[int], Function[object]]

def _invalidatedSource() -> _Scene:
    items = CreateList([1, 2, 3])
    source: IEnumerator[int] = _enumerator(items)
    wrapper = Selector(source)

    wrapper.MoveNext()

    return wrapper, source, lambda: items.Add(9)

def _revokedSource() -> _Scene:
    items = CreateList([1, 2, 3])
    source: IEnumerator[int]|None = items.AsImmutable().TryGetEnumerator()

    assert source is not None

    wrapper = Selector(source)

    wrapper.MoveNext()

    return wrapper, source, lambda: items.Add(9)

def _stoppedSource() -> _Scene:
    source = TupleEnumerator(CreateList([1, 2, 3]))
    wrapper = Selector(source)

    wrapper.MoveNext()

    return wrapper, source, source.Stop

def _endingSource() -> _Scene:
    source = TupleEnumerator(CreateList([1]))
    wrapper = Selector(source)

    wrapper.MoveNext()

    return wrapper, source, lambda: None

def _faultingWrapper() -> _Scene:
    source = TupleEnumerator(CreateList([1, 2, 3]))
    wrapper = ConverterEnumerator(source, _failing)

    wrapper.MoveNext()

    return wrapper, source, wrapper.TryMoveNext

def _stoppedWrapper() -> _Scene:
    source = TupleEnumerator(CreateList([1, 2, 3]))
    wrapper = Selector(source)

    wrapper.MoveNext()

    return wrapper, source, wrapper.Stop

_SCENES: ReadOnlyArray[tuple[str, Function[_Scene], ReadOnlyArray[str|bool]]] = (
    # (event, TryMoveNext(), the wrapper, MoveNext(), the source, the specific hook, _OnAborted)
    ("its source is invalidated", _invalidatedSource, ("None", "False", "Ended/Invalidated", "InvalidatedError", "Ended/Invalidated", "none", True)),
    ("its source is revoked", _revokedSource, ("None", "False", "Ended/Revoked", "InvalidatedError", "Ended/Revoked", "none", True)),
    ("its source is stopped", _stoppedSource, ("None", "False", "Ended/Completed", "False", "Ended/Stopped", "_OnCompleted", False)),
    ("its source ends", _endingSource, ("None", "False", "Ended/Completed", "False", "Ended/Completed", "_OnCompleted", False)),
    ("it faults on its own", _faultingWrapper, ("ValueError", "False", "Ended/Faulted", "BrokenObjectError", "Ended/Stopped", "_OnErrored", True)),
    ("its consumer stops it", _stoppedWrapper, ("None", "False", "Ended/Stopped", "InvalidOperationError", "Ended/Stopped", "_OnStopped", True)))

class TestAWrapperReportsWhatStoppedItsSource(unittest.TestCase):
    def test_each_cause_ends_the_wrapper_as_its_own(self) -> None:
        """Each wrapper has stepped once when the event comes. The source's invalidation and its
        revocation are told by the wrapper as its own: TryMoveNext() answers False, MoveNext() raises
        InvalidatedError (N6), the status names the cause, and the wrapper takes the abort path
        without a specific hook, as the base does on these private causes (C12). A source stopped on
        purpose or ending is the wrapper's end. A fault of the wrapper and a stop by its consumer are
        its own outcomes, and stop the source. No event but the wrapper's own fault raises."""

        for label, scene, expected in _SCENES:
            with self.subTest(wrapper = label):
                wrapper, source, event = scene()
                sink: list[str] = _hooks(wrapper)
                happened: str = _outcome(event)
                answered: str = _outcome(wrapper.TryMoveNext)

                self.assertEqual((happened, answered, _st(wrapper), _outcome(wrapper.MoveNext), _st(source), _fired(sink), "_OnAborted" in sink), expected)

    def test_a_source_revoked_before_the_first_step_ends_the_wrapper_revoked(self) -> None:
        """The guard takes the source in its initial state, where it can still be revoked. The wrapper,
        subscribed since its construction, is told of it before its first step, which a subscription
        deferred to that step would miss: the wrapper would then read nothing and end Completed."""

        items = CreateList([1, 2, 3])
        source: IEnumerator[int]|None = items.AsImmutable().TryGetEnumerator()

        assert source is not None

        wrapper = Selector(source)
        happened: str = _outcome(lambda: items.Add(9))

        self.assertEqual((happened, _outcome(wrapper.TryMoveNext), _st(wrapper), _outcome(wrapper.MoveNext), _st(source)), ("None", "False", "Ended/Revoked", "InvalidatedError", "Ended/Revoked"))

    def test_the_enumerator_of_a_read_only_view_tells_the_invalidation_of_its_collection(self) -> None:
        """The use the wrappers are meant for: a collection wrapper, here the read-only view of an
        indexable list, hands out a wrapper over the enumerator of its collection."""

        items = CreateList([1, 2, 3])
        enumerator: IEnumerator[int]|None = items.AsReadOnly().TryGetEnumerator()

        assert enumerator is not None

        enumerator.MoveNext()

        happened: str = _outcome(lambda: items.Add(9))

        self.assertEqual((happened, _outcome(enumerator.TryMoveNext), _st(enumerator), _outcome(enumerator.MoveNext)), ("None", "False", "Ended/Invalidated", "InvalidatedError"))

class TestAWrapperOnlyWrapsASourceInItsInitialState(unittest.TestCase):
    def test_it_wraps_a_source_in_its_initial_state(self) -> None:
        """A fresh source, and one reset after a step, which is Idle/Idle again."""

        def reset() -> IEnumerator[int]:
            source: IEnumerator[int] = _enumerator(CreateList([1, 2, 3]))

            source.MoveNext()
            source.TryReset()

            return source

        rows: ReadOnlyArray[tuple[str, Function[IEnumerator[int]]]] = (("a fresh source", lambda: _enumerator(CreateList([1, 2, 3]))), ("a source reset after a step", reset))

        for label, make in rows:
            with self.subTest(source = label):
                wrapper = Selector(make())
                read: list[int] = []

                while wrapper.MoveNext(): read.append(wrapper.GetCurrent())

                self.assertEqual(read, [1, 2, 3])

    def test_it_refuses_any_other_source_and_leaves_it_as_it_was(self) -> None:
        """The refusal comes before the wrapper subscribes: the source is never asked for its notifier,
        and its status is unchanged. The enumerator empty by design is refused as well: whoever
        wraps an enumerator it received handles that one itself."""

        def running() -> IEnumerator[int]:
            source: IEnumerator[int] = _enumerator(CreateList([1, 2, 3]))

            source.MoveNext()

            return source

        def completed() -> IEnumerator[int]:
            source: IEnumerator[int] = _enumerator(CreateList([1]))

            while source.MoveNext(): pass

            return source

        def stopped() -> IEnumerator[int]:
            source: IEnumerator[int] = _enumerator(CreateList([1, 2, 3]))

            source.Stop()

            return source

        def invalidated() -> IEnumerator[int]:
            items = CreateList([1, 2, 3])
            source: IEnumerator[int] = _enumerator(items)

            source.MoveNext()
            items.Add(9)

            return source

        def revoked(steps: int) -> IEnumerator[int]:
            items = CreateList([1, 2, 3])
            source: IEnumerator[int]|None = items.AsImmutable().TryGetEnumerator()

            assert source is not None

            for _ in range(steps): source.MoveNext()

            items.Add(9)

            return source

        def faulted() -> IEnumerator[int]:
            source = _Refusing(CreateList([1, 2, 3]))

            _raises(source.TryMoveNext)

            return source

        def empty() -> IEnumerator[int]: return Core.GetEmptyEnumerator()

        rows: ReadOnlyArray[tuple[str, Function[IEnumerator[int]], str]] = (
            ("running", running, "Started/Running"),
            ("completed", completed, "Ended/Completed"),
            ("stopped before its start", stopped, "Ended/Stopped"),
            ("invalidated", invalidated, "Ended/Invalidated"),
            ("revoked before its start", lambda: revoked(0), "Ended/Revoked"),
            ("revoked while running", lambda: revoked(1), "Ended/Revoked"),
            ("faulted at its start", faulted, "Ended/Faulted"),
            ("empty by design", empty, "Ended/NoData"))

        for label, make, status in rows:
            with self.subTest(source = label):
                source: IEnumerator[int] = make()

                self.assertEqual(_st(source), status)

                with mock.patch.object(source, "GetSourceNotifier", wraps = source.GetSourceNotifier) as asked:
                    with self.assertRaises(InvalidOperationError): Selector(source)

                asked.assert_not_called()

                self.assertEqual(_st(source), status)

class TestANestedWrapperIsAbortedThroughItsSource(unittest.TestCase):
    def test_the_outer_wrapper_ends_as_its_innermost_source(self) -> None:
        """A wrapper relays the notifier of its own source, so a wrapper over a wrapper subscribes to
        the innermost source, and both end as it does. The write that invalidates the source does not
        raise."""

        def nested(immutable: bool) -> tuple[EnumeratorAbstract[int], EnumeratorAbstract[int], Function[object]]:
            items = CreateList([1, 2, 3])
            source: IEnumerator[int]|None = items.AsImmutable().TryGetEnumerator() if immutable else items.TryGetEnumerator()

            assert source is not None

            inner = Selector(source)
            outer = Selector(inner)

            outer.MoveNext()

            return outer, inner, lambda: items.Add(9)

        for label, immutable, cause in (("invalidated", False, "Ended/Invalidated"), ("revoked", True, "Ended/Revoked")):
            with self.subTest(source = label):
                outer, inner, event = nested(immutable)
                happened: str = _outcome(event)

                self.assertEqual((happened, _outcome(outer.TryMoveNext), _st(outer), _outcome(outer.MoveNext), _st(inner)), ("None", "False", cause, "InvalidatedError", cause))

class TestTheWrapperBenchesCanFail(unittest.TestCase):
    """The benches of Q12, run against the wrapper before it and against each blocking point that
    its implementation went through (Enumeration 6.13 §1): green on the intact tree, red on the
    rebuilt one, and red on their assertions rather than on an error. The private members are
    reached by their mangled names."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, rebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with ExitStack() as patches:
            for target, members in rebuilt: patches.enter_context(mock.patch.multiple(target, **members))

            broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")
        self.assertEqual(broken.errors, [], f"{name} fell on an error rather than on its assertions")

    def __assertCauseBenchesFall(self, rebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]]) -> None:
        for bench, name in ((TestAWrapperReportsWhatStoppedItsSource, "test_each_cause_ends_the_wrapper_as_its_own"),
                            (TestAWrapperReportsWhatStoppedItsSource, "test_a_source_revoked_before_the_first_step_ends_the_wrapper_revoked"),
                            (TestAWrapperReportsWhatStoppedItsSource, "test_the_enumerator_of_a_read_only_view_tells_the_invalidation_of_its_collection"),
                            (TestANestedWrapperIsAbortedThroughItsSource, "test_the_outer_wrapper_ends_as_its_innermost_source")):
            with self.subTest(bench = name): self.__assertFalls(bench, name, rebuilt)

    def test_the_benches_fall_on_the_wrapper_before_q12(self) -> None:
        """Until Q12, a wrapper stepped with its source's MoveNext() and subscribed to nothing: it
        raised InvalidatedError from TryMoveNext() and ended Faulted (Enumeration 6.10 §1.3), and a
        source stopped on purpose faulted it as well."""

        def stepping(self: Any) -> bool: return cast(bool, self._GetContainer().MoveNext())
        def unsubscribed(self: Any) -> None: return None

        self.__assertCauseBenchesFall(((AbstractEnumeratorBase, {"_MoveNextOverride": stepping, "_GetNotifier": unsubscribed}),))

    def test_the_benches_fall_when_the_subscription_depends_on_the_opt_in(self) -> None:
        """The first blocking point: a wrapper subscribed only if it declared the invalidation, which
        no wrapper does. Before the wrapper's first step, this is also what a subscription deferred to
        that step leaves: no subscription."""

        def optedIn(self: Any) -> Any: return self._GetContainer().GetSourceNotifier() if self._CanInvalidate() else None

        self.__assertCauseBenchesFall(((AbstractEnumeratorBase, {"_GetNotifier": optedIn}),))

    def test_the_benches_fall_when_nobody_keeps_the_callback(self) -> None:
        """The second: the callback handed to the notifier was kept by nobody, and died at once; the
        notifier holds its subscribers weakly. The subscription is rebuilt keeping something else."""

        original: Any = Core.Subscription

        def forgetting(callback: Any, node: Any) -> Any: return original(object(), node)

        self.__assertCauseBenchesFall(((Core, {"Subscription": forgetting}),))

    def test_the_benches_fall_when_the_source_notifies_within_its_work(self) -> None:
        """The third: the source notified while its monitor was busy, so the wrapper's abort stopped
        it reentrantly, and the error reached the write."""

        original: Any = getattr(EnumeratorAbstract, "_EnumeratorAbstract__Abort")

        def within(self: Any, revoke: bool) -> None:
            if getattr(self, "_EnumeratorAbstract__monitor").IsBusy():
                original(self, revoke)

                return

            terminate: Any = getattr(self, "_EnumeratorAbstract__Terminate")
            invalidation: Any = getattr(self, "_EnumeratorAbstract__invalidation")

            def work() -> None:
                terminate(EnumerationAbortReason.Revoked if revoke else EnumerationAbortReason.Invalidated)
                invalidation.Notify(revoke)

            getattr(self, "_EnumeratorAbstract__DoWork")(work)

        self.__assertCauseBenchesFall(((EnumeratorAbstract, {"_EnumeratorAbstract__Abort": within}),))

    def test_the_nested_bench_falls_when_a_wrapper_does_not_relay_its_source(self) -> None:
        """The fourth: GetSourceNotifier() answered the enumerator's own notifier, which a wrapper does
        not have, so a wrapper over a wrapper subscribed to nothing."""

        def own(self: Any) -> Any: return getattr(self, "_EnumeratorAbstract__invalidation").GetSourceNotifier()

        self.__assertFalls(TestANestedWrapperIsAbortedThroughItsSource, "test_the_outer_wrapper_ends_as_its_innermost_source", ((EnumeratorAbstract, {"GetSourceNotifier": own}),))

    def test_the_refusal_bench_falls_on_the_earlier_guard(self) -> None:
        """Until 6ebf66ca, the guard refused only a running source: one that had ended passed."""

        def earlier(self: Any, enumerator: Any) -> None:
            if enumerator.GetStatus().IsStarted(): raise InvalidOperationError("The given enumerator is already started.")

            setattr(self, "_AbstractEnumeratorBase__enumerator", enumerator)

            getattr(EnumeratorAbstract, "__init__")(self)

        self.__assertFalls(TestAWrapperOnlyWrapsASourceInItsInitialState, "test_it_refuses_any_other_source_and_leaves_it_as_it_was", ((AbstractEnumeratorBase, {"__init__": earlier}),))

if __name__ == "__main__": unittest.main()

# ---------------------------------------------------------------------------
# The exit of a with statement
# ---------------------------------------------------------------------------

def _registeredEnumerators(items: object) -> int:
    """The entries of the registry of the enumerators of a collection, counted on its list."""

    registry: Any = getattr(items, "_GetCollectionRegistries")().GetEnumeratorRegistry()._GetRegistry()
    node: Any = getattr(registry, "_ObjectRegistryBase__items")._GetItems().GetFirstNode()
    count: int = 0

    while node is not None:
        count += 1
        node = node.GetNext()

    return count

class _RecordingCursor(IteratorBase[int], ICursor[int]):
    """A cursor that records its stop and its disposal, in their order."""

    def __init__(self, log: list[str]) -> None:
        super().__init__()

        self.__log: list[str] = log

    def GetCurrent(self) -> int: raise GetIterationInactiveError()
    def TryMoveNext(self) -> bool: return False
    def Stop(self) -> None: self.__log.append("Stop")
    def TryReset(self) -> bool|None: return None
    def IsResetSupported(self) -> bool: return False

    def GetStatus(self) -> IIterationStatus: return GetNoDataEnumerationStatus()

    def Dispose(self) -> None: self.__log.append("Dispose")

class TestAWithStatementStopsAnEnumerator(unittest.TestCase):
    """The exit of a with statement stops an enumerator and does nothing else: it leaves the registry
    of its source at once, rather than at a later purge, and an exception raised in the block goes
    through. A cursor, which holds a resource, is stopped, then disposed. A for loop never exits an
    enumerator, so that the with statement is the consumer's way to stop it as soon as it is done
    (Registre 9 §5, Registre 10, and the method report on the guarantees of the language)."""

    def test_an_enumerator_is_stopped_at_the_exit_of_the_block_and_leaves_its_registry(self) -> None:
        items: Any = CreateList([1, 2, 3])
        enumerator: IEnumerator[int] = items.GetEnumerator()

        with enumerator as entered:
            self.assertIs(entered, enumerator)
            self.assertTrue(enumerator.TryMoveNext())
            self.assertEqual(_registeredEnumerators(items), 1)

        self.assertEqual(_st(enumerator), "Ended/Stopped")
        self.assertFalse(enumerator.TryMoveNext())
        self.assertEqual(_registeredEnumerators(items), 0, "the enumerator stays in the registry of its source")

    def test_an_exception_raised_in_the_block_goes_through_and_the_enumerator_is_stopped(self) -> None:
        enumerator: IEnumerator[int] = CreateList([1, 2, 3]).GetEnumerator()

        with self.assertRaises(ValueError):
            with enumerator:
                enumerator.TryMoveNext()

                raise ValueError()

        self.assertEqual(_st(enumerator), "Ended/Stopped")

    def test_a_cursor_is_stopped_then_disposed(self) -> None:
        for name, raising in (("the block ends", False), ("the block raises", True)):
            with self.subTest(exit = name):
                log: list[str] = []

                try:
                    with _RecordingCursor(log):
                        if raising: raise ValueError()

                except ValueError: pass

                self.assertEqual(log, ["Stop", "Dispose"])

class TestTheWithBenchesCanFail(unittest.TestCase):
    """The benches of the with statement, run against a hook taken out: green on the intact tree, red
    on the rebuilt one."""

    def __assertFalls(self, name: str, target: Any, members: dict[str, Any]) -> None:
        self.assertTrue(_run(TestAWithStatementStopsAnEnumerator, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **members): broken: unittest.TestResult = _run(TestAWithStatementStopsAnEnumerator, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall without the hook")

    def test_the_benches_fall_when_the_exit_does_not_stop_the_enumerator(self) -> None:
        def notStopping(self: Any, excType: Any, exc: Any, traceback: Any) -> bool|None: return False

        for name in unittest.defaultTestLoader.getTestCaseNames(TestAWithStatementStopsAnEnumerator):
            with self.subTest(bench = name): self.__assertFalls(name, IEnumeratorBase, {"_OnExiting": notStopping})

    def test_the_cursor_bench_falls_when_the_exit_does_not_dispose(self) -> None:
        def notDisposing(self: Any, result: bool) -> bool: return result

        self.__assertFalls("test_a_cursor_is_stopped_then_disposed", IDisposable, {"_OnExited": notDisposing})
