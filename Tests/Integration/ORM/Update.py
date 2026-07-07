"""ORM UPDATE — test matrix (SQLite reference).

Each scenario runs on a fresh in-memory DB (or a temp file for RowVanished).
Reports PASS/FAIL per scenario; does not attempt to fix the ORM on failure.
"""
import os, sqlite3, tempfile, traceback

from WinCopies.Typing.Delegate import Action, IStruct, Struct
from WinCopies.Data.Abstract import IConnection, IDataBase
from WinCopies.Data.Factory import IFieldFactory
from WinCopies.Data.Field import FieldAttributes, IntegerMode, TextMode, IntegerField, TextField
from WinCopies.Data.ORM import (ITransaction, DataContextBase, DataContext, Entity, EntityCollection,
                                autoPrimaryKeyConfig, primaryKeyConfig, columnConfig, entityColumnConfig,
                                PrimaryKeyMutationError, UnpersistedReferenceError, RowVanishedError,
                                UnresolvedRollbackError, EntityNotPersistedError)
from WinCopies.Data.SQLite import Connection

# ------------------------------------------------------------------ entities
class Item(Entity):
    def __init__(self, quantity: int) -> None:
        super().__init__()

        self.__id: IStruct[int] = Struct[int](0)
        self.__quantity: IStruct[int] = Struct[int](quantity)
    
    def Dispose(self) -> None: pass

    @autoPrimaryKeyConfig()
    def Id(self) -> IStruct[int]: return self.__id

    @columnConfig()
    def Quantity(self) -> IStruct[int]: return self.__quantity
    
    def _SetIdRaw(self, v: int) -> None: self.__id.SetValue(v)   # test-only: bypass the read-only PK
class Items(EntityCollection[Item]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)

    def _GetType(self) -> type[Item]: return Item

class Line(Entity):
    def __init__(self, o: int, l: int, q: int) -> None:
        super().__init__()

        self.__o: IStruct[int] = Struct[int](o); self.__l: IStruct[int] = Struct[int](l); self.__q: IStruct[int] = Struct[int](q)
    
    def Dispose(self) -> None: pass

    @primaryKeyConfig()
    def OrderId(self) -> IStruct[int]: return self.__o

    @primaryKeyConfig()
    def LineId(self) -> IStruct[int]: return self.__l

    @columnConfig()
    def Quantity(self) -> IStruct[int]: return self.__q
class Lines(EntityCollection[Line]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)
    def _GetType(self) -> type[Line]: return Line

class Category(Entity):
    def __init__(self, name: str) -> None:
        super().__init__()

        self.__id: IStruct[int] = Struct[int](0); self.__name: IStruct[str] = Struct[str](name)
    
    def Dispose(self) -> None: pass

    @autoPrimaryKeyConfig()
    def Id(self) -> IStruct[int]: return self.__id

    @columnConfig()
    def Name(self) -> IStruct[str]: return self.__name

class Product(Entity):
    def __init__(self, price: int, category: Category) -> None:
        super().__init__()

        self.__id: IStruct[int] = Struct[int](0); self.__price: IStruct[int] = Struct[int](price)
        self.__category: IStruct[Category] = Struct[Category](category)
    
    def Dispose(self) -> None: pass

    @autoPrimaryKeyConfig()
    def Id(self) -> IStruct[int]: return self.__id

    @columnConfig()
    def Price(self) -> IStruct[int]: return self.__price

    @entityColumnConfig(Category)
    def Category(self) -> IStruct["Category"]: return self.__category
class Products(EntityCollection[Product]):
    def __init__(self, c: DataContextBase) -> None: super().__init__(c)

    def _GetType(self) -> type[Product]: return Product

# ------------------------------------------------------------------ helpers
def try_update(e: Entity) -> Action:
    def tryUpdate(e: Entity) -> None: e.TryUpdate()
    
    return lambda: tryUpdate(e)

def make_conn(path: str = ":memory:") -> IConnection:
    conn = Connection(path)
    
    conn.Open()
    
    return conn

def col(ff: IFieldFactory, name: str) -> IntegerField: return ff.CreateInteger(name, FieldAttributes(0), IntegerMode.Long) # plain integer column (NOT NULL; value supplied)
def pk(ff: IFieldFactory, name: str) -> IntegerField: return ff.CreateInteger(name, FieldAttributes.PrimaryKey, IntegerMode.Long) # auto-increment integer primary key
def txt(ff: IFieldFactory, name: str) -> TextField: return ff.CreateText(name, FieldAttributes(0), TextMode.Text) # plain text column

def create_item_table(conn: IConnection) -> None:
    db: IDataBase = conn.GetCursor()
    ff: IFieldFactory = conn.GetFactoryProvider().GetFieldFactory()

    db.CreateTable("Item", (pk(ff, "Id"), col(ff, "Quantity")))

def insert_item(ctx: DataContextBase, q: int) -> Item:
    it = Item(q)
    tx = ctx.BeginTransaction()

    assert tx.TryAdd(it) is True; tx.Dispose()
    
    return it

_results: list[tuple[str, bool, str]] = []

def scenario(name: str, fn: Action) -> None:
    try:
        fn()
        
        _results.append((name, True, "")); print(f"[PASS] {name}")
    except AssertionError as e:
        _results.append((name, False, f"assert: {e}")); print(f"[FAIL] {name}: assert: {e}")
    except BaseException as e:
        _results.append((name, False, f"{type(e).__name__}: {e}")); print(f"[ERR ] {name}: {type(e).__name__}: {e}")
        traceback.print_exc()

def expect_raises(exc_type: type[Exception], fn: Action) -> None:
    try: fn()
    except exc_type: return

    except BaseException as e: raise AssertionError(f"expected {exc_type.__name__}, got {type(e).__name__}: {e}")

    raise AssertionError(f"expected {exc_type.__name__}, nothing raised")

# ------------------------------------------------------------------ scenarios
def s_simple() -> None:
    conn: IConnection = make_conn()

    create_item_table(conn)
    
    ctx: DataContextBase = DataContext(conn)
    
    it: Item = insert_item(ctx, 10)
    it.Quantity = 20

    tx: ITransaction = ctx.BeginTransaction()
    
    assert it.TryUpdate() is True
    
    tx.Dispose()
    
    rows = [(r.Id, r.Quantity) for r in Items(DataContext(conn)).Select().AsIterable()]
    
    assert rows == [(1, 20)], rows

def s_noop_clean() -> None:
    conn = make_conn()

    create_item_table(conn)

    ctx = DataContext(conn)

    it = insert_item(ctx, 10)
    tx = ctx.BeginTransaction()
    
    assert it.TryUpdate() is False, "clean entity must be a no-op"
    
    tx.Dispose()

def s_noop_roundtrip() -> None:
    # mutate then restore the original value -> value-recompare sees no net change -> no-op
    conn = make_conn()
    
    create_item_table(conn)
    
    ctx = DataContext(conn)
    
    it = insert_item(ctx, 10)
    it.Quantity = 20
    it.Quantity = 10
    
    tx = ctx.BeginTransaction()
    
    assert it.TryUpdate() is False, "round-trip to baseline must be a no-op"
    
    tx.Dispose()

def s_rebaseline() -> None:
    # after a committed update, a second no-op returns False, and a new mutation updates again
    conn = make_conn()
    
    create_item_table(conn)
    
    ctx = DataContext(conn)
    
    it = insert_item(ctx, 10)
    it.Quantity = 20
    
    tx = ctx.BeginTransaction()
    assert it.TryUpdate() is True
    tx.Dispose()
    
    tx = ctx.BeginTransaction()
    assert it.TryUpdate() is False, "committed update must rebaseline"
    tx.Dispose()
    
    it.Quantity = 30
    
    tx = ctx.BeginTransaction()
    assert it.TryUpdate() is True
    tx.Dispose()
    
    rows = [(r.Id, r.Quantity) for r in Items(DataContext(conn)).Select().AsIterable()]
    
    assert rows == [(1, 30)], rows

def s_composite() -> None:
    conn = make_conn()
    ff = conn.GetFactoryProvider().GetFieldFactory()
    
    conn.GetCursor().CreateTable("Line", [col(ff, "OrderId"), col(ff, "LineId"), col(ff, "Quantity")], None)

    ctx = DataContext(conn)
    ln = Line(10, 5, 100)
    
    tx = ctx.BeginTransaction()
    assert tx.TryAdd(ln) is True
    tx.Dispose()
    
    ln.Quantity = 200
    
    tx = ctx.BeginTransaction()
    assert ln.TryUpdate() is True
    tx.Dispose()
    
    rows = [(r.OrderId, r.LineId, r.Quantity) for r in Lines(DataContext(conn)).Select().AsIterable()]
    
    assert rows == [(10, 5, 200)], rows

def s_pk_drift() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    it._SetIdRaw(99) # pyright: ignore[reportPrivateUsage] # drift the primary key
    tx = ctx.BeginTransaction()
    expect_raises(PrimaryKeyMutationError, try_update(it))
    tx.Dispose()

def s_not_persisted() -> None:
    conn = make_conn(); create_item_table(conn); DataContext(conn)
    it = Item(10)   # never persisted -> no context handle
    expect_raises(EntityNotPersistedError, try_update(it))

def s_row_vanished() -> None:
    path = tempfile.mkstemp(suffix=".db")[1]

    try:
        conn = make_conn(path); create_item_table(conn); ctx = DataContext(conn)
        it = insert_item(ctx, 10)
        # out-of-band deletion via a separate connection
        raw = sqlite3.connect(path); raw.execute('DELETE FROM "Item" WHERE "Id" = 1'); raw.commit(); raw.close()
        it.Quantity = 20
        tx = ctx.BeginTransaction()
        expect_raises(RowVanishedError, try_update(it))
        tx.Dispose()
    
    finally:
        if os.path.exists(path): os.remove(path)

def _arm_block(ctx: DataContextBase, it: Item) -> None:
    it.Quantity = 20
    tx = ctx.BeginTransaction()
    assert it.TryUpdate() is True
    tx.Rollback()   # undoes the DB write + arms the context (leave-as-is)
    tx.Dispose()

def s_leave_as_is_arms() -> None:
    conn = make_conn()
    
    create_item_table(conn)
    
    ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    
    _arm_block(ctx, it)
    
    assert ctx.IsBlocked(), "rolled-back update must arm the context"
    # leave-as-is: in-memory value kept
    assert it.Quantity == 20, f"leave-as-is: expected 20, got {it.Quantity}"
    # DB reverted
    rows = [(r.Id, r.Quantity) for r in Items(DataContext(conn)).Select().AsIterable()]
    assert rows == [(1, 10)], rows

def s_gate() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    _arm_block(ctx, it)
    expect_raises(UnresolvedRollbackError, try_update(it))

def s_reverse() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    _arm_block(ctx, it)
    ctx.Reverse()
    assert not ctx.IsBlocked(), "Reverse must clear the block"
    assert it.Quantity == 10, f"Reverse must restore baseline, got {it.Quantity}"
    # subsequent updates work again
    it.Quantity = 40
    tx = ctx.BeginTransaction(); assert it.TryUpdate() is True; tx.Dispose()
    rows = [(r.Id, r.Quantity) for r in Items(DataContext(conn)).Select().AsIterable()]
    assert rows == [(1, 40)], rows

def s_retry() -> None:
    conn = make_conn(); create_item_table(conn); ctx = DataContext(conn)
    it = insert_item(ctx, 10)
    _arm_block(ctx, it)
    assert ctx.Retry() is True, "Retry must succeed and re-emit the update"
    assert not ctx.IsBlocked(), "Retry must clear the block"
    rows = [(r.Id, r.Quantity) for r in Items(DataContext(conn)).Select().AsIterable()]
    assert rows == [(1, 20)], rows

def s_fk_transient() -> None:
    conn = make_conn()
    ff = conn.GetFactoryProvider().GetFieldFactory()
    db = conn.GetCursor()

    db.CreateTable("Category", [pk(ff, "Id"), txt(ff, "Name")], None)
    db.CreateTable("Product", [pk(ff, "Id"), col(ff, "Price"), col(ff, "Category")], None)
    
    ctx = DataContext(conn)
    c1 = Category("A")
    tx = ctx.BeginTransaction(); assert tx.TryAdd(c1) is True; tx.Dispose()
    p = Product(100, c1)
    tx = ctx.BeginTransaction(); assert tx.TryAdd(p) is True; tx.Dispose()
    # point the entity column at a transient (unpersisted) category
    c2 = Category("B")
    p.Category = c2
    tx = ctx.BeginTransaction()
    expect_raises(UnpersistedReferenceError, try_update(p))
    tx.Dispose()

# ------------------------------------------------------------------ run
for name, fn in (
    ("simple update persists", s_simple),
    ("no-op (clean entity)", s_noop_clean),
    ("no-op (round-trip to baseline)", s_noop_roundtrip),
    ("rebaseline after commit", s_rebaseline),
    ("composite-PK update", s_composite),
    ("PK drift -> PrimaryKeyMutationError", s_pk_drift),
    ("unpersisted entity -> EntityNotPersistedError", s_not_persisted),
    ("row vanished -> RowVanishedError", s_row_vanished),
    ("leave-as-is arms the block", s_leave_as_is_arms),
    ("gate -> UnresolvedRollbackError", s_gate),
    ("Reverse resolves (revert + unblock)", s_reverse),
    ("Retry resolves (re-emit + unblock)", s_retry),
    ("FK transient -> UnpersistedReferenceError", s_fk_transient)):

    scenario(name, fn)

print("\n==== SUMMARY ====")

passed = sum(1 for _, ok, _ in _results if ok)

for name, ok, msg in _results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   [{msg}]" if not ok else ""))

print(f"\n{passed}/{len(_results)} passed")
