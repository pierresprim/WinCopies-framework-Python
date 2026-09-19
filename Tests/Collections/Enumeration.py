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
"""

from __future__ import annotations

import gc
import unittest
import weakref

from enum import StrEnum
from typing import Any, Callable, Type, cast



from WinCopies import Abstract

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Enumeration import IterationState, IterationResult, IterationData, IIterationStatus, IterationStatus
from WinCopies.Collections.Enumeration.Abstraction import AbstractionEnumerator
from WinCopies.Collections.Enumeration.Core import IEnumerator, IInvalidatableEnumerator, EnumeratorBase
# `_Registrar` is internal on purpose: the phantom-entry point below has to build
# the real registry chain, and no public entry point exposes it.
from WinCopies.Collections.Extensions.Enumeration import EnumeratorRegistry, _Registrar # pyright: ignore[reportPrivateUsage]
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Generation.Registry.Invalidation import InvalidationRegistrar
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Function, Converter
from WinCopies.Typing.Discard import IInvalidatable, BrokenObjectError, DiscardedError, InvalidatedError

# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def _st(e: IEnumerator[int]) -> str:
    """`State/Result` of an enumerator, as a single readable token."""
    status = e.GetStatus()

    return f"{status.GetState().name}/{status.GetResult().name}"

def _data(e: _Base) -> str:
    return e.GetStatus().GetData().name or "Null"

def _snap(e: _Base) -> tuple[str, str]:
    status = e.GetStatus()

    return (status.GetState().name, status.GetResult().name)

def _drain(e: EnumeratorBase[int]) -> None:
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
        self.cookie: IInvalidatable|None = None

    def Register(self, cookie: IInvalidatable) -> None:
        self.cookie = cookie

        self.__sink.append(Action.REGISTER)

    def Unregister(self) -> None: self.__sink.append(Action.UNREGISTER)

    def Fire(self) -> None: cast(IInvalidatable, self.cookie).Invalidate()

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

class _Base(EnumeratorBase[int]):
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

    def _GetCurrent(self) -> int: return cast(int, self._cur)

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

class TestHookAttribution(unittest.TestCase):
    def test_specific_hooks_including_the_absence_on_invalidated(self) -> None:
        """The deliberate absence on `Invalidated`: `__Invalidate()` is private
        and only registries borrow it, so the implementer is not the party
        addressed by that cause. Asserted so a later reader does not 'fix' it."""
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

        self.assertEqual(aborted, {"Completed": False, "Failed": False,
                                   "Stopped": True, "Faulted": True, "Invalidated": True})

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
        class _AbsBoom(self.Abs):
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
        than the symptom patched."""
        calls: int = 0
        original = IterationStatus.Unfault

        def _counting(self: IterationStatus) -> None:
            nonlocal calls

            calls += 1

            return original(self)

        IterationStatus.Unfault = _counting

        self.addCleanup(setattr, IterationStatus, "Unfault", original)

        e: _Base = _Base(range(50))

        for _ in range(50):
            try:
                if not e.TryMoveNext(): break

            except Exception: break

        e.raiseIn = {"_MoveNextOverride#10"}

        try: e.TryMoveNext()
        except Exception: pass

        self.assertEqual(calls, 0, f"{calls} call(s) to Unfault over a full run — resumption no longer exists")

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

_PATHS: list[tuple[str, Callable[[], Any]]] = [
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
        table = ((F.Faulted, D.Null, True, False, True),
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
