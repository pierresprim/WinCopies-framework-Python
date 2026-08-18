"""
Harnais de régression du registre et du cycle de vie des vues révocables.

Ces tests sont **paramétrés par type concret** : chaque invariant est exercé sur
tous les types de la famille indexable qui le supportent, plutôt que sur un
représentant. La revue Immuabilité.1 a montré qu'une famille supposée uniforme
comporte plusieurs strates de comportement, invisibles à une lecture par
invariant et découvertes en instanciant les types un à un.

Deux contraintes de méthode, héritées du protocole de cette revue, sans
lesquelles les mesures sont fausses :

  * toute mesure de vie d'objet force `gc.collect()` au préalable — une vue
    participe à un cycle sur elle-même via son updater de moniteur, donc sa
    libération passe par le collecteur cyclique ;
  * l'ordre « muter d'abord, observer ensuite » est exercé explicitement : c'est
    là que se logeait le désarmement du registre (D-2).

Le module n'est pas découvert par la ligne qui exécute le reste de la suite ; il
faut le nommer :

    python3 -m unittest Tests.Collections.Registry
"""

import gc
import unittest
from typing import Any, Callable

from WinCopies.Collections.Abstraction.Collection import (
    Array, ArrayList, EquatableTuple, HashableTuple, List, SortedList, TryCreateSizedList, Tuple)
from WinCopies.Collections.Abstraction.Selection import List as SelectionList
from WinCopies.Collections.ObjectModel.Collection import ObservableCollection
from WinCopies.Typing.Delegate import IFunction
from WinCopies.Typing.Discard import DiscardedError

type Factory = Callable[[], Any]
type Action = Callable[[Any], Any]

class _Handle(IFunction[int]):
    """Initialiseur de cellule pour `ArrayList`, qui exige un fournisseur et non une séquence."""

    def GetValue(self) -> int: return 0

def _source() -> Any: return List[int]([1, 2, 3])

def _arrayList() -> Any:
    """`ArrayList` s'initialise par un fournisseur, donc à cellules identiques. Les
    valeurs sont distinguées ensuite, faute de quoi `Move` et `Swap` seraient
    effectifs sans que le contenu observable le montre."""

    items = ArrayList[int](3, _Handle())

    for index in range(3): items.SetAt(index, index + 1)

    return items

def _sizedList() -> Any:
    """Liste dimensionnée avec de la marge : pleine, elle refuserait toute insertion et
    laisserait six chemins d'écriture inexercés."""

    items = TryCreateSizedList(6, [1, 2, 3])

    assert items is not None

    return items

# Recettes de mutation, par nom de membre. Un type ne les porte pas toutes ; le
# harnais n'exerce que celles qu'il expose, ce qui donne la couverture C5 sans
# écrire un test par couple (type, mutateur).
_MUTATORS: dict[str, Action] = {
    "Add":            lambda o: o.Add(9),
    "AddLeft":        lambda o: o.AddLeft(9),
    "AddRange":       lambda o: o.AddRange((7, 8)),
    "TryAddRange":    lambda o: o.TryAddRange((7, 8)),
    "Insert":         lambda o: o.Insert(1, 9),
    "TryInsert":      lambda o: o.TryInsert(1, 9),
    "InsertRange":    lambda o: o.InsertRange(1, (7, 8)),
    "TryInsertRange": lambda o: o.TryInsertRange(1, (7, 8)),
    "InsertValues":   lambda o: o.InsertValues(1, 7, 8),
    "SetAt":          lambda o: o.SetAt(0, 9),
    "TrySetAt":       lambda o: o.TrySetAt(0, 9),
    "RemoveAt":       lambda o: o.RemoveAt(0),
    "TryRemoveAt":    lambda o: o.TryRemoveAt(0),
    "Remove":         lambda o: o.Remove(1),
    "TryRemove":      lambda o: o.TryRemove(1),
    "RemoveRange":    lambda o: o.RemoveRange(0, 2),
    "TryRemoveRange": lambda o: o.TryRemoveRange(0, 2),
    "Move":           lambda o: o.Move(0, 2),
    "TryMove":        lambda o: o.TryMove(0, 2),
    "Swap":           lambda o: o.Swap(0, 2),
    "TrySwap":        lambda o: o.TrySwap(0, 2),
    "Clear":          lambda o: o.Clear(),
}

class _Case:
    """Un type concret et sa fabrique."""

    def __init__(self, name: str, factory: Factory) -> None:
        self.name = name
        self.factory = factory

    def Create(self) -> Any: return self.factory()

class _MutableCase(_Case):
    """Un type mutable, avec de quoi le muter effectivement et de quoi se faire refuser.

    `refuse` applique une mutation que le type doit **rejeter** : elle sert à vérifier
    C6, et son libellé varie selon que le type est redimensionnable ou à taille fixe.
    """

    def __init__(self, name: str, factory: Factory, mutate: Action, refuse: Action, sourced: bool = False) -> None:
        super().__init__(name, factory)

        self.mutate = mutate
        self.refuse = refuse
        self.sourced = sourced   # le type route son registre vers celui d'une source

    def GetMutators(self, items: Any) -> list[tuple[str, Action]]:
        return [(n, f) for n, f in _MUTATORS.items() if callable(getattr(items, n, None))]

def _snapshot(items: Any) -> tuple[Any, ...]:
    """Contenu observable, pour établir qu'une mutation a *effectivement* eu lieu."""

    return tuple(items.GetAt(i) for i in range(items.GetCount()))

# Strate « Abstraction » : registre propre. Strate « ObjectModel » : registre routé
# vers la source. `Abstract` n'y figure pas — ses types sont abstraits, non
# instanciables ; `Selection` fait l'objet d'une classe dédiée plus bas.
def _resizable(items: Any) -> Any: return items.TryRemoveAt(99)
def _fixed(items: Any) -> Any: return items.TrySetAt(99, 9)

_IMMUTABLE: list[_Case] = [
    _Case("Tuple",          lambda: Tuple[int]((1, 2, 3))),
    _Case("EquatableTuple", lambda: EquatableTuple[int]((1, 2, 3))),
    _Case("HashableTuple",  lambda: HashableTuple[int]((1, 2, 3))),
]

# `ObjectModel.Collection` n'y figure pas : elle est abstraite par conception —
# `ObservableCollection` en est le concret. Elle s'instancie pourtant à l'exécution,
# faute de contrainte d'abstraction ; Pyright, lui, la refuse.
_MUTABLE: list[_MutableCase] = [
    _MutableCase("List",       lambda: List[int]([1, 2, 3]),       lambda o: o.Add(9),      _resizable),
    _MutableCase("SortedList", lambda: SortedList[int]([3, 1, 2]), lambda o: o.Add(9),      _resizable),
    _MutableCase("SizedList",  _sizedList,                         lambda o: o.SetAt(0, 9), _resizable),
    _MutableCase("Array",      lambda: Array[int]([1, 2, 3]),      lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("ArrayList",  _arrayList,                         lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("ObservableCollection", lambda: ObservableCollection[int](_source()), lambda o: o.Add(9), _resizable, True),
]
_ALL: list[_Case] = _IMMUTABLE + list(_MUTABLE)

def _revoked(view: Any) -> bool:
    try:
        view.GetCount()
        return False
    except DiscardedError:
        return True

def _countCookies() -> int:
    """Cookies de révocation vivants. Le type est privé : on le reconnaît par son nom
    plutôt que de l'importer, pour ne pas créer de dépendance hors API."""

    gc.collect()

    return sum(1 for o in gc.get_objects() if type(o).__name__ == "_RevocableViewCookie")

class TestGenerationIdentity(unittest.TestCase):
    """C2 et C3 : une génération, une instance ; une mutation, une génération neuve."""

    def test_same_instance_within_a_generation(self) -> None:
        for case in _ALL:
            with self.subTest(type = case.name):
                items = case.Create()

                self.assertIs(items.AsImmutable(), items.AsImmutable())

    def test_new_and_distinct_instance_after_mutation(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                first: Any = items.AsImmutable()

                case.mutate(items)

                second: Any = items.AsImmutable()

                self.assertIsNot(second, first)
                self.assertFalse(_revoked(second))

    def test_generations_chain(self) -> None:
        """La révocation n'est pas à un coup : chaque génération meurt à son tour."""

        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                views: list[Any] = []

                for _ in range(4):
                    views.append(items.AsImmutable())

                    case.mutate(items)

                for index, view in enumerate(views):
                    with self.subTest(generation = index):
                        self.assertTrue(_revoked(view))

class TestLazyCreation(unittest.TestCase):
    """C4 : aucun révocable n'est alloué tant qu'aucun n'est demandé."""

    def test_mutating_without_asking_allocates_nothing(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                before: int = _countCookies()

                for _ in range(20): case.mutate(items)

                self.assertEqual(_countCookies(), before)

class TestWritePathCoverage(unittest.TestCase):
    """C5 : un test par mutateur et par type. Le mode de défaillance est le chemin oublié,
    donc l'échantillon ne vaut rien — il faut l'exhaustivité."""

    def test_every_mutator_revokes(self) -> None:
        """Le verdict dépend de l'effet, pas de l'intention : un mutateur qui refuse
        n'a pas à révoquer — c'est C6 —, un mutateur qui écrit y est tenu."""

        for case in _MUTABLE:
            for name, mutate in case.GetMutators(case.Create()):
                with self.subTest(type = case.name, mutator = name):
                    items = case.Create()
                    view: Any = items.AsImmutable()
                    before: tuple[Any, ...] = _snapshot(items)

                    try: mutate(items)
                    except Exception as error:
                        self.skipTest(f"{name} inapplicable sur ce type : {type(error).__name__}")

                    if _snapshot(items) == before: self.assertFalse(_revoked(view), f"{name} n'a rien changé mais a révoqué")
                    else: self.assertTrue(_revoked(view), f"{name} a muté la collection sans révoquer")

class TestIneffectiveMutation(unittest.TestCase):
    """C6 : c'est la mutation *effective* qui révoque, pas la tentative."""

    def test_a_refused_mutation_leaves_the_view_valid(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                view: Any = items.AsImmutable()
                before: tuple[Any, ...] = _snapshot(items)

                self.assertIsNot(case.refuse(items), True)
                self.assertEqual(_snapshot(items), before)
                self.assertFalse(_revoked(view))

class TestRootRegistration(unittest.TestCase):
    """C7 et C8 : l'enregistrement vise la racine, et les projections survivent."""

    def test_mutating_the_source_revokes_a_view_taken_on_the_wrapper(self) -> None:
        source = _source()
        items = ObservableCollection[int](source)
        view: Any = items.AsImmutable()

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

        source.Add(9)

        self.assertTrue(_revoked(view))

    def test_a_chain_two_deep_still_reaches_the_root(self) -> None:
        source = _source()
        reversed_: Any = source.AsReversed()
        view: Any = reversed_.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))

    def test_the_projection_itself_survives_the_mutation(self) -> None:
        """C8 : seul le révocable meurt ; la vue inversée reste utilisable."""

        source = _source()
        reversed_: Any = source.AsReversed()
        view: Any = reversed_.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))
        self.assertEqual(reversed_.GetCount(), 4)

class TestRevocationIsTotal(unittest.TestCase):
    """D1 : toute lecture lève. Aucune ne rend une valeur périmée."""

    def test_every_read_path_raises(self) -> None:
        for case in _MUTABLE:
            items = case.Create()
            view: Any = items.AsImmutable()

            case.mutate(items)

            reads: dict[str, Callable[[], Any]] = {
                "GetCount":  view.GetCount,
                "GetAt":     lambda: view.GetAt(0),
                "Contains":  lambda: view.Contains(1),
                "len":       lambda: len(view.AsSequence()),
                "iteration": lambda: list(view.AsIterable())}

            for name, read in reads.items():
                with self.subTest(type = case.name, read = name):
                    self.assertRaises(DiscardedError, read)

    def test_the_error_names_the_cause(self) -> None:
        """Un consommateur doit pouvoir distinguer l'invalidation d'une disposition."""

        from WinCopies.Typing.Discard import DiscardReason, InvalidatedError

        items = List[int]([1, 2, 3])
        view: Any = items.AsImmutable()

        items.Add(9)

        with self.assertRaises(InvalidatedError) as caught: view.GetCount()

        self.assertEqual(caught.exception.GetDiscardReason(), DiscardReason.Invalidated)

class TestRepresentationDegrades(unittest.TestCase):
    """D2 : `ToString()` et `repr()` ne lèvent pas — ils sont appelés quand quelque chose
    s'est déjà mal passé — et ne fuient pas le contenu."""

    def test_representation_does_not_raise_and_does_not_leak(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                view: Any = items.AsImmutable()

                case.mutate(items)

                for text in (view.ToString(), repr(view)):
                    self.assertIsInstance(text, str)
                    self.assertNotIn("1, 2, 3", text)

class TestSourceRelease(unittest.TestCase):
    """D5 : retenir une vue révoquée ne retient pas la collection."""

    def test_a_revoked_view_does_not_pin_its_source(self) -> None:
        import weakref

        items = List[int]([1, 2, 3])
        view: Any = items.AsImmutable()

        items.Add(9)

        reference = weakref.ref(items)

        del items
        gc.collect()

        self.assertTrue(_revoked(view))
        self.assertIsNone(reference())

class TestDerivedTransitivity(unittest.TestCase):
    """§2.1 de l'addendum 3 : un dérivé se construit sur le révocable, jamais sur ce
    qu'il enveloppe. Sa validité est celle de son sujet."""

    def test_a_derivative_taken_before_revocation_raises_after(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                view: Any = items.AsImmutable()
                sequence = view.AsSequence()

                case.mutate(items)

                self.assertRaises(DiscardedError, lambda: len(sequence))

class TestEnumeratorInvalidation(unittest.TestCase):
    """F1′ : preuve d'exécution du mécanisme, non preuve de non-régression."""

    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        for case in (c for c in _MUTABLE if c.name != "ArrayList"): # cf. TestArrayCollectionStratum
            with self.subTest(type = case.name):
                items = case.Create()
                enumerator: Any = items.TryGetEnumerator()

                self.assertIsNotNone(enumerator)
                self.assertTrue(enumerator.MoveNext())

                case.mutate(items)

                self.assertRaises(DiscardedError, enumerator.MoveNext)

    def test_a_view_and_an_enumerator_die_on_the_same_notification(self) -> None:
        items = List[int]([1, 2, 3])
        enumerator: Any = items.TryGetEnumerator()

        enumerator.MoveNext()

        view: Any = items.AsImmutable()

        items.Add(9)

        self.assertRaises(DiscardedError, enumerator.MoveNext)
        self.assertTrue(_revoked(view))

class TestMutateBeforeObserving(unittest.TestCase):
    """§4.4 : l'ordre inverse. C'est là que se logeait le désarmement du registre (D-2)."""

    def test_mutating_before_the_first_view_does_not_disarm_the_registry(self) -> None:
        for case in _MUTABLE:
            for count in (1, 2, 5):
                with self.subTest(type = case.name, mutationsBefore = count):
                    items = case.Create()

                    for _ in range(count): case.mutate(items)

                    view: Any = items.AsImmutable()

                    case.mutate(items)

                    self.assertTrue(_revoked(view))

class TestArrayCollectionStratum(unittest.TestCase):
    """`ArrayCollection` — donc `ArrayList` — enregistre ses énumérateurs auprès du
    registre de sa **source** alors qu'il invalide le **sien**. C'est le résidu de D-5 ;
    la vue est bien révoquée, l'énumérateur non. Attendu rouge, marqué comme tel."""

    @unittest.expectedFailure
    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        items = _arrayList()
        enumerator: Any = items.TryGetEnumerator()

        enumerator.MoveNext()
        items.SetAt(0, 9)

        self.assertRaises(DiscardedError, enumerator.MoveNext)

class TestSelectionStratum(unittest.TestCase):
    """La strate `Selection` route trois de ses quatre types vers un registre propre au
    lieu de celui de leur source. C'est D-8, et ces tests le constatent — ils sont
    attendus rouges et marqués comme tels, jamais assouplis."""

    @unittest.expectedFailure
    def test_selection_list_routes_to_its_source_registry(self) -> None:
        source = _source()
        items = SelectionList[int, str](source, str, int)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    @unittest.expectedFailure
    def test_mutating_the_source_revokes_a_selection_view(self) -> None:
        source = _source()
        items = SelectionList[int, str](source, str, int)
        view: Any = items.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))

    @unittest.expectedFailure
    def test_mutating_the_selection_itself_revokes_its_view(self) -> None:
        items = SelectionList[int, str](_source(), str, int)
        view: Any = items.AsImmutable()

        items.Add("9")

        self.assertTrue(_revoked(view))

if __name__ == "__main__":
    unittest.main()
